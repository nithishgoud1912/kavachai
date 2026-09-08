"""
KavachAI — Text Chunking with Overlap
Implements: FR-ING-3 (chunk text into overlapping passages sized for the embedding model)

Chunk size and overlap configured via settings (CHUNK_SIZE=512, CHUNK_OVERLAP=64).
"""

from typing import List, Dict, Any

from app.config import settings


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Chunk extracted pages into overlapping text passages.
    Implements: FR-ING-3

    Args:
        pages: output from extract.extract_text()
        chunk_size: max characters per chunk (default from settings)
        chunk_overlap: overlap between chunks (default from settings)

    Returns:
        List of chunks: [{text, page, chunk_index, source_page_range}]
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.CHUNK_OVERLAP

    chunks = []
    chunk_index = 0

    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]

        # Split into chunks with overlap
        page_chunks = _split_with_overlap(text, chunk_size, chunk_overlap)

        for chunk_text in page_chunks:
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text.strip(),
                    "page": page_num,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

    return chunks


def _split_with_overlap(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into overlapping chunks, preferring to break at sentence/paragraph
    boundaries when possible.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to break at a sentence boundary (. or \n)
            # Look backwards from 'end' for a good break point
            break_point = _find_break_point(text, start, end)
            if break_point > start:
                end = break_point

        chunk = text[start:end]
        chunks.append(chunk)

        # Next chunk starts 'overlap' characters before the end of this one
        start = end - overlap
        if start <= (end - chunk_size):
            # Prevent infinite loop if overlap >= chunk_size
            start = end

    return chunks


def _find_break_point(text: str, start: int, end: int) -> int:
    """Find the best break point near 'end', preferring sentence endings."""
    # Search backwards from end for sentence-ending punctuation
    search_start = max(start, end - 100)  # Look back up to 100 chars

    # Priority: paragraph break > period+space > newline > any space
    for marker in ["\n\n", ". ", ".\n", "\n", " "]:
        pos = text.rfind(marker, search_start, end)
        if pos > start:
            return pos + len(marker)

    return end  # No good break point found; hard break
