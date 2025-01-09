class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.token = localStorage.getItem('token');
        
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
    }

    initializeApp() {
        // Asistanları yükle
        this.loadAssistants();
        
        // Event listeners'ları ekle
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
                    'Authorization': `Bearer ${this.token}`  // Token eklendi
                }
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Token geçersizse login sayfasına yönlendir
                    localStorage.removeItem('token');
                    this.showAuthContainer();
                    return;
                }
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
            this.showError('Failed to load assistants');
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
        if (!message || !this.currentAssistant) return;

        // Kullanıcı mesajını ekle
        this.addMessage(message, true);
        this.messageInput.value = '';

        try {
            let url = `${this.apiUrl}/assistants/${encodeURIComponent(this.currentAssistant)}/chat/stream?message=${encodeURIComponent(message)}`;
            
            // Eğer mevcut bir konuşma varsa, ID'sini ekle
            if (this.currentConversationId) {
                url += `&conversation_id=${this.currentConversationId}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Authorization': `Bearer ${this.token}`  // Token eklendi
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Token geçersizse login sayfasına yönlendir
                    localStorage.removeItem('token');
                    this.showAuthContainer();
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Asistan yanıtı için yeni bir mesaj oluştur
            let assistantMessage = document.createElement('div');
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
                reader.cancel();
            }

            // İlk mesaj gönderildiğinde conversation_id'yi al
            if (!this.currentConversationId) {
                const headerConversationId = response.headers.get('X-Conversation-Id');
                if (headerConversationId) {
                    this.currentConversationId = headerConversationId;
                }
            }

        } catch (error) {
            console.error('Mesaj gönderme hatası:', error);
            this.showError('Mesaj gönderilemedi: ' + error.message);
        }
    }

    showError(message) {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '11';
        
        toastContainer.innerHTML = `
            <div class="toast align-items-center text-white bg-danger border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        document.body.appendChild(toastContainer);
        const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
        toast.show();
        
        toastContainer.addEventListener('hidden.bs.toast', () => {
            toastContainer.remove();
        });
    }

    // Auth metodları
    async handleLogin(event) {
        event.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            // OAuth2PasswordRequestForm formatında gönder
            const formData = new URLSearchParams();
            formData.append('username', email);    // username = email
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
            this.toggleAuthForms('login'); // Varsayılan olarak login formunu göster
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

    async loadConversations() {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/conversations`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Token geçersizse login sayfasına yönlendir
                    localStorage.removeItem('token');
                    this.showAuthContainer();
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const conversations = await response.json();

            // Konuşmaları listele
            const conversationList = document.getElementById('conversations-list');
            if (conversationList) {
                conversationList.innerHTML = ''; // Listeyi temizle

                conversations.forEach(conv => {
                    const item = document.createElement('div');
                    item.classList.add('conversation-item', 'p-2', 'border-bottom');
                    
                    // Konuşma detaylarını göster
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${conv.assistant_name}</strong>
                                <small class="text-muted">${new Date(conv.created_at).toLocaleString()}</small>
                            </div>
                            <button class="btn btn-sm btn-outline-primary load-chat" 
                                    data-conversation-id="${conv.id}">
                                Load Chat
                            </button>
                        </div>
                    `;
                    
                    // Load Chat butonuna tıklama olayı ekle
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
            
            // Mesajları chat alanına yükle
            if (this.chatMessages) {
                this.chatMessages.innerHTML = ''; // Chat alanını temizle
                
                messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.role === 'user' ? 'user' : 'assistant'}`;
                    messageDiv.textContent = msg.content;
                    this.chatMessages.appendChild(messageDiv);
                });
                
                // Chat alanını en alta kaydır
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }
        } catch (error) {
            console.error('Failed to load chat:', error);
            this.showError('Failed to load chat: ' + error.message);
        }
    }
}

// Global scope'a ekle
window.ChatApp = ChatApp;
