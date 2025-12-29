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

# 导入智能图表分析模块
from utils.chart_manager import ChartRuleEngine
from charts.factory import ChartFactory

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
            # 使横轴更紧凑：对齐刻度、自动间隔、并允许旋转以避免文字重叠
            "axisTick": {"alignWithLabel": True},
            "axisLabel": {"color": "#666", "interval": "auto", "rotate": 0}
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
    # 如果数据点很多，默认缩小横轴初始窗口以让点更密集（更小的横轴间距）
    try:
        n_points = len(x_data)
        max_visible = 200  # 初始可见点数（视窗大小）
        if n_points > max_visible:
            # 更智能的默认视野：以时间均值为中心，展示尽可能多的数据点（最多 max_visible）
            try:
                x_floats = [float(v) for v in x_data]
                mean_ts = sum(x_floats) / len(x_floats)
                closest_idx = min(range(len(x_floats)), key=lambda i: abs(x_floats[i] - mean_ts))
            except Exception:
                closest_idx = n_points // 2

            half = max_visible // 2
            start_idx = max(0, closest_idx - half)
            end_idx = min(n_points, start_idx + max_visible)
            if end_idx - start_idx < max_visible:
                start_idx = max(0, end_idx - max_visible)

            start_pct = int(start_idx / n_points * 100)
            end_pct = int(end_idx / n_points * 100)
            option['dataZoom'][0]['start'] = max(0, start_pct)
            option['dataZoom'][1]['start'] = max(0, start_pct)
            option['dataZoom'][0]['end'] = min(100, end_pct)
            option['dataZoom'][1]['end'] = min(100, end_pct)
    except Exception:
        pass
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
            # 默认聚焦最近时间点，便于观察最新数据的细节
            current_time = st.slider("⏱️ 数据快照定位", min_time, max_time, max_time, step=step)
    
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
    # 3. 新增: 🛠️ 自助数据探索模块
    # ==========================================
    st.markdown("---")
    st.markdown("### 🛠️ 自助数据探索")
    st.caption("💡 根据数据类型智能推荐最合适的可视化图表")
    
    # 玻璃态容器
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # 选择 X 轴 (维度)
        # 推荐非纯数值列作为 X 轴
        all_cols = df.columns.tolist()
        x_axis = st.selectbox(
            "🔹 选择维度 (X轴)", 
            options=all_cols,
            index=all_cols.index('Timestamp') if 'Timestamp' in all_cols else 0,
            help="选择作为横轴的数据列,通常为时间或分类"
        )
    
    with col2:
        # 选择 Y 轴 (指标) - 支持多选
        # 过滤出数值列作为推荐
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != x_axis]
        default_y = numeric_cols[:min(2, len(numeric_cols))] if numeric_cols else []
        
        y_axis = st.multiselect(
            "🔹 选择指标 (Y轴)", 
            options=numeric_cols, 
            default=default_y,
            help="支持选择多个数值指标进行对比分析"
        )
    
    with col3:
        # 核心逻辑: 动态更新图表选项
        if x_axis and y_axis:
            # 调用规则引擎获取可用图表
            valid_charts = ChartRuleEngine.get_valid_charts(df, x_axis, y_axis)
            
            if valid_charts:
                # 构建显示用的标签 (Icon + Name)
                chart_options = {
                    k: f"{ChartRuleEngine.CHART_DEFINITIONS[k]['icon']} {ChartRuleEngine.CHART_DEFINITIONS[k]['name']}" 
                    for k in valid_charts
                }
                
                selected_chart_key = st.selectbox(
                    "🔹 选择可视化类型", 
                    options=valid_charts,
                    format_func=lambda x: chart_options[x],
                    help="系统根据数据类型智能推荐适合的图表"
                )
            else:
                selected_chart_key = None
                st.warning("⚠️ 当前选择的数据组合无合适的图表推荐")
        else:
            selected_chart_key = None
            st.info("👆 请先选择 X 轴和 Y 轴数据列")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 渲染区域
    if selected_chart_key and x_axis and y_axis:
        st.markdown("---")
        chart_info = ChartRuleEngine.get_chart_info(selected_chart_key)
        
        # 显示图表信息和推荐理由
        col_title, col_reason = st.columns([2, 1])
        with col_title:
            st.subheader(f"{chart_info['icon']} {chart_info['name']}")
        with col_reason:
            reason = ChartRuleEngine.get_recommendation_reason(df, x_axis, y_axis, selected_chart_key)
            st.markdown(f'<div class="chart-recommendation">💡 {reason}</div>', unsafe_allow_html=True)
        
        # 显示图表描述
        st.caption(chart_info.get('description', ''))
        
        # 动态渲染图表
        try:
            # 获取当前主题
            current_theme = st.session_state.get('theme', 'light')
            
            ChartFactory.render(
                chart_type=selected_chart_key,
                df=df,
                x_col=x_axis,
                y_cols=y_axis,
                height="500px",
                theme=current_theme
            )
            
            # 数据洞察提示
            st.markdown("---")
            with st.expander("🤖 AI 数据洞察", expanded=False):
                st.info(f"""
                **当前分析**: {', '.join(y_axis)} vs {x_axis}
                
                **数据特征**:
                - X轴类型: {ChartRuleEngine.detect_col_type(df, x_axis)}
                - Y轴数量: {len(y_axis)}
                - 数据点数: {len(df)}
                
                **建议**:
                - 可尝试切换不同的图表类型观察数据
                - 使用图表的缩放功能深入分析局部趋势
                - 对比多个指标时注意数值量级差异
                """)
                
                if st.button("🔍 生成智能分析报告 (Coming Soon)", key="ai_analyze"):
                    st.toast("🚧 AI 分析功能开发中...", icon="⚡")
        
        except Exception as e:
            st.error(f"图表渲染失败: {str(e)}")
            st.code(f"错误详情:\n{e}", language="python")

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