class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.currentAssistant = null;
        
        // DOM elementlerini sakla
        this.messageInput = document.getElementById('message-input');
        this.chatMessages = document.getElementById('chat-messages');
        this.assistantSelect = document.getElementById('assistant-select');
        this.sendButton = document.getElementById('send-button');
        this.currentAssistantHeader = document.getElementById('current-assistant');
        this.createAssistantBtn = document.getElementById('create-assistant-btn');
        
        // Modal elementleri
        this.createAssistantModal = new bootstrap.Modal(document.getElementById('createAssistantModal'));
        this.createAssistantForm = document.getElementById('create-assistant-form');

        // Event listeners'ları güvenli bir şekilde ekle
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

        if (this.createAssistantBtn) {
            this.createAssistantBtn.addEventListener('click', () => this.createAssistant());
        }

        // Konuşma listesi için container - opsiyonel
        this.conversationsContainer = document.getElementById('conversations-list');
        const loadConversationsBtn = document.getElementById('load-conversations');
        if (loadConversationsBtn) {
            loadConversationsBtn.addEventListener('click', () => this.loadConversations());
        }

        // Asistanları yükle
        this.loadAssistants();
    }

    // Toast container'ı oluştur
    createToastContainer() {
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '11';
            document.body.appendChild(container);
            this.toastContainer = container;
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
                    'Cache-Control': 'no-cache'
                }
            });

            if (!response.ok) {
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

    async loadAssistants() {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/list`);
            if (!response.ok) throw new Error('Failed to load assistants');
            
            const assistants = await response.json();
            if (this.assistantSelect) {
                this.assistantSelect.innerHTML = '<option value="">Select an assistant...</option>';
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

    // Başarı mesajı göster
    showSuccess(message) {
        const toastElement = document.createElement('div');
        toastElement.className = 'toast align-items-center text-white bg-success border-0';
        toastElement.setAttribute('role', 'alert');
        toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        this.toastContainer.appendChild(toastElement);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Hata mesajı göster
    showError(message) {
        // Error container'ı kontrol et ve gerekirse oluştur
        if (!this.errorContainer) {
            this.createErrorContainer();
        }
        
        if (this.errorContainer) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger alert-dismissible fade show';
            errorDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            this.errorContainer.appendChild(errorDiv);
            
            // 5 saniye sonra otomatik kapat
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        } else {
            console.error('Error container not found:', message);
        }
    }

    async createAssistant() {
        const name = document.getElementById('assistant-name').value;
        const modelType = document.getElementById('model-type').value;
        const systemMessage = document.getElementById('system-message').value;
        const temperature = document.getElementById('temperature')?.value || 0.7;

        try {
            const response = await fetch(`${this.apiUrl}/assistants/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    model_type: modelType,
                    system_message: systemMessage,
                    config: {
                        temperature: parseFloat(temperature)
                    }
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create assistant');
            }

            // Asistan listesini yenile
            await this.loadAssistants();
            
            // Modal'ı kapat
            const modal = bootstrap.Modal.getInstance(document.getElementById('createAssistantModal'));
            modal.hide();
            
            // Başarı mesajı göster
            this.showSuccess('Assistant created successfully');

        } catch (error) {
            console.error('Error creating assistant:', error);
            this.showError(error.message || 'Failed to create assistant');
        }
    }

    async loadConversations() {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/conversations`);
            if (!response.ok) throw new Error('Failed to load conversations');
            
            const conversations = await response.json();
            if (this.conversationsContainer) {
                this.conversationsContainer.innerHTML = '';
                
                conversations.forEach(conv => {
                    const convDiv = document.createElement('div');
                    convDiv.className = 'conversation-item p-2 border-bottom';
                    
                    // Son mesajı bul
                    const lastMessage = conv.messages[conv.messages.length - 1];
                    const lastMessagePreview = lastMessage ? 
                        lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? '...' : '') : 
                        'No messages';
                    
                    convDiv.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-1">Chat with ${conv.assistant_name}</h6>
                            <small class="text-muted">${new Date(conv.created_at).toLocaleString()}</small>
                        </div>
                        <p class="mb-1 text-muted small">${lastMessagePreview}</p>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary load-chat" data-conv-id="${conv.id}">
                                Load Chat
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-chat" data-conv-id="${conv.id}">
                                Delete
                            </button>
                        </div>
                    `;
                    
                    // Load Chat butonu için event listener
                    const loadBtn = convDiv.querySelector('.load-chat');
                    if (loadBtn) {
                        loadBtn.addEventListener('click', () => this.loadConversation(conv));
                    }
                    
                    // Delete butonu için event listener
                    const deleteBtn = convDiv.querySelector('.delete-chat');
                    if (deleteBtn) {
                        deleteBtn.addEventListener('click', () => this.deleteConversation(conv.id));
                    }
                    
                    this.conversationsContainer.appendChild(convDiv);
                });
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showError('Failed to load conversations');
        }
    }

    // Konuşma yükleme metodu
    async loadConversation(conversation) {
        if (this.chatMessages) {
            this.chatMessages.innerHTML = '';
            conversation.messages.forEach(msg => {
                this.appendMessage(msg.role, msg.content);
            });
            
            // Asistan seçimini güncelle
            if (this.assistantSelect) {
                this.assistantSelect.value = conversation.assistant_name;
                this.currentAssistant = conversation.assistant_name;
            }
            
            if (this.currentAssistantHeader) {
                this.currentAssistantHeader.textContent = `Chat with ${conversation.assistant_name}`;
            }
            
            // Otomatik scroll
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    // Konuşma silme metodu
    async deleteConversation(conversationId) {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/conversations/${conversationId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete conversation');
            
            await this.loadConversations();
            this.showSuccess('Conversation deleted successfully');
        } catch (error) {
            console.error('Error deleting conversation:', error);
            this.showError('Failed to delete conversation');
        }
    }

    // appendMessage metodunu ekle
    appendMessage(role, content) {
        if (this.chatMessages) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            // Markdown veya kod içeriği varsa işle
            if (content.includes('```')) {
                const formattedContent = content.replace(/```([\s\S]*?)```/g, (match, code) => {
                    return `<pre><code>${code.trim()}</code></pre>`;
                });
                messageDiv.innerHTML = formattedContent;
            } else {
                messageDiv.textContent = content;
            }
            
            this.chatMessages.appendChild(messageDiv);
            
            // Otomatik scroll
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
}

// DOM yüklendikten sonra uygulama başlat
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
