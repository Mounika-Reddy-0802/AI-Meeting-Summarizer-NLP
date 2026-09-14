"""GET /search across the current user's meetings."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import SearchHit
from app.services import search as search_service

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchHit])
def search(
    q: str = Query(min_length=1, max_length=200),
    k: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SearchHit]:
    """Top-k transcript segments matching the query."""
    return search_service.search(db, user.id, q, k)
