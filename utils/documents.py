from io import BytesIO

from docx import Document
from pypdf import PdfReader


MAX_RESUME_SIZE = 10 * 1024 * 1024
MAX_RESUME_CHARACTERS = 50000


def extract_resume_text(filename, file_bytes):
    if len(file_bytes) > MAX_RESUME_SIZE:
        raise ValueError("Resume file must be 10 MB or smaller.")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension == "pdf":
        pages = PdfReader(BytesIO(file_bytes)).pages
        text = "\n".join(page.extract_text() or "" for page in pages)
    elif extension == "docx":
        document = Document(BytesIO(file_bytes))
        parts = [paragraph.text for paragraph in document.paragraphs]
        parts.extend(
            " | ".join(cell.text for cell in row.cells)
            for table in document.tables
            for row in table.rows
        )
        text = "\n".join(parts)
    else:
        raise ValueError("Upload a PDF or DOCX resume.")

    text = text.strip()
    if not text:
        raise ValueError(
            "No readable text was found. For scanned PDFs, upload a text-based "
            "PDF or DOCX version."
        )
    return text[:MAX_RESUME_CHARACTERS]
