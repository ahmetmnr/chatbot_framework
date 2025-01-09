class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.currentAssistant = null;
        this.initializeElements();
        this.attachEventListeners();
        this.loadAssistants();
    }

    initializeElements() {
        // DOM elementlerini seç
        this.assistantSelect = document.getElementById('assistantSelect');
        this.createAssistantBtn = document.getElementById('createAssistant');
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendMessageBtn = document.getElementById('sendMessage');
        this.modal = document.getElementById('createAssistantModal');
        this.assistantForm = document.getElementById('assistantForm');
    }

    attachEventListeners() {
        // Event listener'ları ekle
        this.createAssistantBtn.addEventListener('click', () => this.showModal());
        this.assistantForm.addEventListener('submit', (e) => this.handleAssistantCreate(e));
        this.sendMessageBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.assistantSelect.addEventListener('change', () => {
            this.currentAssistant = this.assistantSelect.value;
            this.chatMessages.innerHTML = '';
        });
    }

    async loadAssistants() {
        try {
            const response = await fetch(`${this.apiUrl}/assistants/list`);
            const assistants = await response.json();
            
            this.assistantSelect.innerHTML = '<option value="">Asistan Seçin...</option>';
            assistants.forEach(assistant => {
                const option = document.createElement('option');
                option.value = assistant.name;
                option.textContent = `${assistant.name} (${assistant.model_type})`;
                this.assistantSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Asistanlar yüklenirken hata:', error);
            this.showError('Asistanlar yüklenemedi');
        }
    }

    showModal() {
        this.modal.style.display = 'block';
    }

    hideModal() {
        this.modal.style.display = 'none';
        this.assistantForm.reset();
    }

    async handleAssistantCreate(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('assistantName').value,
            model_type: document.getElementById('modelType').value,
            system_message: document.getElementById('systemMessage').value
        };

        try {
            const response = await fetch(`${this.apiUrl}/assistants/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error('Asistan oluşturulamadı');

            await this.loadAssistants();
            this.hideModal();
        } catch (error) {
            console.error('Asistan oluşturma hatası:', error);
            this.showError('Asistan oluşturulamadı');
        }
    }

    addMessage(content, isUser = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        messageDiv.textContent = content;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.currentAssistant) return;

        this.addMessage(message, true);
        this.messageInput.value = '';

        try {
            const response = await fetch(
                `${this.apiUrl}/assistants/${this.currentAssistant}/chat/stream?message=${encodeURIComponent(message)}`,
                {
                    method: 'GET',
                    headers: {
                        'Accept': 'text/event-stream'
                    }
                }
            );

            // Asistan yanıtı için yeni bir mesaj oluştur
            let assistantMessage = document.createElement('div');
            assistantMessage.className = 'message assistant';
            this.chatMessages.appendChild(assistantMessage);
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = ''; // SSE satırlarını birleştirmek için buffer

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // Chunk'ı decode et ve buffer'a ekle
                buffer += decoder.decode(value, { stream: true });

                // Buffer'ı satırlara böl
                let lines = buffer.split('\n');
                // Son satır tamamlanmamış olabilir, buffer'da tut
                buffer = lines.pop() || '';

                // Tam satırları işle
                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine.startsWith('data: ')) {
                        const token = trimmedLine.slice(6); // "data: " prefix'ini kaldır
                        if (token && token !== '[DONE]') {
                            assistantMessage.textContent += token;
                            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                        }
                    }
                }
            }

            // Stream bitti, kalan buffer'ı kontrol et
            if (buffer.trim().startsWith('data: ')) {
                const token = buffer.trim().slice(6);
                if (token && token !== '[DONE]') {
                    assistantMessage.textContent += token;
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }
            }

        } catch (error) {
            console.error('Mesaj gönderme hatası:', error);
            this.showError('Mesaj gönderilemedi');
        }
    }

    showError(message) {
        // Basit bir hata gösterimi
        alert(message);
    }
}

// Uygulama başlatma
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
