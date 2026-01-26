from pypdf import PdfReader
from io import BytesIO
from fastapi import HTTPException


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts text from a PDF file given its raw bytes.
    Raises HTTPException if extraction fails or produces no text.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF file: {e}")

    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    final_text = "\n".join(pages_text).strip()

    if not final_text:
        raise HTTPException(
            status_code=400,
            detail="PDF uploaded but no text could be extracted."
        )

    return final_text
