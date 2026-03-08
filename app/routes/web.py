from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item
from app.auth import authenticate_user

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

router = APIRouter()


def get_current_user(request: Request):
    return request.session.get("user")


def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        return None
    return user


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    recent = (
        db.query(Item)
        .order_by(Item.created_at.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "items": recent,
    })


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password.",
        })
    request.session["user"] = {"id": user.id, "username": user.username}
    return RedirectResponse("/", status_code=302)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})
