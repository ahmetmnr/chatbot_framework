from enum import Enum

class ProcessingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class FileType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    md = "md"
    unknown = "unknown" 