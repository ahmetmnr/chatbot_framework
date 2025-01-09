class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.currentAssistant = null;
        this.currentConversationId = null;
        
        // DOM elementlerini sakla
        this.messageInput = document.getElementById('message-input');
        this.chatMessages = document.getElementById('chat-messages');
        this.assistantSelect = document.getElementById('assistant-select');
        this.sendButton = document.getElementById('send-button');
        this.currentAssistantHeader = document.getElementById('current-assistant');
        
        // Modal elementleri
        this.createAssistantModal = new bootstrap.Modal(document.getElementById('createAssistantModal'));
        this.createAssistantForm = document.getElementById('create-assistant-form');
        this.createAssistantBtn = document.getElementById('create-assistant-btn');

        // Event listeners
        this.assistantSelect.addEventListener('change', (e) => {
            this.currentAssistant = e.target.value;
            if (this.currentAssistant) {
                this.currentAssistantHeader.textContent = `Chat with ${this.currentAssistant}`;
            }
        });
        
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Create assistant butonu için event listener
        this.createAssistantBtn.addEventListener('click', () => this.createAssistant());

        // Asistanları yükle
        this.loadAssistants();

        // Toast container'ı oluştur
        this.createToastContainer();
    }

    // Toast container'ı oluştur
    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '11';
        document.body.appendChild(container);
        this.toastContainer = container;
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
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const assistants = await response.json();
            
            // Mevcut seçenekleri temizle
            this.assistantSelect.innerHTML = '<option value="">Choose an assistant...</option>';
            
            // Yeni asistanları ekle
            assistants.forEach(assistant => {
                const option = document.createElement('option');
                option.value = assistant.name;
                option.textContent = assistant.name;
                this.assistantSelect.appendChild(option);
            });
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
        const toastElement = document.createElement('div');
        toastElement.className = 'toast align-items-center text-white bg-danger border-0';
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
}

// Global scope'a ekle
window.ChatApp = ChatApp;
