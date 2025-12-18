"""
图表推荐规则引擎 - 智能数据分析核心模块
根据数据类型自动推荐合适的图表类型
"""

import pandas as pd
from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype


class ChartRuleEngine:
    """图表推荐规则引擎"""
    
    # 图表类型定义及其数据要求
    CHART_DEFINITIONS = {
        "line": {
            "name": "折线图 (Trend)",
            "icon": "📈",
            "description": "展示数据随时间或顺序的变化趋势",
            "requires": {"x": ["time", "category", "numeric"], "y": ["numeric"]}
        },
        "bar": {
            "name": "柱状图 (Comparison)",
            "icon": "📊",
            "description": "对比不同类别或时间点的数据差异",
            "requires": {"x": ["category", "time"], "y": ["numeric"]}
        },
        "scatter": {
            "name": "散点图 (Distribution)",
            "icon": "💠",
            "description": "显示两个数值变量之间的相关性",
            "requires": {"x": ["numeric", "time"], "y": ["numeric"]}
        },
        "pie": {
            "name": "饼图 (Composition)",
            "icon": "🥧",
            "description": "展示部分与整体的占比关系",
            "requires": {"x": ["category"], "y": ["numeric"]},
            "limitations": "建议分类数量 ≤ 8,仅支持单个Y轴"
        },
        "area": {
            "name": "面积图 (Volume)",
            "icon": "🏔️",
            "description": "强调数值的累积量和变化幅度",
            "requires": {"x": ["time", "numeric"], "y": ["numeric"]}
        },
        "radar": {
            "name": "雷达图 (Multi-dimension)",
            "icon": "🕸️",
            "description": "对比多个维度的综合表现",
            "requires": {"x": ["category"], "y": ["numeric_multi"]},
            "limitations": "需要多个Y轴指标(至少2个)"
        },
        "heatmap": {
            "name": "热力图 (Correlation)",
            "icon": "🔥",
            "description": "展示数据的分布密度或相关性",
            "requires": {"x": ["category", "time"], "y": ["numeric_multi"]},
            "limitations": "需要多个Y轴指标"
        }
    }

    @staticmethod
    def detect_col_type(df, col_name):
        """
        推断列的数据类型
        
        Args:
            df: DataFrame对象
            col_name: 列名
            
        Returns:
            str: 'time'(时间型), 'numeric'(数值型), 'category'(分类型)
        """
        if col_name not in df.columns:
            return None
        
        col = df[col_name]
        
        # 1. 检查是否为时间类型
        if is_datetime64_any_dtype(col):
            return "time"
        
        # 2. 检查是否为数值类型
        if is_numeric_dtype(col):
            # 特殊判断: 如果数值列的唯一值很少,可能是分类编码
            # 例如: [0, 1, 2] 可能代表类别而非真正的数值
            unique_count = col.nunique()
            total_count = len(col)
            
            # 如果唯一值数量 < 10 且占比 < 5%,认为是分类
            if unique_count < 10 and unique_count / total_count < 0.05:
                return "category"
            
            # 特殊处理: Timestamp 列通常是连续数值,认为是时间
            if col_name.lower() in ['timestamp', 'time', 't', 'ts']:
                return "time"
            
            return "numeric"
        
        # 3. 其他情况认为是分类型
        return "category"

    @classmethod
    def get_valid_charts(cls, df, x_col, y_cols):
        """
        根据选中的X/Y列,返回可用的图表列表
        
        Args:
            df: DataFrame对象
            x_col: X轴列名
            y_cols: Y轴列名列表
            
        Returns:
            list: 推荐的图表类型ID列表
        """
        if not x_col or not y_cols:
            return []
        
        valid_charts = []
        
        # 推断数据类型
        x_type = cls.detect_col_type(df, x_col)
        
        # 检查所有Y轴列的类型
        y_types = [cls.detect_col_type(df, col) for col in y_cols]
        
        # 判断是否所有Y轴都是数值型
        all_numeric = all(t == "numeric" for t in y_types)
        is_multi_y = len(y_cols) > 1
        
        # 遍历所有图表定义,匹配规则
        for chart_key, config in cls.CHART_DEFINITIONS.items():
            req_x = config["requires"]["x"]
            req_y = config["requires"]["y"]
            
            # X轴类型匹配
            match_x = x_type in req_x
            
            # Y轴类型匹配
            if "numeric_multi" in req_y:
                # 需要多个数值Y轴
                match_y = all_numeric and is_multi_y
            elif "numeric" in req_y:
                # 至少有一个数值Y轴
                match_y = all_numeric
            else:
                match_y = False
            
            # 特殊规则处理
            if chart_key == "pie":
                # 饼图只支持单个Y轴且X轴必须是分类
                if is_multi_y or x_type != "category":
                    continue
                # 检查分类数量
                category_count = df[x_col].nunique()
                if category_count > 8:
                    continue  # 分类过多不推荐饼图
            
            elif chart_key == "radar":
                # 雷达图需要至少2个Y轴
                if not is_multi_y or len(y_cols) < 2:
                    continue
            
            elif chart_key == "heatmap":
                # 热力图需要多个Y轴
                if not is_multi_y or len(y_cols) < 2:
                    continue
            
            # 如果匹配,加入推荐列表
            if match_x and match_y:
                valid_charts.append(chart_key)
        
        return valid_charts

    @classmethod
    def get_chart_info(cls, chart_key):
        """
        获取图表的详细信息
        
        Args:
            chart_key: 图表类型ID
            
        Returns:
            dict: 图表配置信息
        """
        return cls.CHART_DEFINITIONS.get(chart_key, {})
    
    @classmethod
    def get_recommendation_reason(cls, df, x_col, y_cols, chart_key):
        """
        生成推荐理由说明
        
        Args:
            df: DataFrame对象
            x_col: X轴列名
            y_cols: Y轴列名列表
            chart_key: 图表类型ID
            
        Returns:
            str: 推荐理由文本
        """
        x_type = cls.detect_col_type(df, x_col)
        y_count = len(y_cols)
        
        reasons = []
        
        if chart_key == "line":
            reasons.append(f"X轴({x_col})为{cls._type_name(x_type)},适合展示趋势")
        elif chart_key == "scatter":
            reasons.append(f"适合分析 {x_col} 与 {', '.join(y_cols)} 的相关性")
        elif chart_key == "pie":
            reasons.append(f"{x_col} 有 {df[x_col].nunique()} 个类别,适合饼图")
        elif chart_key == "radar":
            reasons.append(f"选择了 {y_count} 个指标,可多维度对比")
        elif chart_key == "heatmap":
            reasons.append(f"{y_count} 个指标适合热力图展示分布")
        
        return " | ".join(reasons) if reasons else "推荐使用此图表"
    
    @staticmethod
    def _type_name(type_key):
        """数据类型的中文名称"""
        names = {
            "time": "时间序列",
            "numeric": "数值型",
            "category": "分类型"
        }
        return names.get(type_key, type_key)
