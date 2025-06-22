document.addEventListener('DOMContentLoaded', () => {
    // 自动获取API基础URL
    const getApiBaseUrl = () => {
        // 1. 获取当前页面的基础域名
        const currentDomain = window.location.hostname;
        
        // 2. 如果存在自定义数据属性，则使用它（可以在HTML中设置）
        const apiUrlFromMeta = document.querySelector('meta[name="api-base-url"]')?.getAttribute('content');
        
        // 3. 如果meta标签值不为空且不等于模板变量原文，则使用它
        if (apiUrlFromMeta && apiUrlFromMeta !== "{{API_BASE_URL}}") {
            console.log("使用meta标签中的API基础URL:", apiUrlFromMeta);
            return apiUrlFromMeta;
        }
        
        // 4. 默认回退到当前基础域名（添加协议和端口）
        const port = window.location.port ? `:${window.location.port}` : '';
        const defaultUrl = `${window.location.protocol}//${currentDomain}${port}`;
        console.log("使用默认API基础URL:", defaultUrl);
        return defaultUrl;
    };

    const API_BASE_URL = getApiBaseUrl();
    console.log("最终使用的API基础URL:", API_BASE_URL);

    // --- DOM Elements ---
    const sidebarLinks = document.querySelectorAll('.sidebar nav a');
    const contentSections = document.querySelectorAll('.content-section');
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    // KB Management
    const createKbForm = document.getElementById('create-kb-form');
    const kbNameInput = document.getElementById('kb-name');
    const dimensionSelect = document.getElementById('dimension');
    const indexTypeSelect = document.getElementById('index-type');
    const refreshKbListBtn = document.getElementById('refresh-kb-list');
    const deleteKbSelect = document.getElementById('delete-kb-select');
    const deleteKbBtn = document.getElementById('delete-kb-btn');
    const kbListTableBody = document.querySelector('#kb-list-table tbody');

    // File Management
    const uploadKbSelect = document.getElementById('upload-kb-select');
    const fileKbSelect = document.getElementById('file-kb-select');
    const uploadFileForm = document.getElementById('upload-file-form');
    const filesToUploadInput = document.getElementById('files-to-upload');
    const chunkMethodSelect = document.getElementById('chunk-method');
    const chunkSizeInput = document.getElementById('chunk-size');
    const chunkSizeValue = document.getElementById('chunk-size-value');
    const fileListTableBody = document.querySelector('#file-list-table tbody');
    const uploadProgressContainer = document.getElementById('upload-progress-container');
    const uploadProgressBar = document.getElementById('upload-progress-bar');
    const uploadStatusDiv = document.getElementById('upload-status');

    // Search
    const searchKbSelect = document.getElementById('search-kb-select');
    const searchForm = document.getElementById('search-form');
    const searchQueryInput = document.getElementById('search-query');
    const topKInput = document.getElementById('top-k');
    const useRerankCheckbox = document.getElementById('use-rerank');
    const searchResultsDiv = document.getElementById('search-results');

    // Chat
    const chatKbSelect = document.getElementById('chat-kb-select');
    const chatHistoryDiv = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const temperatureInput = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    const chatTopKInput = document.getElementById('chat-top-k');
    let chatHistory = [];

    // App Management
    const addAppBtn = document.getElementById('add-app-btn');
    const addAppFormContainer = document.getElementById('add-app-form-container');
    const addAppForm = document.getElementById('add-app-form');
    const appNameInput = document.getElementById('app-name');
    const appIconSelect = document.getElementById('app-icon');
    const appUrlInput = document.getElementById('app-url');
    const appDescriptionInput = document.getElementById('app-description');
    const cancelAddAppBtn = document.getElementById('cancel-add-app');
    const appGrid = document.getElementById('app-grid');
    const resetAppsBtn = document.getElementById('reset-apps-btn');

    // Toast Container
    const toastContainer = document.getElementById('toast-container');

    // --- UI Event Handlers ---
    // Update range slider values
    chunkSizeInput.addEventListener('input', () => {
        chunkSizeValue.textContent = chunkSizeInput.value;
    });
    
    temperatureInput.addEventListener('input', () => {
        temperatureValue.textContent = temperatureInput.value;
    });

    // Theme toggle
    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDarkTheme = document.body.classList.contains('dark-theme');
        themeToggleBtn.innerHTML = isDarkTheme ? '<i class="bx bx-moon"></i>' : '<i class="bx bx-sun"></i>';
        localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
    });

    // --- Helper Functions ---
    const showToast = (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let iconClass = 'bx-info-circle';
        if (type === 'success') iconClass = 'bx-check-circle';
        if (type === 'error') iconClass = 'bx-error-circle';
        if (type === 'warning') iconClass = 'bx-error';
        
        toast.innerHTML = `
            <div class="toast-icon"><i class="bx ${iconClass}"></i></div>
            <div class="toast-content">
                <p class="toast-message">${message}</p>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Remove toast after animation completes
        setTimeout(() => {
            toast.remove();
        }, 3000);
    };
    
    const fetchAPI = async (endpoint, options = {}) => {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || '请求失败');
            }
            return response.json();
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            showToast(`API错误: ${error.message}`, 'error');
            throw error;
        }
    };

    // --- Knowledge Base Functions ---
    const refreshKbList = async () => {
        try {
            const data = await fetchAPI('/kb/list');
            const kbList = data.data || [];
            
            // Clear existing options and table
            kbListTableBody.innerHTML = '';
            const selects = [deleteKbSelect, uploadKbSelect, fileKbSelect, searchKbSelect, chatKbSelect];
            selects.forEach(s => s.innerHTML = '<option value="">-- 请选择知识库 --</option>');

            if (kbList.length === 0) {
                kbListTableBody.innerHTML = '<tr><td colspan="4" class="text-center">没有找到知识库</td></tr>';
                return;
            }

            // Populate selects
            kbList.forEach(kbName => {
                selects.forEach(s => {
                    const option = document.createElement('option');
                    option.value = kbName;
                    option.textContent = kbName;
                    s.appendChild(option);
                });
            });

            // Populate table
            const infoPromises = kbList.map(name => fetchAPI(`/kb/info/${name}`));
            const infos = await Promise.all(infoPromises);

            infos.forEach(infoData => {
                const info = infoData.data;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${info.kb_name}</td>
                    <td>${info.dimension}</td>
                    <td>${info.index_type}</td>
                    <td>${info.vector_count}</td>
                `;
                kbListTableBody.appendChild(row);
            });

        } catch (error) {
            kbListTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">加载知识库列表失败</td></tr>';
        }
    };

    const handleCreateKb = async (e) => {
        e.preventDefault();
        const kbName = kbNameInput.value.trim();
        if (!kbName) {
            showToast('知识库名称不能为空', 'warning');
            return;
        }

        try {
            const result = await fetchAPI('/kb/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    kb_name: kbName,
                    dimension: parseInt(dimensionSelect.value),
                    index_type: indexTypeSelect.value
                })
            });
            showToast(result.message, 'success');
            kbNameInput.value = '';
            await refreshKbList();
        } catch (error) {
            // Error is already shown by fetchAPI
        }
    };

    const handleDeleteKb = async () => {
        const kbName = deleteKbSelect.value;
        if (!kbName) {
            showToast('请选择要删除的知识库', 'warning');
            return;
        }
        if (!confirm(`确定要删除知识库 "${kbName}" 吗？此操作不可逆！`)) {
            return;
        }
        try {
            const result = await fetchAPI(`/kb/delete/${kbName}`, { method: 'DELETE' });
            showToast(result.message, 'success');
            await refreshKbList();
        } catch (error) {
            // Error handling in fetchAPI
        }
    };

    // --- File Management Functions ---
    const handleKbSelectionForFiles = async () => {
        const kbName = fileKbSelect.value;
        fileListTableBody.innerHTML = '';
        if (!kbName) return;

        try {
            const result = await fetchAPI(`/kb/files/${kbName}`);
            const files = result.data || [];
            if (files.length === 0) {
                fileListTableBody.innerHTML = '<tr><td colspan="5" class="text-center">此知识库中没有文件</td></tr>';
                return;
            }
            files.forEach(file => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${file.file_name}</td>
                    <td>${(file.file_size / 1024).toFixed(2)} KB</td>
                    <td>${file.chunks_count || 0}</td>
                    <td>${new Date(file.add_time).toLocaleString()}</td>
                    <td>
                        <button class="danger delete-file-btn" data-kb="${kbName}" data-filename="${file.file_name}">
                            <i class='bx bx-trash'></i> 删除
                        </button>
                    </td>
                `;
                fileListTableBody.appendChild(row);
            });
        } catch (error) {
            fileListTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">加载文件列表失败</td></tr>';
        }
    };

    const handleDeleteFile = async (e) => {
        if (!e.target.classList.contains('delete-file-btn')) return;
        
        const kbName = e.target.dataset.kb;
        const fileName = e.target.dataset.filename;

        if (!confirm(`确定要删除文件 "${fileName}" 吗？`)) return;

        try {
            await fetchAPI(`/kb/file/${kbName}/${fileName}`, { method: 'DELETE' });
            showToast('文件删除成功', 'success');
            await handleKbSelectionForFiles(); // Refresh list
        } catch (error) {
            // error handled in fetchAPI
        }
    };

    const handleUploadFiles = async (e) => {
        e.preventDefault();
        const kbName = uploadKbSelect.value;
        const files = filesToUploadInput.files;

        if (!kbName || files.length === 0) {
            showToast('请选择知识库和文件', 'warning');
            return;
        }

        const formData = new FormData();
        formData.append('kb_name', kbName);
        for (const file of files) {
            formData.append('files', file);
        }
        // Add chunk config as a JSON string
        const chunkConfig = { 
            method: chunkMethodSelect.value, 
            chunk_size: parseInt(chunkSizeInput.value), 
            chunk_overlap: Math.floor(parseInt(chunkSizeInput.value) * 0.2) // 20% overlap
        };
        formData.append('chunk_config', JSON.stringify(chunkConfig));

        uploadProgressContainer.style.display = 'block';
        uploadProgressBar.style.width = '0%';
        uploadStatusDiv.textContent = '正在上传...';

        try {
            const response = await fetch(`${API_BASE_URL}/kb/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || '上传失败');
            }
            const result = await response.json();
            
            if (result.task_id) {
                uploadStatusDiv.textContent = '文件上传成功，正在后台处理...';
                pollTaskProgress(result.task_id);
            } else {
                 uploadStatusDiv.textContent = result.message || '上传处理完成';
                 uploadProgressBar.style.width = '100%';
            }

            uploadFileForm.reset();
            chunkSizeValue.textContent = '1000'; // Reset displayed value
            
        } catch (error) {
            uploadStatusDiv.textContent = `上传失败: ${error.message}`;
        }
    };
    
    const pollTaskProgress = async (taskId) => {
        const interval = setInterval(async () => {
            try {
                const result = await fetchAPI(`/kb/progress/${taskId}`);
                const task = result.data;
                uploadProgressBar.style.width = `${task.progress}%`;
                uploadStatusDiv.textContent = task.message;

                if (task.status === 'completed' || task.status === 'failed') {
                    clearInterval(interval);
                    if(task.status === 'completed'){
                       showToast('文件处理成功!', 'success');
                       // Refresh the file list if we're on the file management tab
                       if (document.querySelector('#file-management').classList.contains('active') && fileKbSelect.value) {
                           handleKbSelectionForFiles();
                       }
                    } else {
                       showToast(`文件处理失败: ${task.message}`, 'error');
                    }
                    setTimeout(() => {
                        uploadProgressContainer.style.display = 'none';
                    }, 5000);
                }
            } catch (error) {
                clearInterval(interval);
                uploadStatusDiv.textContent = '获取处理进度失败。';
            }
        }, 2000);
    };


    // --- Search Functions ---
    const handleSearch = async (e) => {
        e.preventDefault();
        const kbName = searchKbSelect.value;
        const query = searchQueryInput.value.trim();

        if (!kbName || !query) {
            showToast('请选择知识库并输入问题', 'warning');
            return;
        }
        
        searchResultsDiv.innerHTML = '<div class="text-center"><i class="bx bx-loader-alt bx-spin" style="font-size: 2rem;"></i><p>正在检索中...</p></div>';
        
        try {
            const result = await fetchAPI('/kb/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    kb_name: kbName,
                    query: query,
                    top_k: parseInt(topKInput.value, 10),
                    use_rerank: useRerankCheckbox.checked
                })
            });

            const results = result.data || [];
            if (results.length === 0) {
                searchResultsDiv.innerHTML = '<p class="text-center">未找到相关内容。</p>';
                return;
            }
            searchResultsDiv.innerHTML = results.map((item, index) => `
                <div class="result-item">
                    <h4>
                        ${index + 1}. ${item.metadata?.source || '未知来源'} 
                        <span class="score">相关度: ${item.score.toFixed(3)}</span>
                    </h4>
                    <p>${item.content?.replace(/\n/g, '<br>') || item.text?.replace(/\n/g, '<br>') || '内容为空'}</p>
                </div>
            `).join('');
        } catch (error) {
             searchResultsDiv.innerHTML = `<p class="text-center text-danger">检索失败: ${error.message}</p>`;
        }
    };

    // --- Chat Functions ---
    const handleSendMessage = async () => {
        const kbName = chatKbSelect.value;
        const query = chatInput.value.trim();

        if (!kbName || !query) {
            showToast('请选择知识库并输入问题', 'warning');
            return;
        }

        chatHistory.push({ role: 'user', content: query });
        chatHistory.push({ 
            role: 'assistant', 
            content: '<i class="bx bx-loader-alt bx-spin"></i> 思考中...',
            context: null 
        });
        renderChatHistory(); // Render user message and "Thinking" message
        
        const assistantIndex = chatHistory.length - 1;
        chatInput.value = '';
        chatInput.disabled = true;
        chatSendBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/kb/chat_stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    kb_name: kbName,
                    query: query,
                    history: chatHistory.slice(0, -2),
                    temperature: parseFloat(temperatureInput.value),
                    top_k: parseInt(chatTopKInput.value || 3)
                })
            });
            
            if (!response.ok) throw new Error((await response.json()).detail || '请求失败');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantResponse = '';
            chatHistory[assistantIndex].content = ''; // Clear "Thinking..."

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n').filter(line => line.trim() !== '');

                for (const line of lines) {
                    try {
                        const parsed = JSON.parse(line);
                        if (parsed.type === 'context') {
                            chatHistory[assistantIndex].context = parsed.data;
                        } else if (parsed.type === 'answer') {
                            assistantResponse += parsed.data;
                            chatHistory[assistantIndex].content = assistantResponse;
                        } else if (parsed.type === 'error') {
                            throw new Error(parsed.data);
                        }
                    } catch (e) {
                        console.error("Failed to parse JSON chunk:", line, e);
                    }
                }
                renderSingleMessage(assistantIndex);
            }

        } catch (error) {
            chatHistory[assistantIndex].content = `抱歉，出错了: ${error.message}`;
            renderSingleMessage(assistantIndex);
        } finally {
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    };
    
    const renderSingleMessage = (index) => {
        const msg = chatHistory[index];
        const messageElement = document.getElementById(`chat-message-${index}`);
        
        const contextHtml = msg.context ? `
            <div class="context-container">
                <details>
                    <summary>查看参考信息</summary>
                    <div class="context-list">
                        ${msg.context.map(ctx => `
                            <div class="context-item">
                                <strong>来源: ${ctx.metadata?.source || '未知'} (相关度: ${ctx.score.toFixed(3)})</strong>
                                <p>${ctx.content}</p>
                            </div>
                        `).join('')}
                    </div>
                </details>
            </div>
        ` : '';
        
        const contentHtml = msg.content.replace(/\n/g, '<br>');
        
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            contentDiv.innerHTML = contentHtml + contextHtml;
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        } else {
            renderChatHistory();
        }
    };
    
    const renderChatHistory = () => {
        chatHistoryDiv.innerHTML = chatHistory.map((msg, index) => {
             const contextHtml = msg.context ? `
                <div class="context-container">
                    <details>
                        <summary>查看参考信息</summary>
                        <div class="context-list">
                            ${msg.context.map(ctx => `
                                <div class="context-item">
                                    <strong>来源: ${ctx.metadata?.source || '未知'} (相关度: ${ctx.score.toFixed(3)})</strong>
                                    <p>${ctx.content}</p>
                                </div>
                            `).join('')}
                        </div>
                    </details>
                </div>
            ` : '';
            return `
                <div class="chat-message ${msg.role}-message" id="chat-message-${index}">
                    <div class="message-header">${msg.role === 'user' ? '您' : 'AI助手'}</div>
                    <div class="message-content">
                        ${msg.content.replace(/\n/g, '<br>')}
                        ${contextHtml}
                    </div>
                </div>
            `;
        }).join('');
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    };

    const handleClearChat = () => {
        if (chatHistory.length === 0 || confirm('确定要清空当前对话吗？')) {
            chatHistory = [];
            renderChatHistory();
        }
    };

    // --- App Management Functions ---
    // Load apps using AppConfigManager
    const loadApps = async () => {
        try {
            const apps = await appConfigManager.loadApps();
            renderApps(apps);
        } catch (error) {
            console.error('加载应用失败:', error);
            showToast('加载应用列表失败', 'error');
        }
    };

    // Render apps in the grid
    const renderApps = (apps) => {
        if (apps.length === 0) {
            appGrid.innerHTML = `
                <div class="text-center" style="grid-column: 1/-1; padding: 40px 0;">
                    <i class='bx bx-grid-alt' style="font-size: 3rem; color: var(--text-light-color);"></i>
                    <p>暂无应用，点击"添加应用"按钮创建新应用</p>
                </div>
            `;
            return;
        }

        appGrid.innerHTML = apps.map((app, index) => `
            <div class="app-card">
                <div class="app-header">
                    <h4><i class='bx ${app.icon}'></i> ${app.name}</h4>
                </div>
                <div class="app-body">
                    <p class="app-description">${app.description || '无描述'}</p>
                </div>
                <div class="app-footer">
                    <a href="${app.url}" target="_blank" class="secondary">
                        <i class='bx bx-link-external'></i> 打开
                    </a>
                    <div class="app-actions">
                        <button class="delete-app-btn danger" data-index="${index}">
                            <i class='bx bx-trash'></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Add event listeners to delete buttons
        document.querySelectorAll('.delete-app-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                if (confirm('确定要删除此应用吗？')) {
                    try {
                        const updatedApps = await appConfigManager.deleteApp(index);
                        renderApps(updatedApps);
                        showToast('应用已删除', 'success');
                    } catch (error) {
                        showToast('删除应用失败', 'error');
                    }
                }
            });
        });
    };

    // Handle add app form submission
    const handleAddApp = async (e) => {
        e.preventDefault();
        
        const name = appNameInput.value.trim();
        const icon = appIconSelect.value;
        const url = appUrlInput.value.trim();
        const description = appDescriptionInput.value.trim();
        
        if (!name || !url) {
            showToast('应用名称和URL不能为空', 'warning');
            return;
        }
        
        // Validate URL
        try {
            new URL(url);
        } catch (e) {
            showToast('请输入有效的URL', 'warning');
            return;
        }
        
        const app = { name, icon, url, description };
        
        try {
            const updatedApps = await appConfigManager.addApp(app);
            renderApps(updatedApps);
            
            // Reset form and hide it
            addAppForm.reset();
            addAppFormContainer.style.display = 'none';
            
            showToast('应用添加成功', 'success');
        } catch (error) {
            showToast('添加应用失败', 'error');
        }
    };
    
    // Handle reset apps button
    const handleResetApps = async () => {
        if (confirm('确定要重置为默认应用列表吗？这将删除所有自定义应用。')) {
            try {
                const defaultApps = await appConfigManager.resetToDefault();
                renderApps(defaultApps);
                showToast('已重置为默认应用列表', 'success');
            } catch (error) {
                showToast('重置应用列表失败', 'error');
            }
        }
    };

    // --- Event Listeners ---
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            sidebarLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            link.classList.add('active');
            document.querySelector(link.getAttribute('href')).classList.add('active');
        });
    });

    createKbForm.addEventListener('submit', handleCreateKb);
    refreshKbListBtn.addEventListener('click', refreshKbList);
    deleteKbBtn.addEventListener('click', handleDeleteKb);
    
    fileKbSelect.addEventListener('change', handleKbSelectionForFiles);
    uploadFileForm.addEventListener('submit', handleUploadFiles);
    fileListTableBody.addEventListener('click', handleDeleteFile);

    searchForm.addEventListener('submit', handleSearch);

    chatSendBtn.addEventListener('click', handleSendMessage);
    clearChatBtn.addEventListener('click', handleClearChat);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // App management event listeners
    addAppBtn.addEventListener('click', () => {
        addAppFormContainer.style.display = 'block';
    });
    
    cancelAddAppBtn.addEventListener('click', () => {
        addAppForm.reset();
        addAppFormContainer.style.display = 'none';
    });
    
    addAppForm.addEventListener('submit', handleAddApp);
    
    // 添加重置应用按钮的事件监听器
    if (resetAppsBtn) {
        resetAppsBtn.addEventListener('click', handleResetApps);
    }

    // --- Initial Load ---
    const initialize = async () => {
        // Load theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggleBtn.innerHTML = '<i class="bx bx-moon"></i>';
        }
        
        await refreshKbList();
        await loadApps();
        
        // Activate the first tab
        document.querySelector('.sidebar nav a').click();
    };

    initialize();
}); 