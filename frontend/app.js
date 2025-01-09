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

        // Event listener'ları ekle
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

        // Asistanları yükle
        this.loadAssistants();
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
            const response = await fetch(
                `${this.apiUrl}/assistants/${encodeURIComponent(this.currentAssistant)}/chat/stream?message=${encodeURIComponent(message)}`,
                {
                    method: 'GET',
                    headers: {
                        'Accept': 'text/event-stream',
                        'Cache-Control': 'no-cache'
                    }
                }
            );

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
}

// Global scope'a ekle
window.ChatApp = ChatApp;
