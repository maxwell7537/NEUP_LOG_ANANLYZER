"""
图表工厂 - 根据类型生成 ECharts 配置
"""

from streamlit_echarts import st_echarts


class ChartFactory:
    """图表渲染工厂"""
    
    # 配色方案
    COLOR_PALETTE = [
        '#667eea', '#764ba2', '#f093fb', '#4facfe', 
        '#43e97b', '#38f9d7', '#f0932b', '#eb4d4b',
        '#6c5ce7', '#00b894', '#fdcb6e', '#e17055'
    ]
    
    @staticmethod
    def render(chart_type, df, x_col, y_cols, height="500px", theme="light", **kwargs):
        """统一渲染入口"""
        # 根据图表类型分发到不同的渲染器
        renderers = {
            "line": ChartFactory._render_line,
            "bar": ChartFactory._render_bar,
            "scatter": ChartFactory._render_scatter,
            "pie": ChartFactory._render_pie,
            "area": ChartFactory._render_area,
            "radar": ChartFactory._render_radar,
            "heatmap": ChartFactory._render_heatmap,
        }
        
        renderer = renderers.get(chart_type)
        if not renderer:
            raise ValueError(f"不支持的图表类型: {chart_type}")
        
        option = renderer(df, x_col, y_cols, theme, **kwargs)
        
        st_echarts(options=option, height=height, theme=theme)
    
    @staticmethod
    def _get_base_option(theme="light"):
        """获取基础配置"""
        text_color = "#2d3748" if theme == "light" else "#e2e8f0"
        bg_color = "transparent"
        
        return {
            "backgroundColor": bg_color,
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"},
                "backgroundColor": "rgba(255, 255, 255, 0.9)" if theme == "light" else "rgba(30, 30, 30, 0.9)",
                "borderColor": "#ccc" if theme == "light" else "#555",
                "borderWidth": 1,
                "textStyle": {"color": "#333" if theme == "light" else "#fff"}
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "15%",
                "containLabel": True
            },
            "textStyle": {"color": text_color}
        }
    
    @staticmethod
    def _render_line(df, x_col, y_cols, theme, **kwargs):
        """渲染折线图"""
        option = ChartFactory._get_base_option(theme)
        
        x_data = df[x_col].astype(str).tolist()
        series_list = []
        legend_data = []
        
        mark_line_val = kwargs.get("mark_line_val")
        
        for i, y_col in enumerate(y_cols):
            color = ChartFactory.COLOR_PALETTE[i % len(ChartFactory.COLOR_PALETTE)]
            
            series = {
                "name": y_col,
                "type": "line",
                "data": df[y_col].tolist(),
                "smooth": True,
                "showSymbol": False,
                "itemStyle": {"color": color},
                "lineStyle": {"width": 2}
            }
            
            # 添加标记线 (如果有)
            if mark_line_val is not None:
                series["markLine"] = {
                    "symbol": "none",
                    "label": {"show": False},
                    "lineStyle": {"color": "red", "type": "solid", "width": 1},
                    "data": [{"xAxis": str(mark_line_val)}]
                }
            
            series_list.append(series)
            legend_data.append(y_col)
        
        option.update({
            "legend": {
                "data": legend_data,
                "top": "5%",
                "type": "scroll",
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": x_data,
                "axisLine": {"lineStyle": {"color": "#ccc" if theme == "light" else "#555"}},
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "yAxis": {
                "type": "value",
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee" if theme == "light" else "#333"
                    }
                },
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "dataZoom": [
                {
                    "type": "slider",
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
                    "type": "inside",
                    "xAxisIndex": [0],
                    "start": 0,
                    "end": 100
                }
            ],
            "series": series_list
        })
        
        return option
    
    @staticmethod
    def _render_bar(df, x_col, y_cols, theme, **kwargs):
        """渲染柱状图"""
        option = ChartFactory._get_base_option(theme)
        
        x_data = df[x_col].astype(str).tolist()
        series_list = []
        legend_data = []
        
        for i, y_col in enumerate(y_cols):
            color = ChartFactory.COLOR_PALETTE[i % len(ChartFactory.COLOR_PALETTE)]
            
            series_list.append({
                "name": y_col,
                "type": "bar",
                "data": df[y_col].tolist(),
                "itemStyle": {
                    "color": color,
                    "borderRadius": [5, 5, 0, 0]
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            })
            legend_data.append(y_col)
        
        option.update({
            "legend": {
                "data": legend_data,
                "top": "5%",
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLine": {"lineStyle": {"color": "#ccc" if theme == "light" else "#555"}},
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "yAxis": {
                "type": "value",
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee" if theme == "light" else "#333"
                    }
                },
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "dataZoom": [
                {"type": "slider", "show": True, "xAxisIndex": [0], "height": 20, "bottom": 5},
                {"type": "inside", "xAxisIndex": [0]}
            ],
            "series": series_list
        })
        
        return option
    
    @staticmethod
    def _render_scatter(df, x_col, y_cols, theme, **kwargs):
        """渲染散点图"""
        option = ChartFactory._get_base_option(theme)
        
        series_list = []
        legend_data = []
        
        for i, y_col in enumerate(y_cols):
            color = ChartFactory.COLOR_PALETTE[i % len(ChartFactory.COLOR_PALETTE)]
            
            # 散点图数据格式: [[x, y], [x, y], ...]
            scatter_data = df[[x_col, y_col]].values.tolist()
            
            series_list.append({
                "name": y_col,
                "type": "scatter",
                "data": scatter_data,
                "symbolSize": 8,
                "itemStyle": {"color": color, "opacity": 0.7},
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            })
            legend_data.append(y_col)
        
        option.update({
            "legend": {
                "data": legend_data,
                "top": "5%",
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "xAxis": {
                "type": "value",
                "name": x_col,
                "nameTextStyle": {"color": "#666" if theme == "light" else "#999"},
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee" if theme == "light" else "#333"
                    }
                },
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "yAxis": {
                "type": "value",
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee" if theme == "light" else "#333"
                    }
                },
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "series": series_list
        })
        
        return option
    
    @staticmethod
    def _render_pie(df, x_col, y_cols, theme, **kwargs):
        """渲染饼图 (仅支持单个Y轴)"""
        option = ChartFactory._get_base_option(theme)
        
        y_col = y_cols[0]  # 饼图只使用第一个Y轴
        
        # 饼图数据格式: [{"name": "类别", "value": 数值}, ...]
        pie_data = []
        for _, row in df.iterrows():
            pie_data.append({
                "name": str(row[x_col]),
                "value": float(row[y_col])
            })
        
        option.update({
            "tooltip": {
                "trigger": "item",
                "formatter": "{a} <br/>{b}: {c} ({d}%)"
            },
            "legend": {
                "orient": "vertical",
                "left": "left",
                "top": "center",
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "series": [{
                "name": y_col,
                "type": "pie",
                "radius": ["40%", "70%"],  # 环形饼图
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff" if theme == "light" else "#1a1a1a",
                    "borderWidth": 2
                },
                "label": {
                    "show": True,
                    "formatter": "{b}: {d}%",
                    "color": option["textStyle"]["color"]
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": 14,
                        "fontWeight": "bold"
                    }
                },
                "labelLine": {
                    "show": True
                },
                "data": pie_data,
                "color": ChartFactory.COLOR_PALETTE
            }]
        })
        
        return option
    
    @staticmethod
    def _render_area(df, x_col, y_cols, theme, **kwargs):
        """渲染面积图"""
        option = ChartFactory._get_base_option(theme)
        
        x_data = df[x_col].astype(str).tolist()
        series_list = []
        legend_data = []
        
        for i, y_col in enumerate(y_cols):
            color = ChartFactory.COLOR_PALETTE[i % len(ChartFactory.COLOR_PALETTE)]
            
            series_list.append({
                "name": y_col,
                "type": "line",
                "data": df[y_col].tolist(),
                "smooth": True,
                "showSymbol": False,
                "areaStyle": {"opacity": 0.3},
                "itemStyle": {"color": color},
                "lineStyle": {"width": 2}
            })
            legend_data.append(y_col)
        
        option.update({
            "legend": {
                "data": legend_data,
                "top": "5%",
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": x_data,
                "axisLine": {"lineStyle": {"color": "#ccc" if theme == "light" else "#555"}},
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "yAxis": {
                "type": "value",
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee" if theme == "light" else "#333"
                    }
                },
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "dataZoom": [
                {"type": "slider", "show": True, "xAxisIndex": [0], "height": 20, "bottom": 5},
                {"type": "inside", "xAxisIndex": [0]}
            ],
            "series": series_list
        })
        
        return option
    
    @staticmethod
    def _render_radar(df, x_col, y_cols, theme, **kwargs):
        """渲染雷达图"""
        option = ChartFactory._get_base_option(theme)
        
        # 雷达图需要定义指标维度
        # 这里假设每个Y轴列是一个系列,X轴的每个值是一个维度
        max_val = df[y_cols].max().max()
        
        # 定义雷达指标 (使用X轴的值作为指标名)
        indicators = []
        for val in df[x_col].astype(str):
            indicators.append({"name": val, "max": max_val * 1.2})
        
        # 准备系列数据
        series_data = []
        for y_col in y_cols:
            series_data.append({
                "name": y_col,
                "value": df[y_col].tolist()
            })
        
        option.update({
            "tooltip": {"trigger": "item"},
            "legend": {
                "data": y_cols,
                "top": "5%",
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "radar": {
                "indicator": indicators,
                "shape": "polygon",
                "splitNumber": 5,
                "name": {
                    "textStyle": {
                        "color": "#666" if theme == "light" else "#999"
                    }
                },
                "splitLine": {
                    "lineStyle": {
                        "color": "#eee" if theme == "light" else "#333"
                    }
                },
                "splitArea": {
                    "show": True,
                    "areaStyle": {
                        "color": ["rgba(114, 172, 209, 0.05)", "rgba(114, 172, 209, 0.1)"] if theme == "light"
                               else ["rgba(114, 172, 209, 0.02)", "rgba(114, 172, 209, 0.05)"]
                    }
                }
            },
            "series": [{
                "name": "指标对比",
                "type": "radar",
                "data": series_data,
                "itemStyle": {
                    "color": ChartFactory.COLOR_PALETTE
                },
                "areaStyle": {
                    "opacity": 0.3
                }
            }]
        })
        
        return option
    
    @staticmethod
    def _render_heatmap(df, x_col, y_cols, theme, **kwargs):
        """渲染热力图"""
        option = ChartFactory._get_base_option(theme)
        
        # 热力图数据格式: [[x_index, y_index, value], ...]
        x_data = df[x_col].astype(str).tolist()
        heatmap_data = []
        
        for i, x_val in enumerate(x_data):
            for j, y_col in enumerate(y_cols):
                value = df.loc[i, y_col]
                heatmap_data.append([i, j, value])
        
        # 计算最小值和最大值用于颜色映射
        values = [item[2] for item in heatmap_data]
        min_val = min(values)
        max_val = max(values)
        
        option.update({
            "tooltip": {
                "position": "top",
                "trigger": "item"
            },
            "grid": {
                "height": "70%",
                "top": "10%"
            },
            "xAxis": {
                "type": "category",
                "data": x_data,
                "splitArea": {"show": True},
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "yAxis": {
                "type": "category",
                "data": y_cols,
                "splitArea": {"show": True},
                "axisLabel": {"color": "#666" if theme == "light" else "#999"}
            },
            "visualMap": {
                "min": min_val,
                "max": max_val,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "bottom": "5%",
                "inRange": {
                    "color": ["#50a3ba", "#eac736", "#d94e5d"]  # 蓝-黄-红渐变
                },
                "textStyle": {"color": option["textStyle"]["color"]}
            },
            "series": [{
                "name": "热力值",
                "type": "heatmap",
                "data": heatmap_data,
                "label": {
                    "show": True,
                    "color": "#000"
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }]
        })
        
        return option
