/**
 * NEUP Log Analyzer - 自定义前端交互脚本
 * 
 * 功能：
 * - 增强图表交互
 * - 快捷键支持
 * - 数据导出辅助
 * - 响应式布局优化
 * - 虚拟滚动支持
 * - 性能优化 (防抖/节流)
 */

(function() {
    'use strict';

    // 全局配置
    const CONFIG = {
        MOBILE_BREAKPOINT: 768,
        TABLET_BREAKPOINT: 1024,
        DEBOUNCE_DELAY: 200,
        VIRTUAL_SCROLL_THRESHOLD: 1000,
        VIRTUAL_SCROLL_BUFFER: 10
    };

    // 等待页面加载完成
    window.addEventListener('load', function() {
        console.log('🚀 NEUP Log Analyzer - 前端脚本已加载');
        
        // 初始化功能
        initKeyboardShortcuts();
        enhanceChartInteraction();
        addCustomTooltips();
        initResponsiveLayout();
        initPerformanceOptimization();
        initVirtualScroll();
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
     * 增强图表交互 - 使用强化版 MutationObserver
     * 监听 window.parent.document 以应对 Streamlit rerun 导致的 DOM 重置
     */
    function enhanceChartInteraction() {
        // 尝试监听父窗口（iframe 场景）
        const targetDocument = window.parent ? window.parent.document : document;
        
        const observer = new MutationObserver(debounce(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    // 重新绑定图表控件
                    const chartContainers = document.querySelectorAll('.streamlit-echarts');
                    chartContainers.forEach(function(container) {
                        if (!container.dataset.enhanced) {
                            container.dataset.enhanced = 'true';
                            addChartControls(container);
                            console.log('📊 图表控件已注入');
                        }
                    });
                    
                    // 重新绑定虚拟滚动
                    checkAndInitVirtualScroll();
                }
            });
        }, 100)); // 使用防抖避免过度触发

        // 监听整个文档树
        observer.observe(targetDocument.body || document.body, {
            childList: true,
            subtree: true,
            attributes: false // 不监听属性变化，减少性能开销
        });
        
        console.log('👁️  MutationObserver 已启动，监听 DOM 变化');
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

    // ==========================================
    // 工具函数库
    // ==========================================

    /**
     * 防抖函数 (Debounce)
     * 用于优化频繁触发的事件（如窗口 resize、输入框输入）
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                func.apply(context, args);
            }, wait || CONFIG.DEBOUNCE_DELAY);
        };
    }

    /**
     * 节流函数 (Throttle)
     * 用于限制高频事件的执行频率（如滚动事件）
     */
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const context = this;
            const args = arguments;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(function() {
                    inThrottle = false;
                }, limit || CONFIG.DEBOUNCE_DELAY);
            }
        };
    }

    // ==========================================
    // 响应式布局优化
    // ==========================================

    /**
     * 初始化响应式布局
     * 针对工业现场平板优化（iPad/Android Tablet）
     */
    function initResponsiveLayout() {
        const mediaQueryMobile = window.matchMedia(`(max-width: ${CONFIG.MOBILE_BREAKPOINT}px)`);
        const mediaQueryTablet = window.matchMedia(`(max-width: ${CONFIG.TABLET_BREAKPOINT}px)`);

        // 响应式处理函数
        function handleResponsive() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            const mainContent = document.querySelector('.main');

            if (mediaQueryMobile.matches) {
                // 手机屏幕：自动收起侧边栏
                if (sidebar) {
                    sidebar.style.transform = 'translateX(-100%)';
                    sidebar.style.transition = 'transform 0.3s ease';
                }
                console.log('📱 移动端模式：侧边栏已收起');
            } else if (mediaQueryTablet.matches) {
                // 平板屏幕：侧边栏缩小
                if (sidebar) {
                    sidebar.style.width = '250px';
                    sidebar.style.transition = 'width 0.3s ease';
                }
                console.log('📱 平板模式：侧边栏已缩小');
            } else {
                // 桌面屏幕：恢复默认
                if (sidebar) {
                    sidebar.style.transform = 'translateX(0)';
                    sidebar.style.width = '';
                }
            }

            // 图表自适应调整
            resizeCharts();
        }

        // 监听媒体查询变化
        mediaQueryMobile.addListener(handleResponsive);
        mediaQueryTablet.addListener(handleResponsive);

        // 初始化执行
        handleResponsive();

        // 添加侧边栏切换按钮（移动端）
        addSidebarToggle();

        console.log('📐 响应式布局已启用');
    }

    /**
     * 添加侧边栏切换按钮（移动端）
     */
    function addSidebarToggle() {
        const toggleBtn = document.createElement('button');
        toggleBtn.innerHTML = '☰';
        toggleBtn.className = 'sidebar-toggle-btn';
        toggleBtn.style.cssText = `
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 9999;
            background: rgba(102, 126, 234, 0.95);
            color: white;
            border: none;
            border-radius: 8px;
            width: 40px;
            height: 40px;
            font-size: 20px;
            cursor: pointer;
            display: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        `;

        toggleBtn.addEventListener('click', function() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                const isHidden = sidebar.style.transform === 'translateX(-100%)';
                sidebar.style.transform = isHidden ? 'translateX(0)' : 'translateX(-100%)';
            }
        });

        document.body.appendChild(toggleBtn);

        // 仅在移动端显示
        const mediaQuery = window.matchMedia(`(max-width: ${CONFIG.MOBILE_BREAKPOINT}px)`);
        function updateToggleBtnVisibility() {
            toggleBtn.style.display = mediaQuery.matches ? 'block' : 'none';
        }
        mediaQuery.addListener(updateToggleBtnVisibility);
        updateToggleBtnVisibility();
    }

    /**
     * 调整图表尺寸（应用防抖）
     */
    const resizeCharts = debounce(function() {
        const chartContainers = document.querySelectorAll('.streamlit-echarts');
        chartContainers.forEach(function(container) {
            const chartInstance = window.echarts && window.echarts.getInstanceByDom(container);
            if (chartInstance) {
                chartInstance.resize();
            }
        });
        console.log('📊 图表已重新调整尺寸');
    }, CONFIG.DEBOUNCE_DELAY);

    // ==========================================
    // 性能优化
    // ==========================================

    /**
     * 初始化性能优化
     */
    function initPerformanceOptimization() {
        // 窗口 resize 事件防抖
        window.addEventListener('resize', resizeCharts);

        // 滚动事件节流
        const scrollHandler = throttle(function() {
            // 可以在这里添加滚动相关的逻辑
            // 例如：懒加载、无限滚动等
        }, 100);
        window.addEventListener('scroll', scrollHandler);

        console.log('⚡ 性能优化已启用（防抖/节流）');
    }

    // ==========================================
    // 虚拟滚动实现
    // ==========================================

    /**
     * 虚拟滚动类
     * 用于优化大量 DOM 元素的渲染性能
     */
    class VirtualScroller {
        constructor(container, items, renderItem, itemHeight = 30) {
            this.container = container;
            this.items = items;
            this.renderItem = renderItem;
            this.itemHeight = itemHeight;
            this.visibleCount = Math.ceil(container.clientHeight / itemHeight) + CONFIG.VIRTUAL_SCROLL_BUFFER;
            this.startIndex = 0;
            
            this.init();
        }

        init() {
            // 创建容器
            this.viewport = document.createElement('div');
            this.viewport.style.cssText = `
                height: ${this.container.clientHeight}px;
                overflow-y: auto;
                position: relative;
            `;

            this.content = document.createElement('div');
            this.content.style.cssText = `
                height: ${this.items.length * this.itemHeight}px;
                position: relative;
            `;

            this.viewport.appendChild(this.content);
            this.container.innerHTML = '';
            this.container.appendChild(this.viewport);

            // 绑定滚动事件
            this.viewport.addEventListener('scroll', throttle(() => {
                this.render();
            }, 50));

            // 初始渲染
            this.render();
            console.log(`📜 虚拟滚动已初始化: ${this.items.length} 条数据`);
        }

        render() {
            const scrollTop = this.viewport.scrollTop;
            this.startIndex = Math.floor(scrollTop / this.itemHeight);
            const endIndex = Math.min(this.startIndex + this.visibleCount, this.items.length);

            // 清空当前内容
            this.content.innerHTML = '';

            // 仅渲染可见区域
            for (let i = this.startIndex; i < endIndex; i++) {
                const item = document.createElement('div');
                item.style.cssText = `
                    position: absolute;
                    top: ${i * this.itemHeight}px;
                    height: ${this.itemHeight}px;
                    width: 100%;
                    box-sizing: border-box;
                `;
                item.innerHTML = this.renderItem(this.items[i], i);
                this.content.appendChild(item);
            }
        }
    }

    /**
     * 初始化虚拟滚动
     */
    function initVirtualScroll() {
        checkAndInitVirtualScroll();
    }

    /**
     * 检查并初始化虚拟滚动（可重复调用）
     */
    function checkAndInitVirtualScroll() {
        // 查找日志文本容器
        const logContainers = document.querySelectorAll('pre, code, .stCodeBlock');
        
        logContainers.forEach(function(container) {
            if (container.dataset.virtualScrollEnabled) {
                return; // 已处理过
            }

            const lines = container.textContent.split('\n');
            
            // 仅对超过阈值的大数据启用虚拟滚动
            if (lines.length > CONFIG.VIRTUAL_SCROLL_THRESHOLD) {
                container.dataset.virtualScrollEnabled = 'true';
                
                // 创建虚拟滚动实例
                new VirtualScroller(
                    container,
                    lines,
                    function(line, index) {
                        return `<span style="color: #666; margin-right: 10px;">${index + 1}</span>${escapeHtml(line)}`;
                    },
                    20
                );
                
                console.log(`📜 已对 ${lines.length} 行数据启用虚拟滚动`);
            }
        });
    }

    /**
     * HTML 转义
     */
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

})();
