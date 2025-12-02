"""
样式加载模块
用于加载和应用 CSS 和 JS 资源，支持自动主题检测
"""
import streamlit as st
from pathlib import Path


def load_css(file_path):
    """加载 CSS 文件"""
    css_file = Path(file_path)
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"CSS 文件未找到: {file_path}")


def load_js(file_path):
    """加载 JS 文件"""
    js_file = Path(file_path)
    if js_file.exists():
        with open(js_file) as f:
            st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)
    else:
        st.warning(f"JS 文件未找到: {file_path}")


def apply_theme():
    """
    应用用户选择的主题
    """
    current_dir = Path(__file__).parent.parent
    
    # 从 session_state 获取主题，默认为 light
    theme = st.session_state.get('theme', 'light')
    
    # 根据主题加载对应的 CSS
    if theme == 'dark':
        css_path = current_dir / "styles" / "dark.css"
        theme_indicator = "🌙 深色模式"
    else:
        css_path = current_dir / "styles" / "main.css"
        theme_indicator = "☀️ 浅色模式"
    
    load_css(css_path)
    
    # 显示主题指示器
    st.markdown(f"""
    <div class="theme-indicator">
        {theme_indicator}
    </div>
    """, unsafe_allow_html=True)
    
    return theme


def apply_modern_theme():
    """应用现代主题样式"""
    return apply_theme()


def load_custom_scripts():
    """加载自定义 JS 脚本"""
    current_dir = Path(__file__).parent.parent
    js_path = current_dir / "static" / "js" / "custom.js"
    load_js(js_path)
