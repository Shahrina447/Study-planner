from fastapi import APIRouter, File, UploadFile

from services.document_service import document_service


router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    return await document_service.upload_document(file)


@router.get("/documents")
async def list_documents():
    return await document_service.list_documents()


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    return await document_service.delete_document(filename)
