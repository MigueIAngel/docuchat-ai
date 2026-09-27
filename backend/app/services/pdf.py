from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class InvalidDocumentError(ValueError):
    pass


def extract_pages(data: bytes) -> list[str]:
    """Return the text of each page. Raises InvalidDocumentError for unreadable files."""
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise InvalidDocumentError("Encrypted PDFs are not supported")
        pages = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as error:
        raise InvalidDocumentError("The file is not a valid PDF") from error
    if not any(page.strip() for page in pages):
        raise InvalidDocumentError("No text found (scanned PDFs need OCR)")
    return pages
