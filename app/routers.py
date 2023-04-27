from fastapi import APIRouter,Depends
from app.dependencies.load import load
from app.dependencies.generation import generation
router = APIRouter()

@router.get("/api/presify-onenet-anomaly/load")
async def load(data: dict = Depends(load)):
    return data
@router.get("/api/presify-onenet-anomaly/generation")
async def generation(data: dict = Depends(generation)):
    return data

