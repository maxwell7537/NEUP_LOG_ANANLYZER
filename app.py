import streamlit as st
import re
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts

# 导入模块化组件
from styles.style_loader import apply_modern_theme, load_custom_scripts
from templates.components import (
    render_header, 
    render_welcome_screen,
    render_log_format_help,
    render_about_info,
    render_statistics_card,
    render_chart_hint
)

# ==========================================
# 配置与初始化
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="NEUP_LOG_ANALYZER v1.2", 
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# ==========================================
# 核心逻辑类 (保持不变)
# ==========================================
class LogParser:
    def __init__(self):
        self.first_bracket_re = re.compile(r'\[([^\]]+)\]')
        self.data_pattern = re.compile(r'(\w+)[:=](-?[\d.]+)')

    def parse(self, content):
        data_list = []
        lines = content.split('\n')
        parse_errors = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            timestamp = None
            m = self.first_bracket_re.search(line)
            if m:
                raw_ts = m.group(1)
                if re.match(r'^\d+(?:\.\d+)?$', raw_ts):
                    try:
                        timestamp = float(raw_ts)
                    except ValueError:
                        parse_errors += 1
            
            data_matches = self.data_pattern.findall(line)
            if data_matches:
                row_data = {}
                if timestamp is not None:
                    row_data['Timestamp'] = timestamp
                
                for key, value in data_matches:
                    try:
                        row_data[key] = float(value)
                    except ValueError:
                        pass
                if row_data:
                    data_list.append(row_data)

        if not data_list:
            return pd.DataFrame(), parse_errors

        df = pd.DataFrame(data_list)
        if 'Timestamp' in df.columns:
            df = df.sort_values('Timestamp').reset_index(drop=True)
            df = df.ffill().fillna(0)  # 使用 ffill() 替代 fillna(method='ffill')
        else:
            df['Timestamp'] = df.index
        
        return df, parse_errors
    
    def get_statistics(self, df):
        if df.empty: return {}
        stats = {}
        for col in df.columns:
            if col != 'Timestamp':
                stats[col] = {
                    'mean': df[col].mean(), 'std': df[col].std(),
                    'min': df[col].min(), 'max': df[col].max(),
                    'range': df[col].max() - df[col].min()
                }
        return stats

# ==========================================
# ECharts 绘图辅助函数 (新增)
# ==========================================
def render_echarts_line(df, x_col, y_cols, title="趋势图", mark_line_val=None):
    """
    通用 ECharts 折线图渲染器
    """
    # 颜色盘
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#f0932b', '#eb4d4b']
    
    series_list = []
    legend_data = []

    # 将 Pandas 数据列转换为 List
    x_data = df[x_col].tolist()

    for i, col in enumerate(y_cols):
        series_list.append({
            "name": col,
            "type": "line",
            "data": df[col].tolist(),
            "smooth": True,  # 平滑曲线
            "showSymbol": False, # 默认不显示数据点圆圈，鼠标悬停才显示
            "itemStyle": {"color": colors[i % len(colors)]},
            "lineStyle": {"width": 2},
            "markLine": {
                "symbol": "none",
                "label": {"show": False},
                "data": [{"xAxis": mark_line_val}] if mark_line_val else []
            } if mark_line_val else {}
        })
        legend_data.append(col)

    # ECharts 配置项 (Option)
    option = {
        "title": {
            "text": title,
            "left": "center",
            "textStyle": {"color": "#2d3748", "fontSize": 16}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}, # 十字准星
            "backgroundColor": "rgba(255, 255, 255, 0.9)",
            "borderColor": "#ccc",
            "borderWidth": 1,
            "textStyle": {"color": "#333"}
        },
        "legend": {
            "data": legend_data,
            "top": "30px",
            "type": "scroll"
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "15%", # 留出位置给 DataZoom
            "containLabel": True
        },
        "xAxis": {
            "type": "category", # 使用 Category 模式对于离散日志点通常更稳定
            "boundaryGap": False,
            "data": x_data,
            "axisLine": {"lineStyle": {"color": "#ccc"}},
            "axisLabel": {"color": "#666"}
        },
        "yAxis": {
            "type": "value",
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#eee"}},
            "axisLabel": {"color": "#666"}
        },
        "dataZoom": [
            {
                "type": "slider", # 底部滑块
                "show": True,
                "xAxisIndex": [0],
                "start": 0,
                "end": 100,
                "height": 20,
                "bottom": 5,
                "borderColor": "transparent",
                "fillerColor": "rgba(102, 126, 234, 0.2)"
            },
            {
                "type": "inside", # 鼠标滚轮缩放
                "xAxisIndex": [0],
                "start": 0,
                "end": 100
            }
        ],
        "series": series_list
    }

    # 渲染图表
    st_echarts(options=option, height="500px", theme="light")

def render_echarts_comparison_chart(df1, df2, key, current_time):
    """
    ECharts 对比图表 (处理时间轴对齐问题)
    为了精确对比，我们使用 'value' 类型的 X 轴
    """
    # 准备数据：[timestamp, value] 格式
    data_main = df1[['Timestamp', key]].values.tolist()
    data_ref = df2[['Timestamp', key]].values.tolist()

    option = {
        "title": {"text": f"参数对比: {key}", "left": "center"},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {"data": ["主日志", "参考日志"], "top": "30px"},
        "grid": {"bottom": "15%", "containLabel": True},
        "xAxis": {
            "type": "value", # 使用数值轴而不是类目轴，确保时间对齐
            "scale": True,
            "name": "Timestamp",
            "splitLine": {"show": False}
        },
        "yAxis": {
            "type": "value",
            "scale": True,
            "splitLine": {"lineStyle": {"type": "dashed", "color": "#eee"}}
        },
        "dataZoom": [
            {"type": "slider", "show": True, "bottom": 10},
            {"type": "inside"}
        ],
        "series": [
            {
                "name": "主日志",
                "type": "line",
                "data": data_main,
                "showSymbol": False,
                "smooth": True,
                "itemStyle": {"color": "#667eea"},
                "lineStyle": {"width": 3},
                "markLine": {
                    "symbol": "none",
                    "label": {"show": False},
                    "lineStyle": {"color": "red", "type": "solid", "width": 1},
                    "data": [{"xAxis": current_time}]
                }
            },
            {
                "name": "参考日志",
                "type": "line",
                "data": data_ref,
                "showSymbol": False,
                "smooth": True,
                "itemStyle": {"color": "#f093fb"},
                "lineStyle": {"width": 2, "type": "dashed"}
            }
        ]
    }
    st_echarts(options=option, height="400px")

# ==========================================
# 辅助函数
# ==========================================
def get_common_keys(df1, df2):
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    common = list((cols1 & cols2) - {'Timestamp'})
    common.sort()
    return common

def render_comparison_dashboard(df_main, df_ref, keys):
    st.markdown("### 🔄 日志对比分析")
    
    times_sorted = np.sort(df_main['Timestamp'].unique())
    if len(times_sorted) == 0:
        st.error("主日志无有效时间数据")
        return

    # 1. 顶部控制器与快照
    min_time, max_time = float(times_sorted[0]), float(times_sorted[-1])
    current_time = st.slider("⏱️ 对比时间点同步", min_time, max_time, min_time)

    idx_main = (df_main['Timestamp'] - current_time).abs().idxmin()
    row_main = df_main.loc[idx_main]
    
    idx_ref = (df_ref['Timestamp'] - current_time).abs().idxmin()
    row_ref = df_ref.loc[idx_ref]

    # Metrics
    cols = st.columns(min(len(keys), 4))
    for i, key in enumerate(keys):
        val_main = row_main.get(key, 0)
        val_ref = row_ref.get(key, 0)
        delta = val_main - val_ref
        
        with cols[i % len(cols)]:
            st.metric(
                label=f"{key}",
                value=f"{val_main:.3f}",
                delta=f"{delta:.3f}",
                delta_color="off",
                help=f"主: {val_main:.3f} | 参: {val_ref:.3f}"
            )

    st.markdown("---")
    
    # 2. ECharts 对比图表
    st.markdown("### 📉 趋势叠加 (支持滚轮缩放)")
    for key in keys:
        render_echarts_comparison_chart(df_main, df_ref, key, current_time)

def render_single_dashboard(df, keys, parser):
    st.markdown("### 📋 单日志文件分析")
    
    # 统计信息 - 使用模板组件
    with st.expander("📊 数据统计概览", expanded=False):
        stats = parser.get_statistics(df)
        for key in keys:
            if key in stats:
                render_statistics_card(key, stats[key])
    
    # 1. 顶部控制器与快照 (保持 Streamlit 原生控件用于精确看数)
    times_sorted = np.sort(df['Timestamp'].unique())
    min_time, max_time = float(times_sorted[0]), float(times_sorted[-1])
    diffs = np.diff(times_sorted)
    step = max(float(np.min(diffs[diffs > 0])) if len(diffs) > 0 else 0.1, 1e-3)
    
    col_ctrl, col_info = st.columns([2, 1])
    with col_ctrl:
        current_time = st.slider("⏱️ 数据快照定位", min_time, max_time, min_time, step=step)
    
    nearest_idx = (df['Timestamp'] - current_time).abs().idxmin()
    row = df.loc[nearest_idx]
    real_time = row['Timestamp']

    with col_info:
        st.info(f"当前锁定时间: {real_time:.4f}")

    cols = st.columns(min(len(keys), 5))
    for i, key in enumerate(keys):
        with cols[i % len(cols)]:
            st.metric(label=key, value=f"{row[key]:.4f}")

    st.markdown("---")

    # 2. ECharts 全局趋势图
    st.markdown("### 📊 交互式趋势图")
    render_chart_hint()
    
    # 调用 ECharts 渲染函数
    render_echarts_line(df, 'Timestamp', keys, title="多参数趋势分析", mark_line_val=real_time)

# ==========================================
# 主程序入口
# ==========================================
def main():
    parser = LogParser()
    
    st.sidebar.title("⚙️ 控制面板")
    
    # 主题切换
    st.sidebar.markdown("### 🎨 主题设置")
    
    # 初始化主题（如果不存在，默认为浅色）
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    theme_option = st.sidebar.radio(
        "选择主题",
        ("☀️ 浅色模式", "🌙 深色模式"),
        index=0 if st.session_state.theme == 'light' else 1,
        help="切换界面的颜色主题"
    )
    
    # 根据用户选择更新主题
    if theme_option == "☀️ 浅色模式":
        st.session_state.theme = 'light'
    elif theme_option == "🌙 深色模式":
        st.session_state.theme = 'dark'
    
    st.sidebar.markdown("---")
    
    # 应用样式和加载脚本（在主题选择之后）
    apply_modern_theme()
    load_custom_scripts()
    render_header()
    
    analysis_mode = st.sidebar.radio("📌 分析模式", ("单文件分析", "日志对比"), index=0)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### 📁 数据导入")
    file_main = st.sidebar.file_uploader("主日志文件", type=["txt", "log"], key="f1")
    file_ref = None
    if analysis_mode == "日志对比":
        file_ref = st.sidebar.file_uploader("参考日志文件", type=["txt", "log"], key="f2")
    
    # 帮助信息
    st.sidebar.markdown("---")
    with st.sidebar.expander("💡 使用帮助"):
        st.markdown(render_log_format_help())
    
    with st.sidebar.expander("ℹ️ 关于"):
        st.markdown(render_about_info())
    
    # 数据解析
    df_main = pd.DataFrame()
    df_ref = pd.DataFrame()

    if file_main:
        content_main = file_main.getvalue().decode("utf-8", errors='ignore')
        df_main, _ = parser.parse(content_main)
        if not df_main.empty:
            st.sidebar.success(f"✅ 主日志: {len(df_main)} 行")
    
    if file_ref:
        content_ref = file_ref.getvalue().decode("utf-8", errors='ignore')
        df_ref, _ = parser.parse(content_ref)
        if not df_ref.empty:
            st.sidebar.info(f"✅ 参考日志: {len(df_ref)} 行")

    # 路由
    if df_main.empty:
        render_welcome_screen()
        return

    all_keys = [c for c in df_main.columns if c != 'Timestamp']
    
    if analysis_mode == "单文件分析":
        st.sidebar.markdown("---")
        selected_keys = st.sidebar.multiselect("选择参数", all_keys, default=all_keys[:min(3, len(all_keys))])
        if selected_keys:
            render_single_dashboard(df_main, selected_keys, parser)
            
            # CSV 导出
            st.sidebar.markdown("---")
            csv = df_main.to_csv(index=False).encode('utf-8')
            st.sidebar.download_button("📥 导出 CSV", csv, "log_data.csv", "text/csv")

    elif analysis_mode == "日志对比":
        if df_ref.empty:
            st.warning("请上传参考日志")
        else:
            common_keys = get_common_keys(df_main, df_ref)
            if common_keys:
                st.sidebar.markdown("---")
                selected_keys = st.sidebar.multiselect("对比参数", common_keys, default=common_keys[:min(2, len(common_keys))])
                if selected_keys:
                    render_comparison_dashboard(df_main, df_ref, selected_keys)
            else:
                st.error("无共同字段")

if __name__ == "__main__":
    main()