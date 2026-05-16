"""
core/tools/pdf_tool.py — PDF text extraction.
"""
from pathlib import Path
from typing import List, Optional

def extract_pdf_text(file_path: str, pages: Optional[str] = None, max_chars: int = 50000) -> str:
    """
    Extract text from a PDF file.
    'pages' can be a range like '1-5' or a list like '1,3,5'.
    """
    path = Path(file_path)

    if not path.exists():
        return f"Error: File not found: {file_path}"

    if path.suffix.lower() != ".pdf":
        return f"Error: Not a PDF file: {file_path}"

    try:
        import pdfplumber
    except ImportError:
        return "Error: pdfplumber package not installed. Install with: pip install pdfplumber"

    try:
        with pdfplumber.open(str(path)) as pdf:
            total_pages = len(pdf.pages)

            if pages:
                page_indices = _parse_pages(pages, total_pages)
            else:
                page_indices = list(range(total_pages))

            text_parts: List[str] = []
            for idx in page_indices:
                if 0 <= idx < total_pages:
                    page_text = pdf.pages[idx].extract_text() or ""
                    text_parts.append(page_text)

            text = "\n\n".join(text_parts)
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Content truncated]"

            if not text.strip():
                return "No text content found in PDF."

            return f"--- Content of {path.name} ({len(page_indices)} pages) ---\n\n{text}"
    except Exception as exc:
        return f"PDF extraction error: {str(exc)}"

def _parse_pages(pages_str: str, total_pages: int) -> List[int]:
    """Parse a page range string into zero-indexed page numbers."""
    result: List[int] = []
    for part in pages_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = max(1, int(start_str.strip()))
                end = min(total_pages, int(end_str.strip()))
                result.extend(range(start - 1, end))
            except ValueError:
                continue
        else:
            try:
                page_num = int(part)
                if 1 <= page_num <= total_pages:
                    result.append(page_num - 1)
            except ValueError:
                continue
    return sorted(set(result))
