import json
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, Note, Tag
from app.services.summarizer import regenerate_summary

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

router = APIRouter(prefix="/item")


def require_login(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user


@router.get("/{item_id}", response_class=HTMLResponse)
def item_detail(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    bullets = []
    if item.summary and item.summary.bullet_summary:
        try:
            bullets = json.loads(item.summary.bullet_summary)
        except (json.JSONDecodeError, TypeError):
            bullets = [item.summary.bullet_summary]

    return templates.TemplateResponse("item_detail.html", {
        "request": request,
        "user": user,
        "item": item,
        "bullets": bullets,
    })


@router.post("/{item_id}/note")
def add_note(
    item_id: int,
    request: Request,
    note_text: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    note = Note(item_id=item_id, user_id=user["id"], note_text=note_text)
    db.add(note)
    db.commit()
    return RedirectResponse(f"/item/{item_id}", status_code=302)


@router.post("/{item_id}/tag")
def add_tag(
    item_id: int,
    request: Request,
    tag_name: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    tag_name = tag_name.strip().lower()
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()

    if tag not in item.tags:
        item.tags.append(tag)
    db.commit()
    return RedirectResponse(f"/item/{item_id}", status_code=302)


@router.post("/{item_id}/reprocess")
def reprocess_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    regenerate_summary(db, item)
    return RedirectResponse(f"/item/{item_id}", status_code=302)


@router.post("/{item_id}/delete")
def delete_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return RedirectResponse("/", status_code=302)
