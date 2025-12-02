# NEUP_LOG_ANALYZER

轻量且实用的日志可视化与对比工具（基于 Streamlit）。

## 功能概览

- 单文件分析：展示选定参数随时间的变化曲线与关键指标（均值、标准差、范围）。
- 日志对比：同时加载两个日志文件，按共有参数对比趋势并高亮时间点差异。
- 数据导出：将解析后的表格导出为 CSV。
- 直观交互：时间轴滑块、参数选择、图表悬浮提示等。
- 兼容常见键值日志格式（key:value 或 key=value），支持时间戳放在方括号中如 `[123.45]`。

## 快速开始

1. 创建并进入虚拟环境（可选推荐）：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 启动应用：

```bash
streamlit run app.py
```

然后在浏览器打开 Streamlit 给出的地址（默认 http://localhost:8501）。

## 日志格式说明

- 推荐的日志行格式示例：

```
[100.5] temp:25.3 pressure=101.2 rpm:1500
[101.2] temp:25.6 pressure=101.0 rpm:1498
```

- 解析规则简述：
  - 时间戳：若行内含 `[数字]`，则该数字作为 Timestamp（支持小数）。
  - 键值对：支持 `key:value` 与 `key=value` 两种写法，value 为数字（可带负号和小数点）。
  - 空行与以 `#` 开头的行会被忽略。

## 使用建议

- 若日志未包含时间戳，工具会以行索引作为时间轴。
- 若两个日志时间轴差异较大，建议先对齐或在导出后做预处理再进行精确对比。
- 对于噪声较大的信号，可在导出后进行滤波或在后续版本加入平滑功能。

## 开发与扩展

- 主要代码：`app.py`
- 解析与统计逻辑集中在 `LogParser` 类中，便于扩展更多解析规则或支持字符串型字段。

想要添加的常见扩展：
- 支持更多时间格式（如 ISO 时间戳）
- 添加简单平滑/滤波（移动平均、低通）选项
- 支持更多导出格式（Excel/JSON）

## 依赖

请参见 `requirements.txt`（主要依赖：streamlit, pandas, numpy, plotly）。

## 联系与许可

如需帮助或报告问题，请在代码仓库中创建 issue。

---

版本：v1.0 • 2025
## 如何运行

- 安装依赖: pip install -r requirements.txt

- 运行应用: streamlit run app.py