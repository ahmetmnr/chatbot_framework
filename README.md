# Chatbot Framework

Bu framework, farklı dil modellerini (LLM) ve RAG (Retrieval-Augmented Generation) sistemlerini entegre eden modüler bir chatbot altyapısı sunar. OpenAI GPT ve Ollama gibi farklı modelleri destekler ve özelleştirilebilir bilgi tabanı ile zenginleştirilmiş yanıtlar üretebilir.

## 🌟 Özellikler

### Çoklu Model Desteği
- **OpenAI GPT**: GPT-3.5 ve GPT-4 modelleri
- **Ollama**: Yerel modeller ve özelleştirilmiş LLM'ler
- **Genişletilebilir**: Yeni model servisleri kolayca eklenebilir

### RAG (Retrieval-Augmented Generation)
- Çoklu RAG sistemi desteği
- Ağırlıklı bilgi kaynakları
- Özelleştirilebilir belge kaynakları
- Bağlam zenginleştirme

### Veritabanı
- PostgreSQL ile güçlü veri yönetimi
- Asenkron veritabanı işlemleri
- Konuşma geçmişi ve oturum yönetimi

### API
- FastAPI ile modern REST API
- Streaming yanıt desteği
- Swagger/OpenAPI dokümantasyonu

## 📁 Proje Yapısı
plaintext
chatbot_framework/
├── api/ # API şemaları ve bağımlılıklar
├── core/ # Temel bileşenler
│ ├── database/ # Veritabanı modelleri
│ ├── models/ # Asistan modeli
│ ├── rag/ # RAG sistemleri
│ └── services/ # Model servisleri
├── routers/ # API route'ları
└── scripts/ # Yardımcı scriptler


## 🚀 Kurulum

### 1. Gereksinimleri Yükleyin
Virtual environment oluşturun (opsiyonel ama önerilen)
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
Gereksinimleri yükleyin
pip install -r requirements.txt


### 2. PostgreSQL Kurulumu
- PostgreSQL'i yükleyin
- Yeni bir veritabanı oluşturun:

CREATE DATABASE chatbot_db;


### 3. Çevresel Değişkenler
`.env` dosyası oluşturun:
Database Configuration
DB_NAME=chatbot_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
OpenAI Configuration
OPENAI_API_KEY=your_openai_key


### 4. Veritabanı Tablolarını Oluşturun
python scripts/create_database.py

### 5. Uygulamayı Başlatın

uvicorn app:app --reload


## 💻 API Kullanımı

### Asistan Oluşturma
curl -X POST "http://localhost:8000/assistants/create" \
-H "Content-Type: application/json" \
-d '{
"name": "my_assistant",
"model_type": "openai",
"system_message": "You are a helpful assistant."
}'

### Mesaj Gönderme
curl -X POST "http://localhost:8000/assistants/my_assistant/chat" \
-H "Content-Type: application/json" \
-d '{
"message": "What is the meaning of life?",
"stream": false
}'

### Streaming Yanıt Alma
curl "http://localhost:8000/assistants/my_assistant/chat/stream?message=Tell+me+a+story"


### RAG Sistemi Ekleme
curl -X POST "http://localhost:8000/rag/my_assistant/add" \
-H "Content-Type: application/json" \
-d '{
"name": "company_docs",
"weight": 1.0,
"enabled": true,
"documents": {
"doc1": "Company information...",
"doc2": "Product details..."
}
}'


## 🔧 Geliştirme

### Yeni Model Servisi Ekleme
1. `core/services/` altında yeni bir servis modülü oluşturun
2. `BaseLanguageModel` sınıfını implement edin:

from .base_model import BaseLanguageModel
class NewModelService(BaseLanguageModel):
async def generate_text(self, prompt: str) -> str:
# Model implementasyonu
pass
async def generate_stream(self, prompt: str):
# Streaming implementasyonu
pass


### Yeni RAG Sistemi Ekleme
1. `core/rag/` altında yeni bir RAG modülü oluşturun
2. `BaseRAG` sınıfını implement edin:

from .base_rag import BaseRAG

class NewRAGSystem(BaseRAG):

async def query(self, query: str) -> dict:
# RAG sistemi implementasyonu


## 🧪 Test

### Veritabanı Testleri
Tabloları kontrol et
python scripts/check_tables.py
Test verisi ekle
python scripts/test_database.py


### API Testleri
Swagger UI: `http://localhost:8000/docs`

## 📊 Veritabanı Şeması

### Assistant
- Chatbot asistanlarının yapılandırması
- Model tipi ve sistem mesajı
- RAG sistem entegrasyonu

### Conversation
- Konuşma oturumları
- Kullanıcı ve oturum takibi
- Mesaj geçmişi yönetimi

### Message
- Kullanıcı ve asistan mesajları
- RAG sonuçları ile ilişki
- Zaman damgalı kayıtlar

### RAGSystem
- RAG sistem yapılandırması
- Ağırlık ve durum yönetimi
- Asistan ilişkileri

### RAGResult
- RAG sorgu sonuçları
- Bağlam ve meta veriler
- Mesaj ilişkileri

## 🤝 Katkıda Bulunma

1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📮 İletişim

Proje Sahibi - [@ahmetmnr](https://github.com/ahmetmnr)

Proje Linki: [https://github.com/ahmetmnr/chatbot_framework](https://github.com/ahmetmnr/chatbot_framework)