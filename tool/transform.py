"""
The file previously contained a duplicate/old copy after the new implementation. Remove that duplicate trailing content so only the cleaned implementation remains.
"""
"""
transform.py

解析二进制或十六进制日志文件并按配置分帧、解码字段。

用法示例：
  python3 tool/transform.py --input examples/control_log_20251229_172455.log --out out.json --format json

支持：
 - 从 tool/config.yaml 读取帧格式（header/footer、字段顺序、类型、crc）
 - 支持输入为原始二进制文件或包含 hex 文本的文件（连续 hex 或以空格分隔）
 - 可选 CRC 校验（CRC-16-CCITT，配置可关闭）
 - 输出 JSON 或 CSV

注：默认按配置中 fields 顺序解析固定长度帧。若实际协议可变需调整配置。
"""

import argparse
import yaml
import struct
import hashlib
import json
import csv
import sys
from pathlib import Path


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# 简化版：只读取二进制日志文件（例如 firmware 生成的 control_log_*.log）
def read_control_like_file(path: Path) -> bytes:
    """针对 firmware 生成的 control_log_*.log：这些文件经常是 ASCII hex 文本。
    如果文件名以 control_log_ 开头，则按文本 hex 解析（去除空白后 hex decode）；
    否则按原始二进制读取。
    这个函数比之前的通用探测更简单明确，符合“只需读取 control_log 类型文件”的要求。
    """
    name = path.name
    if name.startswith('control_log_'):
        s = path.read_text(encoding='ascii', errors='ignore')
        # remove common prefixes like 0x and whitespace
        s = s.replace('0x', '').replace('0X', '')
        s = ''.join(s.split())
        if len(s) % 2 == 1:
            s = s[:-1]
        try:
            return bytes.fromhex(s)
        except Exception:
            # fallback to raw bytes if conversion fails
            return path.read_bytes()
    else:
        return path.read_bytes()


def crc16_ccitt(data: bytes, init=0xFFFF) -> int:
    # CRC-16-CCITT (poly 0x1021), common implementation
    crc = init
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


TYPE_SIZES = {
    'uint8': 1,
    'int8': 1,
    'uint16': 2,
    'int16': 2,
    'uint32': 4,
    'int32': 4,
    'uint64': 8,
    'int64': 8,
    'bytes': None  # variable - length must be provided in config
}


def parse_frame_by_layout(frame_bytes: bytes, layout: dict, endianness='little') -> dict:
    # layout: dict with 'fields' list
    offset = 0
    res = {}
    endian_prefix = '<' if endianness == 'little' else '>'

    for fld in layout['fields']:
        name = fld['name']
        ftype = fld['type']

        if ftype == 'bytes':
            length = fld.get('length')
            if length is None:
                # 如果没有长度，取到下一字段为止（不支持）
                raise ValueError('bytes field requires length in config')
            val = frame_bytes[offset: offset + length]
            # 尝试剔除尾部的 0x00
            try:
                # 保留原始 hex 以及 utf-8 的可打印表示
                text = val.rstrip(b'\x00')
                res[name] = { 'hex': val.hex(), 'text': text.decode('utf-8', errors='ignore') }
            except Exception:
                res[name] = { 'hex': val.hex() }
            offset += length
            continue

        # numeric types
        size = TYPE_SIZES.get(ftype)
        if size is None:
            raise ValueError(f'Unsupported type: {ftype}')

        chunk = frame_bytes[offset: offset + size]
        if len(chunk) < size:
            raise ValueError(f'Not enough bytes for field {name}')

        fmt = None
        if ftype in ('uint8', 'int8'):
            fmt = 'B' if 'u' in ftype else 'b'
        elif ftype in ('uint16', 'int16'):
            fmt = 'H' if 'u' in ftype else 'h'
        elif ftype in ('uint32', 'int32'):
            fmt = 'I' if 'u' in ftype else 'i'
        elif ftype in ('uint64', 'int64'):
            fmt = 'Q' if 'u' in ftype else 'q'

        if fmt is None:
            raise ValueError(f'Unknown fmt for {ftype}')

        val = struct.unpack(endian_prefix + fmt, chunk)[0]
        res[name] = int(val)
        offset += size

    return res


def split_tx_buf_items(tx_buf_bytes: bytes):
    """
    按 0xA7 分隔 Tx_Buf 中的条目。
    每个条目格式 (log.cpp 中描述)：0xA7, id, data..., 下一个 0xA7 表示结束/下一个条目。
    返回 items 列表，每项为 { 'id': int, 'data': bytes, 'hex': str, 'len': int }
    """
    sep = 0xA7
    items = []
    if not tx_buf_bytes:
        return items

    # 找到所有 sep 的索引
    idxs = [i for i, b in enumerate(tx_buf_bytes) if b == sep]
    if not idxs:
        return items

    # 处理相邻 sep 对；按协议：0xA7 后紧跟 1 字节 id，然后是数据
    for k in range(len(idxs)-1):
        start = idxs[k]
        end = idxs[k+1]
        # 需要至少有 sep + id => start+2 <= end
        if end - start < 2:
            continue
        id_byte = tx_buf_bytes[start+1]
        id_val = int(id_byte)
        data = tx_buf_bytes[start+2:end]
        items.append({
            'id': id_val,
            'data': data,
            'hex': data.hex(),
            'len': len(data)
        })

    return items


def split_tx_buf_groups(tx_buf_bytes: bytes):
    """按 0xA7 分割 Tx_Buf 为若干组（group）。
    每个 group 是从一个 0xA7 开始到下一个 0xA7 之前的全部字节（不包含分隔符本身），
    或者如果最后一个 0xA7 后面没有下一个分隔符，则取到第一个 0x00 填充前或到末尾。
    返回每组为 dict: { 'hex': str, 'len': int, 'sha1': str }
    目的：便于对每组做快速对比/哈希匹配。
    """
    sep = 0xA7
    groups = []
    if not tx_buf_bytes:
        return groups

    n = len(tx_buf_bytes)
    idxs = [i for i,b in enumerate(tx_buf_bytes) if b == sep]
    if not idxs:
        # 没有分隔符，全作为一组（去除尾部 0x00）
        trimmed = tx_buf_bytes.rstrip(b'\x00')
        groups.append({'hex': trimmed.hex(), 'len': len(trimmed), 'sha1': hashlib.sha1(trimmed).hexdigest()})
        return groups

    for k, start in enumerate(idxs):
        # 下一个分隔符的位置
        if k+1 < len(idxs):
            end = idxs[k+1]
            # layout: 0xA7, id(1 byte), payload = start+2 .. end-1
            if end - start < 2:
                data = b''
            else:
                data = tx_buf_bytes[start+2:end]
        else:
            # last sep: take until first 0x00 padding or to end; skip 2-byte id
            tail = tx_buf_bytes[start+2:]
            # find first 0x00 which likely indicates padding
            z = tail.find(b'\x00')
            if z != -1:
                data = tail[:z]
            else:
                data = tail

        trimmed = data
        groups.append({'hex': trimmed.hex(), 'len': len(trimmed), 'sha1': hashlib.sha1(trimmed).hexdigest()})

    return groups


### Encode helpers for verification (pack values back to bytes)
def encode_motor_from_parsed(parsed: dict, item_id: int, endianness='little') -> bytes:
    import struct as _struct
    le = '<' if endianness == 'little' else '>'
    prefix = f"motor_{item_id}_"
    # best-effort: pick available parsed fields, default to zero
    try:
        type_b = int(parsed.get(f'{prefix}type', 0)) & 0xFF
    except Exception:
        type_b = 0
    can_x = int(parsed.get(f'{prefix}can_x', 0)) & 0xFF
    std_ID = int(parsed.get(f'{prefix}std_ID', 0)) & 0xFFFFFFFF
    encoder = int(parsed.get(f'{prefix}encoder', 0)) & 0xFFFF
    speed = int(parsed.get(f'{prefix}speed', 0)) & 0xFFFF
    trueCurrent = int(parsed.get(f'{prefix}trueCurrent', 0)) & 0xFFFFFFFF
    temperature = int(parsed.get(f'{prefix}temperature', 0)) & 0xFFFF
    totalAngle_f = float(parsed.get(f'{prefix}totalAngle_f', 0.0))
    totalRound = int(parsed.get(f'{prefix}totalRound', 0)) & 0xFFFFFFFF
    lostFlag = int(parsed.get(f'{prefix}lostFlag', 0)) & 0xFF
    parts = [
        _struct.pack('B', type_b),
        _struct.pack('B', can_x),
        _struct.pack(le + 'I', std_ID),
        _struct.pack(le + 'H', encoder),
        _struct.pack(le + 'h', int(speed)),
        _struct.pack(le + 'i', int(trueCurrent)),
        _struct.pack(le + 'h', int(temperature)),
        _struct.pack(le + 'f', float(totalAngle_f)),
        _struct.pack(le + 'i', int(totalRound)),
        _struct.pack('B', lostFlag),
    ]
    return b''.join(parts)


def encode_imu_from_parsed(parsed: dict, endianness='little') -> bytes:
    import struct as _struct
    le = '<' if endianness == 'little' else '>'
    acc = [float(parsed.get(f'acc_{i}', 0.0)) for i in range(3)]
    gyro = [float(parsed.get(f'gyro_{i}', 0.0)) for i in range(3)]
    angle = [float(parsed.get(f'angle_{i}', 0.0)) for i in range(3)]
    watchtemp = float(parsed.get('watchtemp', 0.0))
    parts = [
        _struct.pack(le + 'fff', *acc),
        _struct.pack(le + 'fff', *gyro),
        _struct.pack(le + 'fff', *angle),
        _struct.pack(le + 'f', watchtemp),
    ]
    return b''.join(parts)


def encode_rc_from_parsed(parsed: dict, endianness='little') -> bytes:
    import struct as _struct
    le = '<' if endianness == 'little' else '>'
    ch = [int(parsed.get(f'CH_{i}', 0)) for i in range(13)]
    wheelCode = int(parsed.get('wheelCode', 0))
    # reconstruct flags if present as flag_<NAME>
    flag_names = ['W','S','A','D','SHIFT','CTRL','Q','E','R','F','G','Z','X','C','V','B']
    flags = 0
    for i, name in enumerate(flag_names):
        if parsed.get(f'flag_{name}'):
            flags |= (1 << i)
    offline = int(parsed.get('offlineFlag', 0))
    parts = [
        _struct.pack(le + '13h', *ch),
        _struct.pack(le + 'i', wheelCode),
        _struct.pack(le + 'H', flags),
        _struct.pack('B', offline),
    ]
    return b''.join(parts)


def encode_power_from_parsed(parsed: dict, endianness='little') -> bytes:
    import struct as _struct
    le = '<' if endianness == 'little' else '>'
    capacitance = int(parsed.get('capacitance_percentage_t', 0))
    maxCurrent = int(parsed.get('maxCurrent_t', 0))
    currentNow = int(parsed.get('currentNow_t', 0))
    capHealth = int(parsed.get('capHealth', 0))
    errorCode = int(parsed.get('errorCode', 0))
    offline = int(parsed.get('offlineFlag', 0))
    parts = [
        _struct.pack(le + 'H', capacitance),
        _struct.pack(le + 'H', maxCurrent),
        _struct.pack(le + 'H', currentNow),
        _struct.pack(le + 'H', capHealth),
        _struct.pack(le + 'H', errorCode),
        _struct.pack('B', offline),
    ]
    return b''.join(parts)


def find_frames(data: bytes, cfg: dict):
    header = cfg.get('header')
    footer = cfg.get('footer')
    crc_len = cfg.get('crc', {}).get('length', 2)

    if isinstance(header, str):
        header = int(header, 0)
    if isinstance(footer, str):
        footer = int(footer, 0)

    frames = []
    i = 0
    n = len(data)
    while i < n:
        try:
            idx = data.index(bytes([header]), i)
        except ValueError:
            break
        # find footer after idx+1
        try:
            j = data.index(bytes([footer]), idx+1)
        except ValueError:
            break

        # CRC follows footer
        end = j + 1 + crc_len
        if end > n:
            # incomplete frame
            break

        frame_bytes = data[idx:end]
        frames.append((idx, frame_bytes))
        i = end

    return frames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='input .log file (binary or hex text)')
    parser.add_argument('--config', '-c', default='tool/config.yaml', help='config yaml path')
    parser.add_argument('--out', '-o', default=None, help='output file (json, csv, or log)')
    parser.add_argument('--format', choices=['json','csv','log'], default='json', help='output format; use "log" to produce app.py 可读的文本日志')
    parser.add_argument('--no-crc', action='store_true', help='disable crc check even if enabled in config')
    parser.add_argument('--verify', action='store_true', help='verify round-trip decode/encode for known item types')
    args = parser.parse_args()

    cfg = load_config(args.config)
    # 仅支持 control_log_* 类型（ASCII hex）或普通二进制日志
    data = read_control_like_file(Path(args.input))

    frames = find_frames(data, cfg)
    results = []

    for idx, fb in frames:
        # According to config, crc is last N bytes
        crc_cfg = cfg.get('crc', {})
        crc_enabled = bool(crc_cfg.get('enabled', False)) and (not args.no_crc)
        crc_len = crc_cfg.get('length', 2)

        # separate payload (everything except trailing CRC)
        payload = fb[:-crc_len] if crc_len > 0 else fb

        # if CRC enabled, compute over payload (exclude CRC field). Many protocols compute CRC over bytes between header and footer or entire frame; here we do: payload_without_crc = fb[0:-crc_len]
        crc_ok = None
        if crc_enabled:
            expected_crc = int.from_bytes(fb[-crc_len:], byteorder=cfg.get('endianness','little'))
            # compute CRC over payload up to footer (exclude CRC itself)
            computed = crc16_ccitt(payload)
            crc_ok = (expected_crc == computed)

        # Now parse fields according to config.fields using frame bytes starting after header
        # Our config includes header and footer as fields; to parse easier, pass full frame and layout.
        try:
            parsed = parse_frame_by_layout(fb, cfg, endianness=cfg.get('endianness','little'))
        except Exception as e:
            parsed = { 'error': str(e), 'raw_hex': fb.hex() }

        # 如果解析出 Tx_Buf 字段，按 0xA7 分隔内部条目
        try:
            # 支持字段名 Tx_Buf 或 tx_buff
            tx_buf_key = None
            if isinstance(parsed, dict):
                if 'Tx_Buf' in parsed:
                    tx_buf_key = 'Tx_Buf'
                elif 'tx_buff' in parsed:
                    tx_buf_key = 'tx_buff'

            if tx_buf_key:
                tx_entry = parsed.get(tx_buf_key)
                if isinstance(tx_entry, dict) and 'hex' in tx_entry:
                    tx_bytes = bytes.fromhex(tx_entry['hex'])
                    # 先按组分割（便于对比），再按 item id 拆分
                    groups = split_tx_buf_groups(tx_bytes)
                    parsed['tx_groups'] = groups
                    items = split_tx_buf_items(tx_bytes)
                    parsed['items'] = items
                    # 为每个 item 添加数值字段，便于 app.py 的文本格式读取
                    for it in items:
                        parsed[f"item_{it['id']}_len"] = it['len']
                else:
                    # 未解析为 dict (异常情况)，跳过
                    pass
        except Exception:
            # 不要因为 items 解析阻塞整个流程
            pass

        entry = {
            'offset': idx,
            'raw_hex': fb.hex(),
            'parsed': parsed,
            'crc_ok': crc_ok
        }
        results.append(entry)

    # If verify requested, run round-trip tests for items
    if args.verify:
        report = []
        total_items = 0
        mismatches = 0
        for r in results:
            parsed = r.get('parsed', {})
            items = parsed.get('items', []) if isinstance(parsed, dict) else []
            for it in items:
                total_items += 1
                id = it['id']
                orig = it['data']
                try:
                    if 50 <= id < 70:
                        # motor
                        enc = encode_motor_from_parsed(parsed, id)
                    elif id == 80:
                        enc = encode_imu_from_parsed(parsed)
                    elif id == 81:
                        enc = encode_rc_from_parsed(parsed)
                    elif id == 82:
                        enc = encode_power_from_parsed(parsed)
                    else:
                        enc = None
                except Exception as e:
                    enc = None
                    report.append(f'frame@{r["offset"]} item {id} encode error: {e}')

                if enc is None:
                    continue
                if enc != orig:
                    mismatches += 1
                    report.append(f'frame@{r["offset"]} item {id} mismatch (orig len {len(orig)} vs enc len {len(enc)})')

        summary = f'Verify: total_items={total_items} mismatches={mismatches}'
        report.insert(0, summary)
        out_report = args.out or (Path(args.input).with_suffix('.verify.txt'))
        with open(out_report, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f'Wrote verify report {out_report}')

    # output
    if args.format == 'json':
        out = args.out or (Path(args.input).with_suffix('.parsed.json'))
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'Wrote {out} ({len(results)} frames)')

    elif args.format == 'csv':
        out = args.out or (Path(args.input).with_suffix('.parsed.csv'))
        # flatten parsed dict for CSV columns
        rows = []
        # discover all keys
        keys = set()
        for r in results:
            if isinstance(r['parsed'], dict):
                keys.update(r['parsed'].keys())
        keys = ['offset','raw_hex','crc_ok'] + sorted(keys)
        with open(out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in results:
                row = { 'offset': r['offset'], 'raw_hex': r['raw_hex'], 'crc_ok': r['crc_ok'] }
                if isinstance(r['parsed'], dict):
                    for k,v in r['parsed'].items():
                        # if value is dict (for bytes), dump hex/text
                        if isinstance(v, dict):
                            row[k] = v.get('hex')
                        else:
                            row[k] = v
                writer.writerow(row)
        print(f'Wrote {out} ({len(results)} frames)')

    else:  # log format for app.py
        out = args.out or (Path(args.input).with_suffix('.parsed.log'))
        # Each line: [timestamp] key1:val key2:val ... (only numeric fields are emitted so app.py's LogParser can parse them)
        with open(out, 'w', encoding='utf-8') as f:
            for r in results:
                parsed = r.get('parsed', {})
                # determine timestamp
                ts = None
                if isinstance(parsed, dict):
                    ts = parsed.get('time_stamp') or parsed.get('Timestamp')
                if ts is None:
                    ts = r.get('offset', 0)
                # build key:val pairs for numeric fields only
                kvs = []
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        if isinstance(v, (int, float)):
                            kvs.append(f"{k}:{v}")

                # Append A7-split groups (in sequence) if present — group_0_hex, group_1_hex, ...
                if isinstance(parsed, dict):
                    groups = parsed.get('tx_groups') if isinstance(parsed.get('tx_groups'), list) else None
                    if groups:
                        for gi, g in enumerate(groups):
                            ghex = g.get('hex', '')
                            # include full hex for ordered comparison between frames
                            kvs.append(f"group_{gi}_hex:{ghex}")
                            # also provide an integer interpretation (little-endian) for quick numeric comparison
                            try:
                                if ghex:
                                    ival = int.from_bytes(bytes.fromhex(ghex), byteorder=cfg.get('endianness','little'))
                                else:
                                    ival = 0
                            except Exception:
                                ival = 0
                            kvs.append(f"group_{gi}_val:{ival}")
                    else:
                        # if no groups, still include item_<id>_hex entries (older behavior)
                        items = parsed.get('items') if isinstance(parsed.get('items'), list) else None
                        if items:
                            for it in items:
                                hexv = it.get('hex') or it.get('data') or ''
                                kvs.append(f"item_{it.get('id')}_hex:{hexv}")

                line = f"[{ts}] " + ' '.join(kvs) + "\n"
                f.write(line)
        print(f'Wrote {out} ({len(results)} frames)')


if __name__ == '__main__':
    main()
