import hashlib
from fastapi import UploadFile, HTTPException
from pathlib import Path
import uuid
from typing import Optional
from config.logger import app_logger
from core.schemas.enums import FileType
from PyPDF2 import PdfReader
from docx import Document
import io

class FileUploadService:
    def __init__(self):
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        self.processed_dir = Path("processed_documents")
        self.processed_dir.mkdir(exist_ok=True)

    async def read_file_content(self, content: bytes, file_extension: str) -> str:
        """Dosya içeriğini okur ve metin olarak döndürür."""
        try:
            if file_extension == '.pdf':
                pdf = PdfReader(io.BytesIO(content))
                return "\n".join(page.extract_text() for page in pdf.pages)
                
            elif file_extension == '.docx':
                doc = Document(io.BytesIO(content))
                return "\n".join(paragraph.text for paragraph in doc.paragraphs)
                
            elif file_extension in ['.txt', '.md']:
                return content.decode('utf-8')
                
            return ""  # Desteklenmeyen dosya tipi için boş string
            
        except Exception as e:
            app_logger.error(f"Dosya içeriği okuma hatası: {str(e)}")
            return ""

    async def save_temp_file(self, file: UploadFile, current_user=None) -> dict:
        try:
            # 1. Dosya validasyonu
            if not file.filename:
                raise HTTPException(400, "Geçersiz dosya adı")
                
            file_extension = Path(file.filename).suffix.lower()
            allowed_extensions = {'.pdf', '.docx', '.txt', '.md'}
            if file_extension not in allowed_extensions:
                raise HTTPException(400, "Desteklenmeyen dosya formatı")

            # 2. Dosya boyutu kontrolü (max 20MB)
            max_size = 20 * 1024 * 1024  # 20MB
            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(413, "Dosya boyutu 20MB'ı aşıyor")

            # 3. Checksum hesapla ve tekrarı kontrol et
            checksum = hashlib.sha256(content).hexdigest()
            existing = await self.check_existing_file(checksum)
            if existing:
                return existing

            # 4. Dosya içeriğini oku
            file_content_str = await self.read_file_content(content, file_extension)
            if not file_content_str:
                app_logger.warning(f"Boş içerik: {file.filename}")
                file_content_str = ""  # NULL yerine boş string

            # 5. Geçici dosyayı kaydet
            file_id = f"{uuid.uuid4()}{file_extension}"
            temp_path = self.temp_dir / file_id
            
            with open(temp_path, "wb") as f:
                f.write(content)
                
            # Dosya tipini belirleme
            file_type_map = {
                '.pdf': FileType.pdf,
                '.docx': FileType.docx,
                '.txt': FileType.txt,
                '.md': FileType.md
            }
            file_type = file_type_map.get(file_extension, FileType.unknown)
            
            return {
                "file_id": file_id,
                "original_name": file.filename,
                "size": len(content),
                "checksum": checksum,
                "temp_path": str(temp_path),
                "content_type": file.content_type,
                "file_type": file_type,
                "content": file_content_str  # Mutlaka string gönder
            }
            
        except HTTPException as he:
            app_logger.error(
                "Dosya yükleme hatası (Kullanıcı: %s): %s", 
                current_user.id if current_user else "anon", 
                str(he.detail)
            )
            raise he
        except Exception as e:
            app_logger.exception("Beklenmeyen yükleme hatası")
            raise HTTPException(500, "Dosya işlenemedi")

    async def move_to_processed(self, temp_path: str) -> str:
        processed_path = self.processed_dir / Path(temp_path).name
        Path(temp_path).rename(processed_path)
        return str(processed_path)

    async def check_existing_file(self, checksum: str) -> Optional[dict]:
        # Veritabanında checksum kontrolü yap
        # Örnek implementasyon:
        # from core.database import get_db
        # async with get_db() as db:
        #     existing = await db.execute(select(RAGDocument).filter_by(file_checksum=checksum))
        #     if existing: return existing.first()
        return None 