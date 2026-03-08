from pathlib import Path
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Item, Tag, Summary

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

router = APIRouter()


@router.get("/search", response_class=HTMLResponse)
def search(
    request: Request,
    q: str = Query(default=""),
    tag: str = Query(default=""),
    source_type: str = Query(default=""),
    db: Session = Depends(get_db),
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=302)

    query = db.query(Item)

    if q:
        pattern = f"%{q}%"
        query = query.outerjoin(Item.summary).filter(
            or_(
                Item.title.ilike(pattern),
                Item.extracted_text.ilike(pattern),
                Item.source_url.ilike(pattern),
                Summary.claim.ilike(pattern),
                Summary.detailed_explanation.ilike(pattern),
            )
        )

    if tag:
        query = query.join(Item.tags).filter(Tag.name == tag.lower())

    if source_type:
        query = query.filter(Item.source_type == source_type)

    results = query.order_by(Item.created_at.desc()).limit(50).all()

    # Get all tags for filter sidebar
    all_tags = db.query(Tag).order_by(Tag.name).all()

    return templates.TemplateResponse("search.html", {
        "request": request,
        "user": user,
        "results": results,
        "query": q,
        "selected_tag": tag,
        "selected_type": source_type,
        "all_tags": all_tags,
    })
