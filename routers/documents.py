from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from core.database import get_db, AsyncSessionLocal
from core.database.models import RAGDocument
from core.schemas.enums import FileType
from core.services.file_upload import FileUploadService
from core.services.document_processing import DocumentProcessor
from api.dependencies import get_current_user
from api.schemas import RAGDocumentResponse
from core.database.crud import create_rag_document

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

@router.post("/upload", response_model=RAGDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Dosya validasyonu
        if not file.filename.lower().endswith(('.pdf', '.docx', '.txt', '.md')):
            raise HTTPException(400, "Desteklenmeyen dosya formatı")
        print(file.filename)
        # 2. Dosyayı geçici klasöre kaydet
        upload_service = FileUploadService()
        upload_data = await upload_service.save_temp_file(file, current_user)
        print("upload_data::", upload_data)
        processor = DocumentProcessor()
        print("upload_data['temp_path']::", upload_data["temp_path"])
        doc_record = await processor.process_document(upload_data["temp_path"],upload_data["content"], current_user.id)
        print(doc_record)

        document_data = {
            "title": upload_data["original_name"],
            "content": upload_data["content"],
            "file_path": upload_data["temp_path"],
            "file_type": upload_data["file_type"],
            "user_id": current_user.id
        }
        
        new_doc = await create_rag_document(db, document_data)
        return new_doc

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f"Dosya işleme hatası: {str(e)}")

@router.get("/", response_model=List[RAGDocumentResponse])
async def list_user_documents(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    try:
        processor = DocumentProcessor(db)
        docs = await processor.get_user_documents(current_user.id)
        return docs
    except Exception as e:
        raise HTTPException(500, f"Dökümanlar getirilemedi: {str(e)}") 