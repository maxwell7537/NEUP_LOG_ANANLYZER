# NEUP_LOG_ANALYZER

> 轻量且实用的核电日志可视化与对比工具（基于 Streamlit + ECharts）

**版本**: v1.3.0 | **更新日期**: 2025-12-18

## ✨ 新功能亮点

### 🛠️ 自助数据探索模块 (v1.3.0)

智能 BI 自助分析功能,根据数据类型自动推荐最合适的可视化图表!

**核心特性**:
- 🧠 **智能识别**: 自动识别时间型/数值型/分类型数据
- 📊 **智能推荐**: 7 种图表类型自动匹配(折线/柱状/散点/饼图/面积/雷达/热力图)
- 🎨 **防呆设计**: 只显示合法的图表选项,避免无效组合
- 🏭 **工厂模式**: 统一渲染引擎,支持主题切换
- 💠 **玻璃态 UI**: 现代化玻璃拟态设计

**快速上手**: 查看 [自助分析使用指南](docs/SELF_SERVICE_ANALYTICS.md)

---

### 安装与运行

```bash
# 1. 克隆项目
git clone https://github.com/maxwell7537/NEUP_LOG_ANANLYZER.git
cd NEUP_LOG_ANANLYZER

# 2. 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
streamlit run app.py
```

浏览器访问: **http://localhost:8501**

### 测试数据

#### 基础功能测试
```bash
# 使用示例文件测试对比功能
# 1. 上传 examples/sample_log.txt (样本日志)
# 2. 上传 examples/reference_log.txt (参考日志)
```

## 📋 日志格式

### 支持格式

```bash
# 标准格式（推荐）
[100.5] temp:25.3 pressure=101.2 rpm:1500
[101.2] temp:25.6 pressure=101.0 rpm:1498

# 无时间戳（使用行号作为时间轴）
reactor_temp:300.5 coolant_flow:1200
reactor_temp:301.2 coolant_flow:1198
```

### 解析规则
- **时间戳**: `[数字]` 格式（支持小数），缺失时使用行索引
- **键值对**: 支持 `key:value` 和 `key=value` 两种格式
- **数值**: 支持整数、小数、负数、科学计数法 (如 `1.5e12`)
- **忽略**: 空行和 `#` 开头的注释行

---

## ⌨️ 快捷键

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Ctrl/Cmd + E` | 导出数据 | 触发 CSV 下载 |
| `F` | 全屏切换 | 图表全屏显示 |
| `☰` 按钮 | 侧边栏切换 | 仅移动端显示 |

---



#### `app.py` - 主应用
```python
class LogParser:
    @staticmethod
    def parse(file_content) -> pd.DataFrame
        # 正则解析日志，提取时间戳和键值对

def render_echarts_line(df, params)
    # 渲染 ECharts 折线图

def render_single_dashboard(df, keys, parser)
    # 单文件分析仪表板（包含自助探索模块）

def main()
    # Streamlit 主逻辑
```

#### `utils/chart_manager.py` - 图表规则引擎 (NEW)
```python
class ChartRuleEngine:
    @staticmethod
    def detect_col_type(df, col_name)
        # 智能识别列的数据类型（time/numeric/category）
    
    @classmethod
    def get_valid_charts(cls, df, x_col, y_cols)
        # 根据 X/Y 轴类型推荐图表列表
    
    @classmethod
    def get_recommendation_reason(cls, df, x_col, y_cols, chart_key)
        # 生成推荐理由说明
```

#### `charts/factory.py` - 图表工厂 (NEW)
```python
class ChartFactory:
    @staticmethod
    def render(chart_type, df, x_col, y_cols, **kwargs)
        # 统一渲染入口，支持 7 种图表类型
    
    # 内部渲染器
    _render_line()      # 折线图
    _render_bar()       # 柱状图
    _render_scatter()   # 散点图
    _render_pie()       # 饼图
    _render_area()      # 面积图
    _render_radar()     # 雷达图
    _render_heatmap()   # 热力图
```

#### `custom.js` - 前端增强
```javascript
// 虚拟滚动类
class VirtualScroller {
    render() {
        // 仅渲染可视区域 + 缓冲区
    }
}

// 防抖函数
function debounce(func, wait) { ... }

// MutationObserver 监听
observer.observe(document.body, { childList: true, subtree: true })
```


## 🔧 高级配置

### JavaScript 配置 (custom.js)

```javascript
const CONFIG = {
    MOBILE_BREAKPOINT: 768,          // 手机临界点
    TABLET_BREAKPOINT: 1024,         // 平板临界点
    DEBOUNCE_DELAY: 200,             // 防抖延迟 (ms)
    VIRTUAL_SCROLL_THRESHOLD: 1000,  // 虚拟滚动阈值
    VIRTUAL_SCROLL_BUFFER: 10        // 缓冲区行数
};
```


---


### 修改配色

```css
/* styles/main.css */
:root {
    --primary: #667eea;   /* 主色 */
    --secondary: #764ba2; /* 辅助色 */
    --accent: #f093fb;    /* 强调色 */
}
```


依赖： `requirements.txt`



**最后更新**: 2025-12-18 | **当前版本**: v1.3.0

## 📚 更多文档

- [自助数据探索使用指南](docs/SELF_SERVICE_ANALYTICS.md) - 智能图表推荐功能详解
- [API 文档](docs/API.md) - 开发者接口文档 (Coming Soon)
- [贡献指南](CONTRIBUTING.md) - 如何参与项目开发 (Coming Soon)