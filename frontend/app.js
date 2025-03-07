class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.token = localStorage.getItem('token');
        this.currentConversationId = null;  // Mevcut sohbet oturumunun ID'sini tutar

        // DOM elementleri
        this.authContainer = document.getElementById('auth-container');
        this.mainContainer = document.getElementById('main-container');
        this.messageInput = document.getElementById('message-input');
        this.chatMessages = document.getElementById('chat-messages');
        this.assistantSelect = document.getElementById('assistant-select');
        this.sendButton = document.getElementById('send-button');
        this.currentAssistantHeader = document.getElementById('current-assistant');

        // Token kontrolü
        if (!this.token) {
            this.showAuthContainer();
        } else {
            this.showMainContainer();
            this.initializeApp();
        }

        // Auth event listeners
        this.setupAuthEventListeners();

        // Load Conversations butonu için event listener
        const loadConversationsBtn = document.getElementById('load-conversations');
        if (loadConversationsBtn) {
            loadConversationsBtn.addEventListener('click', () => this.loadConversations());
        }

        // Logout butonu için event listener
        const logoutBtn = document.getElementById('logout-button');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Model parametreleri için event listener'lar
        ['temperature', 'top-p', 'max-tokens', 'frequency-penalty', 'presence-penalty'].forEach(param => {
            const slider = document.getElementById(param);
            const value = document.getElementById(`${param}-value`);
            if (slider && value) {
                slider.addEventListener('input', (e) => {
                    value.textContent = e.target.value;
                });
            }
        });

        // Model seçimi değiştiğinde
        const modelType = document.getElementById('model-type');
        if (modelType) {
            modelType.addEventListener('change', () => this.loadModels(modelType.value));
        }

        // Create Assistant butonu için event listener
        const createAssistantBtn = document.getElementById('create-assistant-btn');
        if (createAssistantBtn) {
            createAssistantBtn.addEventListener('click', () => this.createAssistant());
        }

        // Yeni Sohbet butonu
        const newChatButton = document.getElementById('new-chat-button');
        if (newChatButton) {
            newChatButton.addEventListener('click', () => this.startNewConversation());
        }

        this.initFileUpload();
    }

    initializeApp() {
        // Asistanları yükle
        this.loadAssistants();

        // Event listeners
        if (this.assistantSelect) {
            this.assistantSelect.addEventListener('change', (e) => {
                this.currentAssistant = e.target.value;
                if (this.currentAssistant && this.currentAssistantHeader) {
                    this.currentAssistantHeader.textContent = `Chat with ${this.currentAssistant}`;
                }
            });
        }

        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendMessage();
            });
        }
    }

    async loadAssistants() {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/list`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const assistants = await response.json();

            // Asistan listesini güncelle
            if (this.assistantSelect) {
                this.assistantSelect.innerHTML = '<option value="">Choose an assistant...</option>';
                assistants.forEach(assistant => {
                    const option = document.createElement('option');
                    option.value = assistant.name;
                    option.textContent = assistant.name;
                    this.assistantSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading assistants:', error);
            this.showError('Failed to load assistants: ' + error.message);
        }
    }

    addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        messageDiv.textContent = text;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.currentAssistant) {
            this.showError('Lütfen bir asistan seçin ve mesaj girin');
            return;
        }

        try {
            // Mesajı göster
            this.addMessage(message, true);
            this.messageInput.value = '';

            // URL oluştur
            const url = new URL(`${this.apiUrl}/assistants/${encodeURIComponent(this.currentAssistant)}/chat/stream`);
            url.searchParams.append('message', message);
            
            if (this.currentConversationId) {
                url.searchParams.append('conversation_id', this.currentConversationId);
            }

            // Fetch isteği
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Accept': 'text/event-stream'
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            // Conversation ID'yi header'dan al
            const newConversationId = response.headers.get('X-Conversation-Id');
            if (newConversationId && !this.currentConversationId) {
                this.currentConversationId = newConversationId;
                console.log('Yeni konuşma ID:', this.currentConversationId);
            }

            // Asistan yanıtı için yeni bir mesaj oluştur
            const assistantMessage = document.createElement('div');
            assistantMessage.className = 'message assistant';
            this.chatMessages.appendChild(assistantMessage);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    let lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        const trimmedLine = line.trim();
                        if (trimmedLine.startsWith('data: ')) {
                            const token = trimmedLine.slice(6);
                            if (token && token !== '[DONE]') {
                                if (token.startsWith('error:')) {
                                    throw new Error(token.slice(6));
                                }
                                assistantMessage.textContent += token;
                                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                            }
                        }
                    }
                }
            } catch (streamError) {
                console.error('Stream error:', streamError);
                throw streamError;
            } finally {
                // Reader'ı sonlandır
                reader.cancel();
            }

        } catch (error) {
            console.error('Mesaj gönderme hatası:', error);
            this.showError(`Hata: ${error.message}`);
            this.addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', false);
        }
    }

    showError(message) {
        const alertContainer = document.getElementById('alert-container') || document.body;
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertContainer.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    showSuccess(message) {
        const alertContainer = document.getElementById('alert-container') || document.body;
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertContainer.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // ===================== AUTH METHODS =====================
    async handleLogin(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${this.apiUrl}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            // Token'ı sakla
            this.token = data.access_token;
            localStorage.setItem('token', this.token);

            // Ana uygulamayı başlat
            this.showMainContainer();
            this.initializeApp();

        } catch (error) {
            console.error('Login error:', error);
            this.showError('Error: ' + error.message);
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        const email = document.getElementById('register-email').value;
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;

        try {
            const response = await fetch(`${this.apiUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, username, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            // Başarılı kayıt mesajı göster
            this.showSuccess('Registration successful! Please login.');
            // Login formunu göster
            this.toggleAuthForms('login');

        } catch (error) {
            console.error('Registration error:', error);
            this.showError(error.message);
        }
    }

    toggleAuthForms(show = 'login') {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');

        if (!loginForm || !registerForm) {
            console.error('Auth forms not found in DOM');
            return;
        }

        if (show === 'login') {
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
        } else {
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
        }
    }

    showAuthContainer() {
        if (this.authContainer) {
            this.authContainer.style.display = 'block';
            this.toggleAuthForms('login');
        }
        if (this.mainContainer) {
            this.mainContainer.style.display = 'none';
        }
    }

    showMainContainer() {
        if (this.authContainer) {
            this.authContainer.style.display = 'none';
        }
        if (this.mainContainer) {
            this.mainContainer.style.display = 'block';
        }
    }

    setupAuthEventListeners() {
        const loginForm = document.getElementById('login-form-element');
        const registerForm = document.getElementById('register-form-element');
        const showRegisterBtn = document.getElementById('show-register');
        const showLoginBtn = document.getElementById('show-login');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }
        if (showRegisterBtn) {
            showRegisterBtn.addEventListener('click', () => this.toggleAuthForms('register'));
        }
        if (showLoginBtn) {
            showLoginBtn.addEventListener('click', () => this.toggleAuthForms('login'));
        }
    }
    // ========================================================

    async loadConversations() {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/conversations`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const conversations = await response.json();
            const conversationList = document.getElementById('conversations-list');

            if (conversationList) {
                conversationList.innerHTML = ''; // Listeyi temizle

                conversations.forEach(conv => {
                    const item = document.createElement('div');
                    item.classList.add('conversation-item', 'p-2', 'border-bottom', 'hover-bg-light');

                    // Tarih formatını düzenle
                    const date = new Date(conv.created_at);
                    const formattedDate = date.toLocaleString('tr-TR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="conversation-info">
                                <div class="fw-bold text-truncate" style="max-width: 150px;">
                                    ${conv.assistant_name}
                                </div>
                                <small class="text-muted">
                                    <i class="bi bi-clock"></i> ${formattedDate}
                                </small>
                            </div>
                            <button class="btn btn-sm btn-primary load-chat" 
                                    data-conversation-id="${conv.id}">
                                <i class="bi bi-chat-dots"></i> Load
                            </button>
                        </div>
                    `;

                    // Load Chat butonuna tıklama
                    const loadChatBtn = item.querySelector('.load-chat');
                    if (loadChatBtn) {
                        loadChatBtn.addEventListener('click', () => this.loadChat(conv.id));
                    }

                    conversationList.appendChild(item);
                });
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
            this.showError('Failed to load conversations: ' + error.message);
        }
    }

    async loadChat(conversationId) {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/conversations/${conversationId}/messages`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const messages = await response.json();

            // Chat alanını temizle
            if (this.chatMessages) {
                this.chatMessages.innerHTML = '';
                // conversation_id'yi sakla
                this.currentConversationId = conversationId;
            }

            // Mesajları ekrana bas
            messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${msg.role === 'user' ? 'user' : 'assistant'}`;
                messageDiv.textContent = msg.content;
                this.chatMessages.appendChild(messageDiv);
            });

            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;

        } catch (error) {
            console.error('Failed to load chat:', error);
            this.showError('Failed to load chat: ' + error.message);
        }
    }

    async handleLogout() {
        try {
            const response = await fetch(`${this.apiUrl}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Logout failed');
            }

            // Token'ı sil ve login sayfasına yönlendir
            localStorage.removeItem('token');
            this.token = null;

            // UI güncelle
            this.authContainer.style.display = 'block';
            this.mainContainer.style.display = 'none';

            // Login formunu sıfırla
            document.getElementById('login-email').value = '';
            document.getElementById('login-password').value = '';

        } catch (error) {
            console.error('Logout error:', error);
            this.showError('Logout failed: ' + error.message);
        }
    }

    async loadModels(provider) {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/models`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const models = await response.json();
            const modelSelect = document.getElementById('model-name');

            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Select a model...</option>';

                // Seçilen sağlayıcıya göre modeller
                if (models[provider]) {
                    models[provider].forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            this.showError('Failed to load models: ' + error.message);
        }
    }

    async createAssistant() {
        try {
            const name = document.getElementById('assistant-name').value;
            const modelType = document.getElementById('model-type').value;
            const modelName = document.getElementById('model-name').value;
            const systemMessage = document.getElementById('system-message').value;

            if (!name || !modelType || !modelName || !systemMessage) {
                this.showError('Please fill in all required fields');
                return;
            }

            const config = {
                temperature: parseFloat(document.getElementById('temperature').value),
                top_p: parseFloat(document.getElementById('top-p').value),
                max_tokens: parseInt(document.getElementById('max-tokens').value),
                frequency_penalty: parseFloat(document.getElementById('frequency-penalty').value),
                presence_penalty: parseFloat(document.getElementById('presence-penalty').value)
            };

            const response = await fetch(`${this.apiUrl}/assistants/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    name: name,
                    model_type: modelType,
                    model_name: modelName,
                    system_message: systemMessage,
                    config: config
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            // Modal'ı kapat (Bootstrap 5)
            const modal = bootstrap.Modal.getInstance(document.getElementById('createAssistantModal'));
            if (modal) modal.hide();

            // Asistan listesini yenile
            await this.loadAssistants();

            // Başarı mesajı
            this.showSuccess('Assistant created successfully!');

        } catch (error) {
            console.error('Failed to create assistant:', error);
            this.showError('Failed to create assistant: ' + error.message);
        }
    }

    // ===================== Yeni sohbet başlatma =====================
    startNewConversation() {
        this.currentConversationId = null;
        this.clearChatMessages();

        // Başlık güncelle
        if (this.currentAssistant && this.currentAssistantHeader) {
            this.currentAssistantHeader.textContent = `New Chat with ${this.currentAssistant}`;
        }

        // Mesaj input alanını temizle
        if (this.messageInput) {
            this.messageInput.value = '';
        }

        console.log('Started new conversation');
    }

    clearChatMessages() {
        if (this.chatMessages) {
            this.chatMessages.innerHTML = '';
        }
    }

    initFileUpload() {
        const dropZone = document.querySelector('.file-drop-zone');
        if (!dropZone) return;

        // Drag & Drop event handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file) await this.handleFileUpload(file);
        });

        // Click to upload
        dropZone.addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf,.docx,.txt,.md';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) await this.handleFileUpload(file);
            };
            input.click();
        });
    }

    async handleFileUpload(file) {
        // Dosya tipi kontrolü
        const validTypes = ['application/pdf', 
                          'text/plain',
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        
        if(!validTypes.includes(file.type)) {
            this.showError('Desteklenmeyen dosya formatı');
            return;
        }
        
        // Dosya boyutu kontrolü (20MB)
        if(file.size > 20 * 1024 * 1024) {
            this.showError('Dosya boyutu 20MB sınırını aşıyor');
            return;
        }
        
        // Yükleme işlemi
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${this.apiUrl}/documents/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                },
                body: formData
            });
            
            if(!response.ok) throw new Error(await response.text());
            
            // Başarılı yanıt
            const result = await response.json();
            this.updateFileList(result);
            
        } catch(error) {
            console.error('Yükleme hatası:', error);
            this.showError(`Sunucu hatası: ${error.message}`);
        }
    }

    addFileToList(fileData) {
        const fileList = document.querySelector('.file-list');
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item p-2 mb-2 border rounded';
        fileItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="bi bi-file-text me-2"></i>
                    ${fileData.title} (${Math.round(fileData.file_size/1024)}KB)
                </div>
                <span class="badge bg-success">Yüklendi</span>
            </div>
        `;
        fileList.prepend(fileItem);
    }
}

// Global scope'a ekle
window.ChatApp = ChatApp;
