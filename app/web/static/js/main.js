document.addEventListener('DOMContentLoaded', function() {
    // 全局变量
    let socket = null;
    let messageTypeChart = null;
    let dailyStatsChart = null;
    let currentFilter = 'all';
    
    // 初始化
    initSocket();
    loadConfig();
    loadMessages();
    initCharts();
    initEventListeners();
    
    // 初始添加一个目录配置
    addDirectoryConfig();
    
    // ===== 初始化函数 =====
    function initSocket() {
        "use strict";
        // 建立Socket.IO连接
        try {
            const socketProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const socketUrl = `${socketProtocol}//${window.location.host}/socket.io/?EIO=4&transport=websocket`;
            
            // 简单的轮询替代方案
            setInterval(() => {
                loadMessages();
                updateStats();
            }, 5000);
            
            console.log('Socket连接已初始化');
        } catch (error) {
            console.error('Socket连接初始化失败:', error);
        }
    }
    
    function loadConfig() {
        "use strict";
        // 加载配置
        fetch('/api/config')
            .then(response => response.json())
            .then(config => {
                // 填充表单
                document.getElementById('tmdb_api_key').value = config.tmdb_api_key || '';
                document.getElementById('douban_cookies').value = config.douban_cookies || '';
                document.getElementById('max_retries').value = config.max_retries || 3;
                document.getElementById('cache_expiry_days').value = config.cache_expiry_days || 30;
                
                // 加载目录配置
                const directoriesContainer = document.getElementById('directories-container');
                directoriesContainer.innerHTML = '';
                
                const directories = config.directories || [];
                if (directories.length === 0) {
                    addDirectoryConfig();
                } else {
                    directories.forEach(dir => {
                        addDirectoryConfig(dir);
                    });
                }
                
                // 更新监控状态
                document.getElementById('monitor-toggle').checked = config.monitor_enabled || false;
                updateMonitorStatus();
            })
            .catch(error => {
                console.error('加载配置失败:', error);
                showNotification('加载配置失败', 'error');
            });
    }
    
    function loadMessages(limit = 50) {
        "use strict";
        // 加载消息
        let url = `/api/messages?limit=${limit}`;
        if (currentFilter !== 'all') {
            url += `&type=${currentFilter}`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(messages => {
                updateMessagesList(messages);
                updateNotificationBadge(messages.length);
                updateStats(messages);
            })
            .catch(error => {
                console.error('加载消息失败:', error);
            });
    }
    
    function initCharts() {
        "use strict";
        // 初始化图表
        const messageTypeCtx = document.getElementById('message-type-chart').getContext('2d');
        const dailyStatsCtx = document.getElementById('daily-stats-chart').getContext('2d');
        
        // 消息类型统计图表
        messageTypeChart = new Chart(messageTypeCtx, {
            type: 'doughnut',
            data: {
                labels: ['系统', '文件处理', '错误', '成功'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#3b82f6', '#64748b', '#ef4444', '#10b981'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: '消息类型统计'
                    }
                }
            }
        });
        
        // 每日统计图表
        dailyStatsChart = new Chart(dailyStatsCtx, {
            type: 'bar',
            data: {
                labels: ['今天', '昨天', '前天'],
                datasets: [{
                    label: '成功',
                    data: [0, 0, 0],
                    backgroundColor: '#10b981'
                }, {
                    label: '错误',
                    data: [0, 0, 0],
                    backgroundColor: '#ef4444'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: '每日处理统计'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    function initEventListeners() {
        "use strict";
        // 配置表单提交
        document.getElementById('config-form').addEventListener('submit', handleConfigSubmit);
        
        // 添加目录配置
        document.getElementById('add-directory-btn').addEventListener('click', addDirectoryConfig);
        
        // 监控切换
        document.getElementById('monitor-toggle').addEventListener('change', handleMonitorToggle);
        
        // 批量处理按钮
        document.getElementById('run-batch-btn').addEventListener('click', handleRunBatch);
        document.getElementById('run-compare-btn').addEventListener('click', handleRunCompare);
        document.getElementById('refresh-btn').addEventListener('click', refreshData);
        
        // 消息过滤
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', handleMessageFilter);
        });
        
        // 清空消息
        document.getElementById('clear-messages-btn').addEventListener('click', handleClearMessages);
        
        // 通知按钮
        document.getElementById('notifications-btn').addEventListener('click', handleNotificationsClick);
        
        // 重做模态框
        document.getElementById('close-redo-modal').addEventListener('click', closeRedoModal);
        document.getElementById('close-redo-modal-btn').addEventListener('click', closeRedoModal);
        document.getElementById('process-all-redo-btn').addEventListener('click', processAllRedo);
        
        // 主题切换
        document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    }
    
    // ===== 事件处理函数 =====
    function handleConfigSubmit(event) {
        "use strict";
        event.preventDefault();
        
        // 收集目录配置
        const directories = [];
        document.querySelectorAll('#directories-container > div').forEach(container => {
            const name = container.querySelector('.dir-name').value;
            const source = container.querySelector('.dir-source').value;
            const target = container.querySelector('.dir-target').value;
            
            if (name && source && target) {
                directories.push({ name, source, target });
            }
        });
        
        // 构建配置对象
        const config = {
            tmdb_api_key: document.getElementById('tmdb_api_key').value,
            douban_cookies: document.getElementById('douban_cookies').value,
            max_retries: parseInt(document.getElementById('max_retries').value) || 3,
            cache_expiry_days: parseInt(document.getElementById('cache_expiry_days').value) || 30,
            directories: directories,
            monitor_enabled: document.getElementById('monitor-toggle').checked
        };
        
        // 保存配置
        fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('配置保存成功', 'success');
            } else {
                showNotification(`保存失败: ${data.error || '未知错误'}`, 'error');
            }
        })
        .catch(error => {
            console.error('保存配置失败:', error);
            showNotification('保存配置失败', 'error');
        });
    }
    
    function handleMonitorToggle(event) {
        "use strict";
        const enabled = event.target.checked;
        
        fetch('/api/toggle_monitor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateMonitorStatus();
                showNotification(enabled ? '监控已开启' : '监控已关闭', 'success');
            } else {
                event.target.checked = !enabled; // 恢复状态
                showNotification(`操作失败: ${data.error || '未知错误'}`, 'error');
            }
        })
        .catch(error => {
            console.error('切换监控状态失败:', error);
            event.target.checked = !enabled; // 恢复状态
            showNotification('操作失败', 'error');
        });
    }
    
    function handleRunBatch() {
        "use strict";
        // 显示加载状态
        const btn = document.getElementById('run-batch-btn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 处理中...';
        
        // 获取第一个目录配置
        const firstDir = document.querySelector('#directories-container > div');
        if (!firstDir) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('请先配置目录', 'error');
            return;
        }
        
        const source_dir = firstDir.querySelector('.dir-source').value;
        const target_dir = firstDir.querySelector('.dir-target').value;
        
        if (!source_dir || !target_dir) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('请填写完整的目录信息', 'error');
            return;
        }
        
        fetch('/api/run_batch_process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ source_dir, target_dir, mode: 'all' })
        })
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            
            if (data.success) {
                showNotification(`批量处理完成: 成功 ${data.success_count}, 失败 ${data.error_count}`, 'success');
                // 重新加载消息
                setTimeout(() => {
                    loadMessages();
                }, 1000);
            } else {
                showNotification(`处理失败: ${data.error || '未知错误'}`, 'error');
            }
        })
        .catch(error => {
            console.error('批量处理失败:', error);
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('处理失败', 'error');
        });
    }
    
    function handleRunCompare() {
        "use strict";
        // 显示加载状态
        const btn = document.getElementById('run-compare-btn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 比较中...';
        
        // 获取第一个目录配置
        const firstDir = document.querySelector('#directories-container > div');
        if (!firstDir) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('请先配置目录', 'error');
            return;
        }
        
        const source_dir = firstDir.querySelector('.dir-source').value;
        const target_dir = firstDir.querySelector('.dir-target').value;
        
        if (!source_dir || !target_dir) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('请填写完整的目录信息', 'error');
            return;
        }
        
        fetch('/api/run_batch_process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ source_dir, target_dir, mode: 'compare' })
        })
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            
            if (data.success) {
                showNotification(`比较处理完成: 成功 ${data.success_count}, 失败 ${data.error_count}`, 'success');
                // 重新加载消息
                setTimeout(() => {
                    loadMessages();
                }, 1000);
            } else {
                showNotification(`处理失败: ${data.error || '未知错误'}`, 'error');
            }
        })
        .catch(error => {
            console.error('比较处理失败:', error);
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('处理失败', 'error');
        });
    }
    
    function handleMessageFilter(event) {
        "use strict";
        // 更新过滤器状态
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active', 'bg-primary', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        });
        
        const btn = event.target;
        btn.classList.add('active', 'bg-primary', 'text-white');
        btn.classList.remove('bg-gray-200', 'text-gray-700');
        
        // 设置当前过滤器
        currentFilter = btn.textContent.trim() === '全部' ? 'all' : 
                       btn.textContent.trim() === '成功' ? 'file_process' :
                       btn.textContent.trim() === '错误' ? 'error' :
                       btn.textContent.trim() === '系统' ? 'system' : 'redo';
        
        // 重新加载消息
        loadMessages();
    }
    
    function handleClearMessages() {
        "use strict";
        if (confirm('确定要清空所有消息吗？')) {
            fetch('/api/clear_messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type: currentFilter === 'all' ? null : currentFilter })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('消息已清空', 'success');
                    loadMessages();
                }
            })
            .catch(error => {
                console.error('清空消息失败:', error);
                showNotification('清空失败', 'error');
            });
        }
    }
    
    function handleNotificationsClick() {
        "use strict";
        // 显示重做命令模态框
        loadRedoCommands();
        document.getElementById('redo-modal').classList.remove('hidden');
    }
    
    // ===== 辅助函数 =====
    function addDirectoryConfig(dir = {}) {
        "use strict";
        const container = document.getElementById('directories-container');
        const index = container.children.length + 1;
        
        const div = document.createElement('div');
        div.className = 'bg-gray-50 p-3 rounded-lg border border-gray-200 relative';
        
        div.innerHTML = `
            <div class="absolute -top-2 -right-2">
                <button type="button" class="remove-dir-btn bg-danger text-white w-6 h-6 rounded-full flex items-center justify-center hover:bg-danger/90">
                    <i class="fa fa-times"></i>
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
                <div>
                    <label class="block text-xs text-gray-500 mb-1">名称</label>
                    <input type="text" class="dir-name w-full px-2 py-1 border border-gray-300 rounded text-sm" placeholder="如：电影/电视剧" value="${dir.name || ''}">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">源目录</label>
                    <input type="text" class="dir-source w-full px-2 py-1 border border-gray-300 rounded text-sm" placeholder="/source" value="${dir.source || ''}">
                </div>
                <div>
                    <label class="block text-xs text-gray-500 mb-1">目标目录</label>
                    <input type="text" class="dir-target w-full px-2 py-1 border border-gray-300 rounded text-sm" placeholder="/target" value="${dir.target || ''}">
                </div>
            </div>
        `;
        
        // 添加删除事件
        div.querySelector('.remove-dir-btn').addEventListener('click', function() {
            if (container.children.length > 1) {
                container.removeChild(div);
            } else {
                showNotification('至少保留一个目录配置', 'warning');
            }
        });
        
        container.appendChild(div);
    }
    
    function updateMessagesList(messages) {
        "use strict";
        const container = document.getElementById('messages-list');
        
        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    暂无消息
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        messages.forEach(msg => {
            const msgEl = createMessageElement(msg);
            container.appendChild(msgEl);
        });
    }
    
    function createMessageElement(message) {
        "use strict";
        const div = document.createElement('div');
        
        // 根据消息类型设置样式
        let iconClass = 'fa-info-circle text-primary';
        let bgClass = 'bg-blue-50 border-blue-200';
        
        if (message.type === 'file_process') {
            if (message.success) {
                iconClass = 'fa-check-circle text-secondary';
                bgClass = 'bg-green-50 border-green-200';
            } else {
                iconClass = 'fa-times-circle text-danger';
                bgClass = 'bg-red-50 border-red-200';
            }
        } else if (message.type === 'error') {
            iconClass = 'fa-exclamation-circle text-danger';
            bgClass = 'bg-red-50 border-red-200';
        } else if (message.type === 'success') {
            iconClass = 'fa-check-circle text-secondary';
            bgClass = 'bg-green-50 border-green-200';
        }
        
        div.className = `p-3 rounded-lg border ${bgClass} transition-all duration-300 hover:shadow-sm`;
        
        // 格式化时间
        const timeStr = formatTimestamp(message.timestamp);
        
        // 构建消息内容
        let content = '';
        if (message.type === 'file_process') {
            content = `
                <div class="flex items-start">
                    <i class="fa ${iconClass} mt-1 mr-3"></i>
                    <div class="flex-1">
                        <div class="font-medium">${message.success ? '处理成功' : '处理失败'}</div>
                        <div class="text-sm text-gray-600 mt-1">来源: ${truncatePath(message.source)}</div>
                        ${message.destination ? `<div class="text-sm text-gray-600">目标: ${truncatePath(message.destination)}</div>` : ''}
                        ${message.message ? `<div class="text-sm text-gray-600 mt-1">${message.message}</div>` : ''}
                        <div class="text-xs text-gray-500 mt-1">${timeStr}</div>
                    </div>
                </div>
            `;
        } else {
            content = `
                <div class="flex items-start">
                    <i class="fa ${iconClass} mt-1 mr-3"></i>
                    <div class="flex-1">
                        <div class="font-medium">${message.message || '无消息内容'}</div>
                        <div class="text-xs text-gray-500 mt-1">${timeStr}</div>
                    </div>
                </div>
            `;
        }
        
        div.innerHTML = content;
        return div;
    }
    
    function loadRedoCommands() {
        "use strict";
        fetch('/api/redo_commands')
            .then(response => response.json())
            .then(commands => {
                const container = document.getElementById('redo-commands-list');
                
                if (commands.length === 0) {
                    container.innerHTML = '<div class="text-center text-gray-500 py-4">暂无重做命令</div>';
                    return;
                }
                
                container.innerHTML = '';
                
                commands.forEach(cmd => {
                    const div = document.createElement('div');
                    div.className = 'p-3 border border-gray-200 rounded-lg flex justify-between items-center';
                    
                    div.innerHTML = `
                        <div>
                            <div class="text-sm font-medium">${cmd.message || '重做文件处理'}</div>
                            <div class="text-xs text-gray-500">${formatTimestamp(cmd.timestamp)}</div>
                        </div>
                        <button type="button" class="execute-redo-btn bg-primary hover:bg-primary/90 text-white px-3 py-1 rounded text-sm" data-id="${cmd.id}">
                            执行
                        </button>
                    `;
                    
                    // 添加执行事件
                    div.querySelector('.execute-redo-btn').addEventListener('click', function() {
                        const redoId = parseInt(this.getAttribute('data-id'));
                        executeRedo(redoId);
                    });
                    
                    container.appendChild(div);
                });
            })
            .catch(error => {
                console.error('加载重做命令失败:', error);
            });
    }
    
    function executeRedo(redoId) {
        "use strict";
        fetch(`/api/execute_redo/${redoId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('重做命令执行成功', 'success');
                loadRedoCommands();
                loadMessages();
            } else {
                showNotification(`执行失败: ${data.error || '未知错误'}`, 'error');
            }
        })
        .catch(error => {
            console.error('执行重做命令失败:', error);
            showNotification('执行失败', 'error');
        });
    }
    
    function processAllRedo() {
        "use strict";
        const redoBtns = document.querySelectorAll('.execute-redo-btn');
        if (redoBtns.length === 0) return;
        
        let currentIndex = 0;
        
        function processNext() {
            if (currentIndex < redoBtns.length) {
                const btn = redoBtns[currentIndex];
                btn.click();
                currentIndex++;
                setTimeout(processNext, 1000);
            } else {
                showNotification('所有重做命令已处理', 'success');
                closeRedoModal();
            }
        }
        
        processNext();
    }
    
    function closeRedoModal() {
        "use strict";
        document.getElementById('redo-modal').classList.add('hidden');
    }
    
    function updateMonitorStatus() {
        "use strict";
        const enabled = document.getElementById('monitor-toggle').checked;
        const statusEl = document.getElementById('monitor-status');
        
        if (enabled) {
            statusEl.textContent = '已启用';
            statusEl.className = 'text-lg font-semibold text-secondary';
        } else {
            statusEl.textContent = '已禁用';
            statusEl.className = 'text-lg font-semibold text-gray-500';
        }
    }
    
    function updateNotificationBadge(count) {
        "use strict";
        const badge = document.getElementById('notification-badge');
        
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
    
    function updateStats(messages = []) {
        "use strict";
        // 统计错误消息数量
        const errorCount = messages.filter(m => m.type === 'error' || (m.type === 'file_process' && !m.success)).length;
        document.getElementById('error-count').textContent = errorCount;
        
        // 统计今日成功数量
        const today = new Date().toDateString();
        const todaySuccess = messages.filter(m => {
            const msgDate = new Date(m.timestamp).toDateString();
            return msgDate === today && m.type === 'file_process' && m.success;
        }).length;
        document.getElementById('today-success').textContent = todaySuccess;
        
        // 更新图表数据
        updateChartsData(messages);
    }
    
    function updateChartsData(messages) {
        "use strict";
        // 统计各类型消息数量
        const typeCounts = {
            system: messages.filter(m => m.type === 'system').length,
            file_process: messages.filter(m => m.type === 'file_process').length,
            error: messages.filter(m => m.type === 'error').length,
            success: messages.filter(m => m.type === 'file_process' && m.success).length
        };
        
        // 更新消息类型图表
        messageTypeChart.data.datasets[0].data = [
            typeCounts.system,
            typeCounts.file_process,
            typeCounts.error,
            typeCounts.success
        ];
        messageTypeChart.update();
        
        // 更新每日统计图表（模拟数据）
        dailyStatsChart.data.datasets[0].data = [typeCounts.success, Math.floor(typeCounts.success * 0.8), Math.floor(typeCounts.success * 0.6)];
        dailyStatsChart.data.datasets[1].data = [typeCounts.error, Math.floor(typeCounts.error * 0.7), Math.floor(typeCounts.error * 0.5)];
        dailyStatsChart.update();
    }
    
    function refreshData() {
        "use strict";
        loadConfig();
        loadMessages();
        showNotification('数据已刷新', 'success');
    }
    
    function showNotification(message, type = 'info') {
        "use strict";
        // 创建通知元素
        const notification = document.createElement('div');
        
        // 设置样式
        let bgColor = 'bg-primary';
        let iconClass = 'fa-info-circle';
        
        if (type === 'success') {
            bgColor = 'bg-secondary';
            iconClass = 'fa-check-circle';
        } else if (type === 'error') {
            bgColor = 'bg-danger';
            iconClass = 'fa-exclamation-circle';
        } else if (type === 'warning') {
            bgColor = 'bg-warning';
            iconClass = 'fa-exclamation-triangle';
        }
        
        notification.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center justify-between fixed bottom-4 right-4 z-50 transform transition-all duration-300 translate-y-full`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fa ${iconClass} mr-2"></i>
                <span>${message}</span>
            </div>
            <button class="ml-4 text-white hover:text-gray-200">
                <i class="fa fa-times"></i>
            </button>
        `;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 显示通知
        setTimeout(() => {
            notification.classList.remove('translate-y-full');
        }, 100);
        
        // 自动关闭
        const timer = setTimeout(() => {
            notification.classList.add('translate-y-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
        
        // 点击关闭
        notification.querySelector('button').addEventListener('click', () => {
            clearTimeout(timer);
            notification.classList.add('translate-y-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        });
    }
    
    function toggleTheme() {
        "use strict";
        const body = document.body;
        const icon = document.querySelector('#theme-toggle i');
        
        if (body.classList.contains('dark')) {
            // 切换到亮色模式
            body.classList.remove('dark');
            icon.className = 'fa fa-moon-o text-gray-600';
        } else {
            // 切换到暗色模式
            body.classList.add('dark');
            icon.className = 'fa fa-sun-o text-yellow-400';
        }
    }
    
    // 工具函数
    function formatTimestamp(timestamp) {
        "use strict";
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    function truncatePath(path, maxLength = 30) {
        "use strict";
        if (!path || path.length <= maxLength) return path;
        
        const parts = path.split('/');
        const lastPart = parts[parts.length - 1];
        
        if (lastPart.length > maxLength - 3) {
            return lastPart.substring(0, maxLength - 3) + '...';
        }
        
        return '.../' + lastPart;
    }
});