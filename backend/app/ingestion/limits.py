"""Bound uploads and compressed containers before expensive extraction."""
import io
import zipfile
from fastapi import HTTPException
from app.config import settings


async def read_upload(file):
    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Upload exceeds configured size limit")
    if not data:
        raise HTTPException(422, "Empty file")
    validate_container(data, file.filename or '')
    return data


def validate_container(data, filename):
    if filename.lower().endswith(('.docx', '.xlsx', '.pptx')):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(i.file_size for i in archive.infolist()) > settings.MAX_EXTRACTED_BYTES:
                raise HTTPException(413, "Expanded document exceeds configured size limit")
    if filename.lower().endswith('.pdf'):
        import pymupdf
        with pymupdf.open(stream=data, filetype='pdf') as document:
            if len(document) > settings.MAX_DOCUMENT_PAGES:
                raise HTTPException(413, "PDF exceeds configured page limit")
