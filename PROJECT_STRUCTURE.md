# 项目结构说明

## 目录结构

```
NEUP_LOG_ANANLYZER/
├── app.py                      # 主应用程序（已模块化简化）
├── requirements.txt            # 项目依赖
├── README.md                   # 项目说明文档
│
├── styles/                     # 样式模块
│   ├── __init__.py
│   ├── main.css               # 主样式表（现代商务主题）
│   └── style_loader.py        # 样式加载器
│
├── templates/                  # 模板组件
│   ├── __init__.py
│   └── components.py          # HTML 模板组件函数
│
└── static/                     # 静态资源
    └── js/
        └── custom.js          # 自定义前端交互脚本
```

## 模块说明

### 1. `app.py` - 主应用程序
简化后的主程序，专注于业务逻辑：
- 数据解析（LogParser 类）
- ECharts 图表渲染
- 路由和状态管理

### 2. `styles/` - 样式模块

#### `main.css`
- 现代商务主题 CSS
- 响应式设计
- 卡片、按钮、度量指标等组件样式
- 动画效果

#### `style_loader.py`
提供样式和脚本加载函数：
- `load_css(file_path)` - 加载 CSS 文件
- `load_js(file_path)` - 加载 JS 文件
- `apply_modern_theme()` - 应用主题
- `load_custom_scripts()` - 加载自定义脚本

### 3. `templates/` - 模板组件

#### `components.py`
HTML 模板组件函数：
- `render_header()` - 页面头部
- `render_welcome_screen()` - 欢迎屏幕
- `render_log_format_help()` - 日志格式帮助
- `render_about_info()` - 关于信息
- `render_statistics_card()` - 统计卡片
- `render_chart_hint()` - 图表提示

### 4. `static/js/` - 前端脚本

#### `custom.js`
自定义前端交互功能：
- **键盘快捷键**：
  - `Ctrl/Cmd + E` - 导出数据
  - `F` - 全屏切换
- **图表增强**：
  - 自动为图表添加全屏按钮
  - 增强交互提示
- **通知系统**：
  - 浮动通知消息
  - 动画效果

## 使用方法

### 基本使用
```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py
```

### 添加新样式
1. 编辑 `styles/main.css` 添加 CSS 规则
2. 样式会自动被 `style_loader.py` 加载

### 添加新组件
1. 在 `templates/components.py` 中定义新函数
2. 在 `app.py` 中导入并使用

### 添加 JS 功能
1. 编辑 `static/js/custom.js` 添加新功能
2. 脚本会通过 `load_custom_scripts()` 自动加载

## 优势

### 1. 代码组织清晰
- 关注点分离：样式、模板、逻辑独立
- 易于维护和扩展
- 团队协作友好

### 2. 可复用性
- 组件可在多处使用
- 样式统一管理
- 减少代码重复

### 3. 性能优化
- CSS 和 JS 文件独立加载
- 缓存友好
- 按需加载资源

### 4. 易于扩展
- 添加新主题：创建新的 CSS 文件
- 添加新组件：在 components.py 中定义
- 添加新交互：在 custom.js 中实现

## 开发建议

### 添加新主题
```python
# 在 styles/ 下创建 theme_dark.css
# 在 style_loader.py 中添加加载函数
def apply_dark_theme():
    load_css("styles/theme_dark.css")
```

### 添加新页面组件
```python
# 在 templates/components.py 中
def render_custom_section(data):
    st.markdown(f"""
    <div class="custom-section">
        {data}
    </div>
    """, unsafe_allow_html=True)
```

### 添加新 JS 功能
```javascript
// 在 static/js/custom.js 中
function addNewFeature() {
    // 实现新功能
}
```

## 注意事项

1. **路径问题**：确保相对路径正确，特别是在加载 CSS/JS 时
2. **Streamlit 限制**：某些 JS 功能可能受 Streamlit 架构限制
3. **缓存**：修改 CSS/JS 后可能需要清除浏览器缓存
4. **安全性**：使用 `unsafe_allow_html=True` 时注意 XSS 风险

## 未来扩展方向

- [ ] 支持多主题切换
- [ ] 添加更多图表类型
- [ ] 国际化支持（i18n）
- [ ] 用户偏好设置持久化
- [ ] WebSocket 实时数据更新
- [ ] 导出为 PDF/图片功能
