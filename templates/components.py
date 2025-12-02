"""
HTML 模板组件模块
存放所有 HTML 模板和组件函数
"""
import streamlit as st


def render_header():
    """渲染页面头部"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        # 📊 NEUP 日志分析器 <span style='font-size:0.5em; color:#667eea'>ECharts Edition</span>
        <p style='color: #718096; font-size: 1.1rem; margin-top: -10px;'>
            专业的日志数据可视化与对比分析工具
        </p>
        """, unsafe_allow_html=True)
    st.markdown("---")


def render_welcome_screen():
    """渲染欢迎屏幕"""
    st.info("💡 请从左侧上传日志文件开始分析")
    st.markdown("""
    <div class="gradient-card-dark" style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 12px; color: white; margin-top: 2rem;
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);'>
        <h3 style='color: white; margin-top: 0;'>📖 使用指南</h3>
        <ol style='line-height: 2;'>
            <li><b>单文件分析模式</b>: 上传一个日志文件，查看各参数的时间序列变化</li>
            <li><b>日志对比模式</b>: 上传两个日志文件，实时对比数据差异</li>
            <li>支持的格式: 包含 key:value 或 key=value 格式的文本日志</li>
            <li><b>快捷键</b>: Ctrl+E (导出数据), F (全屏切换)</li>
            <li><b>主题</b>: 左侧顶部切换 ☀️ 浅色 / 🌙 深色模式</li>
        </ol>
        <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.3);'>
            <small>💡 提示: 图表支持鼠标滚轮缩放和拖拽平移</small>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_log_format_help():
    """渲染日志格式帮助"""
    return """
    **日志格式要求：**
    - 支持 `key:value` 或 `key=value` 格式
    - 时间戳需要用方括号包裹，如 `[123.45]`
    - 示例：`[100.5] temp:25.3 pressure=101.2`
    
    **功能说明：**
    - 🔍 单文件分析：查看参数随时间的变化
    - 🔄 日志对比：对比两个日志的差异
    - 📊 统计分析：查看数据的统计特征
    - 📥 数据导出：将数据导出为 CSV 格式
    - ⌨️  快捷键：Ctrl+E 导出, F 全屏
    - 🎨 主题切换：顶部切换浅色/深色模式
    """


def render_about_info():
    """渲染关于信息"""
    return """
    **NEUP 日志分析器 v1.2**
    
    一款专业的日志数据可视化工具，支持：
    - ✨ 实时数据可视化 (ECharts)
    - 📈 多参数对比分析
    - 🎯 精确时间点定位
    - 💾 数据导出功能
    - ⚡ 交互式缩放与平移
    - ⌨️  键盘快捷键支持
    - 🎨 浅色/深色主题切换
    
    © 2025 NEUP Project
    """


def render_statistics_card(key, stats):
    """渲染统计信息卡片"""
    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 12px; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 1rem;'>
        <h4 style='color: #667eea; margin-top: 0;'>{key}</h4>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem;'>
            <div>
                <div style='color: #718096; font-size: 0.85rem;'>平均值</div>
                <div style='font-size: 1.2rem; font-weight: 600; color: #2d3748;'>{stats['mean']:.3f}</div>
            </div>
            <div>
                <div style='color: #718096; font-size: 0.85rem;'>标准差</div>
                <div style='font-size: 1.2rem; font-weight: 600; color: #2d3748;'>{stats['std']:.3f}</div>
            </div>
            <div>
                <div style='color: #718096; font-size: 0.85rem;'>最小值</div>
                <div style='font-size: 1.2rem; font-weight: 600; color: #2d3748;'>{stats['min']:.3f}</div>
            </div>
            <div>
                <div style='color: #718096; font-size: 0.85rem;'>最大值</div>
                <div style='font-size: 1.2rem; font-weight: 600; color: #2d3748;'>{stats['max']:.3f}</div>
            </div>
            <div>
                <div style='color: #718096; font-size: 0.85rem;'>范围</div>
                <div style='font-size: 1.2rem; font-weight: 600; color: #2d3748;'>{stats['range']:.3f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chart_hint():
    """渲染图表提示"""
    st.caption("💡 提示：在图表上使用鼠标滚轮可缩放，拖动底部滑块可平移，按 F 键全屏")


def render_loading_spinner(text="正在处理..."):
    """渲染加载动画"""
    return st.spinner(text)
