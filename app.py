import streamlit as st
import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64

# ==========================================
# 配置与初始化
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="NEUP_LOG_ANALYZER v1.0", 
    page_icon="🖥️",
    initial_sidebar_state="expanded"
)

# ==========================================
# UI 风格定义 (现代商务主题)
# ==========================================
def apply_modern_style():
    st.markdown("""
    <style>
        /* 全局字体与背景 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* 侧边栏样式 */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
            border-right: 1px solid #dee2e6;
        }
        
        section[data-testid="stSidebar"] h1 {
            color: #2c3e50 !important;
            font-weight: 700;
        }

        /* 按钮样式 */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.25);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
        }

        /* 标题样式 */
        h1 {
            color: #1a202c !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }
        
        h2, h3 {
            color: #2d3748 !important;
            font-weight: 600 !important;
        }
        
        /* Metric 样式 */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            color: #2d3748 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #718096 !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            font-size: 0.75rem !important;
            letter-spacing: 0.5px;
        }
        
        /* 卡片效果 */
        div[data-testid="stMetric"] {
            background: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            border: 1px solid #e2e8f0;
        }
        
        /* 文件上传器样式 */
        .uploadedFile {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        
        /* 信息框样式 */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 核心逻辑类
# ==========================================
class LogParser:
    def __init__(self):
        # 预编译正则，提升性能
        self.first_bracket_re = re.compile(r'\[([^\]]+)\]')
        # 支持 key:value 和 key=value 两种常见格式
        self.data_pattern = re.compile(r'(\w+)[:=](-?[\d.]+)')

    def parse(self, content):
        data_list = []
        lines = content.split('\n')
        parse_errors = 0

        for line_no, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):  # 跳过空行和注释
                continue

            # 1. 尝试提取时间戳 (支持 [] 包裹的)
            timestamp = None
            m = self.first_bracket_re.search(line)
            
            # 如果有中括号，尝试解析其中的数字
            if m:
                raw_ts = m.group(1)
                if re.match(r'^\d+(?:\.\d+)?$', raw_ts):
                    try:
                        timestamp = float(raw_ts)
                    except ValueError:
                        parse_errors += 1
            
            # 2. 提取数据键值对
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
                
                # 只有解析到数据才添加
                if row_data:
                    data_list.append(row_data)

        if not data_list:
            return pd.DataFrame(), parse_errors

        df = pd.DataFrame(data_list)
        
        # 处理时间轴
        if 'Timestamp' in df.columns:
            df = df.sort_values('Timestamp').reset_index(drop=True)
            # 使用前向填充处理缺失值
            df = df.fillna(method='ffill').fillna(0)
        else:
            # 如果没有解析到时间戳，使用索引作为时间
            df['Timestamp'] = df.index
        
        return df, parse_errors
    
    def get_statistics(self, df):
        """获取数据统计信息"""
        if df.empty:
            return {}
        
        stats = {}
        for col in df.columns:
            if col != 'Timestamp':
                stats[col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'range': df[col].max() - df[col].min()
                }
        return stats

# ==========================================
# 页面组件
# ==========================================
def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        # 📊 NEUP 日志分析器
        <p style='color: #718096; font-size: 1.1rem; margin-top: -10px;'>
            专业的日志数据可视化与对比分析工具
        </p>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='text-align: right; padding-top: 20px;'>
            <span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 0.5rem 1rem; border-radius: 20px; 
                         font-weight: 600; font-size: 0.9rem;'>
                v1.0
            </span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")

def get_common_keys(df1, df2):
    """获取两个日志共有的列"""
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    # 排除时间戳
    common = list((cols1 & cols2) - {'Timestamp'})
    common.sort()
    return common

def render_comparison_dashboard(df_main, df_ref, keys):
    """渲染对比模式仪表盘"""
    st.markdown("### 🔄 日志对比分析")
    st.markdown("实时对比主日志与参考日志的数据差异")
    
    # 对齐时间轴逻辑：简单起见，我们假设两者基于索引或相对时间对齐
    # 在这里我们以主日志的时间为基准
    
    times_sorted = np.sort(df_main['Timestamp'].unique())
    if len(times_sorted) == 0:
        st.error("主日志无有效时间数据")
        return

    # 滑块
    min_time, max_time = float(times_sorted[0]), float(times_sorted[-1])
    current_time = st.slider(
        "⏱️ 时间轴同步", 
        min_time, max_time, min_time,
        help="拖动滑块查看不同时间点的数据对比"
    )

    # 寻找最近的行
    idx_main = (df_main['Timestamp'] - current_time).abs().idxmin()
    row_main = df_main.loc[idx_main]
    
    # 寻找对比日志中最近的行 (假设时间戳含义相同)
    # 如果时间戳范围差异巨大，可能需要归一化，这里假设是同一次运行的不同记录或相似时间轴
    idx_ref = (df_ref['Timestamp'] - current_time).abs().idxmin()
    row_ref = df_ref.loc[idx_ref]

    # 显示 Metrics
    st.markdown(f"**当前时间点: {current_time:.2f}**")
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
                help=f"主日志: {val_main:.3f} | 参考日志: {val_ref:.3f}"
            )

    # 绘图：双线图
    st.markdown("---")
    st.markdown("### � 数据趋势对比")
    for key in keys:
        fig = go.Figure()
        
        # 主数据线
        fig.add_trace(go.Scatter(
            x=df_main['Timestamp'], y=df_main[key],
            mode='lines', name=f'{key} (主日志)',
            line=dict(color='#667eea', width=2.5),
            hovertemplate='<b>主日志</b><br>时间: %{x}<br>值: %{y:.3f}<extra></extra>'
        ))
        
        # 对比数据线
        fig.add_trace(go.Scatter(
            x=df_ref['Timestamp'], y=df_ref[key],
            mode='lines', name=f'{key} (参考)',
            line=dict(color='#f093fb', width=2, dash='dash'),
            hovertemplate='<b>参考日志</b><br>时间: %{x}<br>值: %{y:.3f}<extra></extra>'
        ))

        # 垂直线标记当前时间点
        fig.add_vline(
            x=current_time, 
            line_width=2, 
            line_color="rgba(255, 75, 75, 0.6)",
            line_dash="solid"
        )

        fig.update_layout(
            title=dict(
                text=f"<b>{key}</b>",
                font=dict(size=16, color='#2d3748')
            ),
            template='plotly_white',
            height=350,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(
                orientation="h", 
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                title="时间戳",
                showgrid=True,
                gridcolor='#e2e8f0'
            ),
            yaxis=dict(
                title="数值",
                showgrid=True,
                gridcolor='#e2e8f0'
            ),
            hovermode='x unified',
            plot_bgcolor='#fafafa'
        )
        st.plotly_chart(fig, use_container_width=True)

def render_single_dashboard(df, keys, parser):
    """渲染单文件模式仪表盘"""
    st.markdown("### 📋 单日志文件分析")
    st.markdown("查看日志文件中各参数随时间的变化趋势")
    
    # 显示统计信息
    with st.expander("📊 数据统计概览", expanded=False):
        stats = parser.get_statistics(df)
        for key in keys:
            if key in stats:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("参数", key)
                col2.metric("平均值", f"{stats[key]['mean']:.3f}")
                col3.metric("标准差", f"{stats[key]['std']:.3f}")
                col4.metric("范围", f"{stats[key]['range']:.3f}")
                st.markdown("---")
    
    times_sorted = np.sort(df['Timestamp'].unique())
    min_time, max_time = float(times_sorted[0]), float(times_sorted[-1])
    
    # 智能步长
    diffs = np.diff(times_sorted)
    step = max(float(np.min(diffs[diffs > 0])) if len(diffs) > 0 else 0.1, 1e-3)
    
    current_time = st.slider(
        "⏱️ 时间轴定位", 
        min_time, max_time, min_time, step=step,
        help="拖动滑块查看不同时间点的数据快照"
    )
    
    # 对齐
    nearest_idx = (df['Timestamp'] - current_time).abs().idxmin()
    row = df.loc[nearest_idx]
    real_time = row['Timestamp']

    # Metrics
    st.markdown(f"**当前时间点: {real_time:.4f}**")
    cols = st.columns(min(len(keys), 5))
    for i, key in enumerate(keys):
        with cols[i % len(cols)]:
            st.metric(
                label=key, 
                value=f"{row[key]:.4f}",
                help=f"{key}在时刻{real_time:.4f}的数值"
            )

    # Plot
    st.markdown("---")
    st.markdown("### 📊 全局趋势图")
    
    # 使用渐变色
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
    
    fig = go.Figure()
    for i, key in enumerate(keys):
        fig.add_trace(go.Scatter(
            x=df['Timestamp'], 
            y=df[key],
            mode='lines',
            name=key,
            line=dict(color=colors[i % len(colors)], width=2.5),
            hovertemplate=f'<b>{key}</b><br>时间: %{{x}}<br>值: %{{y:.4f}}<extra></extra>'
        ))
    
    # 标记当前位置
    fig.add_vline(
        x=real_time, 
        line_width=2, 
        line_color="rgba(255, 75, 75, 0.6)", 
        line_dash="solid",
        annotation_text="当前位置",
        annotation_position="top"
    )
    
    fig.update_layout(
        template='plotly_white',
        height=550,
        hovermode="x unified",
        xaxis=dict(
            title="时间戳",
            showgrid=True,
            gridcolor='#e2e8f0'
        ),
        yaxis=dict(
            title="数值",
            showgrid=True,
            gridcolor='#e2e8f0'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='#fafafa',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 主程序逻辑
# ==========================================
def main():
    apply_modern_style()
    render_header()

    parser = LogParser()
    
    # --- Sidebar ---
    st.sidebar.title("⚙️ 控制面板")
    
    # 模式选择
    analysis_mode = st.sidebar.radio(
        "📌 分析模式",
        ("单文件分析", "日志对比"),
        index=0,
        help="选择单个日志分析或两个日志对比模式"
    )

    st.sidebar.markdown("---")
    
    # 文件上传
    st.sidebar.markdown("### 📁 数据导入")
    file_main = st.sidebar.file_uploader(
        "主日志文件", 
        type=["txt", "log"], 
        key="f1",
        help="支持 .txt 和 .log 格式的日志文件"
    )
    file_ref = None
    
    if analysis_mode == "日志对比":
        file_ref = st.sidebar.file_uploader(
            "参考日志文件", 
            type=["txt", "log"], 
            key="f2",
            help="用于对比的第二个日志文件"
        )
    
    # 帮助信息
    st.sidebar.markdown("---")
    with st.sidebar.expander("💡 使用帮助"):
        st.markdown("""
        **日志格式要求：**
        - 支持 `key:value` 或 `key=value` 格式
        - 时间戳需要用方括号包裹，如 `[123.45]`
        - 示例：`[100.5] temp:25.3 pressure=101.2`
        
        **功能说明：**
        - 🔍 单文件分析：查看参数随时间的变化
        - 🔄 日志对比：对比两个日志的差异
        - 📊 统计分析：查看数据的统计特征
        - 📥 数据导出：将数据导出为 CSV 格式
        """)
    
    with st.sidebar.expander("ℹ️ 关于"):
        st.markdown("""
        **NEUP 日志分析器 v1.0**
        
        一款专业的日志数据可视化工具，支持：
        - ✨ 实时数据可视化
        - 📈 多参数对比分析
        - 🎯 精确时间点定位
        - 💾 数据导出功能
        
        © 2025 NEUP Project
        """)

    # --- Data Processing ---
    df_main = pd.DataFrame()
    df_ref = pd.DataFrame()

    if file_main:
        with st.spinner('正在解析主日志...'):
            content_main = file_main.getvalue().decode("utf-8", errors='ignore')
            df_main, errors_main = parser.parse(content_main)
            if not df_main.empty:
                st.sidebar.success(f"✅ 主日志已加载: {len(df_main)} 行数据")
                num_params = len([c for c in df_main.columns if c != 'Timestamp'])
                st.sidebar.caption(f"📊 检测到 {num_params} 个参数")
            else:
                st.sidebar.error("❌ 主日志解析失败")
    
    if file_ref:
        with st.spinner('正在解析参考日志...'):
            content_ref = file_ref.getvalue().decode("utf-8", errors='ignore')
            df_ref, errors_ref = parser.parse(content_ref)
            if not df_ref.empty:
                st.sidebar.info(f"✅ 参考日志已加载: {len(df_ref)} 行数据")
                num_params = len([c for c in df_ref.columns if c != 'Timestamp'])
                st.sidebar.caption(f"📊 检测到 {num_params} 个参数")
            else:
                st.sidebar.error("❌ 参考日志解析失败")

    # --- Visualization Routing ---
    if df_main.empty:
        st.info("💡 请从左侧上传日志文件开始分析")
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 12px; color: white; margin-top: 2rem;'>
            <h3 style='color: white; margin-top: 0;'>📖 使用指南</h3>
            <ol style='line-height: 2;'>
                <li><b>单文件分析模式</b>: 上传一个日志文件，查看各参数的时间序列变化</li>
                <li><b>日志对比模式</b>: 上传两个日志文件，实时对比数据差异</li>
                <li>支持的格式: 包含 key:value 或 key=value 格式的文本日志</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    # 提取所有可用列 (排除 Timestamp)
    all_keys = [c for c in df_main.columns if c != 'Timestamp']
    
    if not all_keys:
        st.warning("⚠️ 未检测到有效的数据字段，请检查日志格式")
        with st.expander("查看原始数据"):
            st.dataframe(df_main)
        return

    if analysis_mode == "单文件分析":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 数据选择")
        selected_keys = st.sidebar.multiselect(
            "选择要分析的参数", 
            all_keys, 
            default=all_keys[:min(3, len(all_keys))],
            help="可以选择多个参数进行对比分析"
        )
        
        if selected_keys:
            render_single_dashboard(df_main, selected_keys, parser)
        else:
            st.warning("⚠️ 请至少选择一个参数进行分析")
        
        # 数据导出
        col1, col2 = st.columns([3, 1])
        with col2:
            csv = df_main.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 导出 CSV",
                data=csv,
                file_name="log_data.csv",
                mime="text/csv",
                help="下载当前数据为 CSV 格式"
            )
        
        with st.expander("📄 查看原始数据表"):
            st.dataframe(df_main, use_container_width=True)

    elif analysis_mode == "日志对比":
        if df_ref.empty:
            st.warning("⚠️ 请上传参考日志文件以启用对比功能")
        else:
            # 找出公共列
            common_keys = get_common_keys(df_main, df_ref)
            if not common_keys:
                st.error("❌ 两个日志文件没有共同的数据字段，无法进行对比")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**主日志字段:**")
                    st.write(all_keys)
                with col2:
                    st.write("**参考日志字段:**")
                    st.write([c for c in df_ref.columns if c != 'Timestamp'])
            else:
                st.sidebar.markdown("---")
                st.sidebar.markdown("### 🎯 对比参数")
                selected_keys = st.sidebar.multiselect(
                    "选择要对比的参数", 
                    common_keys, 
                    default=common_keys[:min(2, len(common_keys))],
                    help="选择在两个日志中都存在的参数进行对比"
                )
                
                if selected_keys:
                    render_comparison_dashboard(df_main, df_ref, selected_keys)
                else:
                    st.warning("⚠️ 请至少选择一个参数进行对比")

if __name__ == "__main__":
    main()