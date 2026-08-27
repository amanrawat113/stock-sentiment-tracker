from fastapi import APIRouter
from .service import *

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/announcements")
def get_announcements(from_date: str, to_date: str):
    return fetch_announcements(from_date, to_date)