/**
 * NEUP Log Analyzer - 自定义前端交互脚本
 * 
 * 功能：
 * - 增强图表交互
 * - 快捷键支持
 * - 数据导出辅助
 */

(function() {
    'use strict';

    // 等待页面加载完成
    window.addEventListener('load', function() {
        console.log('🚀 NEUP Log Analyzer - 前端脚本已加载');
        
        // 初始化功能
        initKeyboardShortcuts();
        enhanceChartInteraction();
        addCustomTooltips();
    });

    /**
     * 初始化键盘快捷键
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + E: 导出数据
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const exportBtn = document.querySelector('[data-testid="stDownloadButton"]');
                if (exportBtn) {
                    exportBtn.click();
                    showNotification('正在导出数据...', 'info');
                }
            }
            
            // Ctrl/Cmd + R: 刷新数据（重新上传）
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                showNotification('提示：请使用侧边栏重新上传文件', 'info');
            }
            
            // F: 全屏切换（针对图表）
            if (e.key === 'f' && !e.ctrlKey && !e.metaKey) {
                toggleFullscreen();
            }
        });
        
        console.log('⌨️  快捷键已启用: Ctrl+E (导出), F (全屏)');
    }

    /**
     * 增强图表交互
     */
    function enhanceChartInteraction() {
        // 监听 ECharts 容器
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    const chartContainers = document.querySelectorAll('.streamlit-echarts');
                    chartContainers.forEach(function(container) {
                        if (!container.dataset.enhanced) {
                            container.dataset.enhanced = 'true';
                            addChartControls(container);
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * 为图表添加控制按钮
     */
    function addChartControls(chartContainer) {
        // 添加全屏按钮
        const controlBar = document.createElement('div');
        controlBar.className = 'chart-controls';
        controlBar.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            display: flex;
            gap: 5px;
        `;

        const fullscreenBtn = createButton('⛶', '全屏', function() {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                chartContainer.requestFullscreen();
            }
        });

        controlBar.appendChild(fullscreenBtn);
        
        // 确保容器有相对定位
        if (window.getComputedStyle(chartContainer).position === 'static') {
            chartContainer.style.position = 'relative';
        }
        
        chartContainer.appendChild(controlBar);
    }

    /**
     * 创建按钮辅助函数
     */
    function createButton(text, title, onClick) {
        const btn = document.createElement('button');
        btn.textContent = text;
        btn.title = title;
        btn.style.cssText = `
            background: rgba(102, 126, 234, 0.9);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        `;
        
        btn.addEventListener('mouseenter', function() {
            btn.style.background = 'rgba(102, 126, 234, 1)';
            btn.style.transform = 'scale(1.05)';
        });
        
        btn.addEventListener('mouseleave', function() {
            btn.style.background = 'rgba(102, 126, 234, 0.9)';
            btn.style.transform = 'scale(1)';
        });
        
        btn.addEventListener('click', onClick);
        return btn;
    }

    /**
     * 添加自定义提示
     */
    function addCustomTooltips() {
        // 为特定元素添加提示信息
        const elements = document.querySelectorAll('[data-testid="stMetric"]');
        elements.forEach(function(el) {
            el.title = '点击查看详细信息';
            el.style.cursor = 'pointer';
        });
    }

    /**
     * 全屏切换
     */
    function toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    }

    /**
     * 显示通知消息
     */
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'info' ? '#667eea' : '#43e97b'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        setTimeout(function() {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(function() {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // 添加 CSS 动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

})();
