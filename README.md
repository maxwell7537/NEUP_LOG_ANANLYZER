# 日志分析可视化工具

基于 Streamlit 和 ECharts 的数据分析系统

版本: v1.3.0  
更新: 2025-12-18

## 功能说明

### 主要功能

1. 日志文件解析与可视化
2. 多日志对比分析
3. 智能图表推荐系统
4. 支持7种图表类型：折线图、柱状图、散点图、饼图、面积图、雷达图、热力图

### 技术栈

- Python 3.10+
- Streamlit (Web框架)
- ECharts (图表库)
- Pandas (数据处理)

## 安装运行

```bash
# 1. 克隆项目
git clone https://github.com/maxwell7537/NEUP_LOG_ANANLYZER.git
cd NEUP_LOG_ANANLYZER

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
streamlit run app.py
```

访问地址: http://localhost:8501

## 日志格式

支持的日志格式：

```
# 带时间戳格式
[100.5] temp:25.3 pressure=101.2 rpm:1500
[101.2] temp:25.6 pressure=101.0 rpm:1498

# 无时间戳格式（使用行号）
temp:300.5 flow:1200
temp:301.2 flow:1198
```

解析规则：
- 时间戳: [数字] 格式，支持小数
- 键值对: 支持 key:value 和 key=value
- 数值: 支持整数、小数、负数
- 注释: # 开头的行会被忽略

## 使用示例

1. 上传日志文件
2. 选择分析模式（单文件或对比）
3. 选择要分析的参数
4. 在自助探索模块中选择X轴和Y轴
5. 系统自动推荐合适的图表类型
## 项目结构

```
app.py                    # 主程序入口
utils/chart_manager.py    # 图表推荐引擎
charts/factory.py         # 图表渲染工厂
styles/                   # CSS样式文件
templates/                # UI组件
examples/                 # 测试数据
```

### 核心模块

**LogParser 类**
- 解析日志文件
- 提取时间戳和键值对
- 返回 DataFrame 格式数据

**ChartRuleEngine 类**
- 自动识别数据类型（时间/数值/分类）
- 根据数据类型推荐图表
- 防止无效图表组合

**ChartFactory 类**
- 统一的图表渲染接口
- 支持7种图表类型
- 主题自适应

## 配置说明

CSS配色可在 styles/main.css 中修改：

```css
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --accent: #f093fb;
}
```

JavaScript配置在 static/js/custom.js：

```javascript
const CONFIG = {
    MOBILE_BREAKPOINT: 768,
    TABLET_BREAKPOINT: 1024,
    DEBOUNCE_DELAY: 200
};
```

## 依赖库

见 requirements.txt：
- streamlit>=1.28.0
- pandas>=2.0.0
- numpy>=1.24.0
- streamlit-echarts>=0.4.0

## 开发笔记

这个项目是为了学习数据可视化开发的。主要学到了：
1. Streamlit框架的使用
2. ECharts图表配置
3. 工厂模式设计
4. 数据类型推断算法

后续可以改进的地方：
- 添加更多图表类型
- 优化大数据量性能
- 增加数据导出功能