import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.services.summarizer import process_item

router = APIRouter(prefix="/submit")


def require_login(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/link")
async def submit_link(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_login(request)
    item = await process_item(
        db=db,
        user_id=user["id"],
        source_type="link",
        source_url=url,
        background_tasks=background_tasks,
    )
    return RedirectResponse(f"/item/{item.id}", status_code=302)


@router.post("/file")
async def submit_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = require_login(request)

    suffix = Path(file.filename).suffix.lower()
    if suffix in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"):
        source_type = "screenshot"
    elif suffix == ".pdf":
        source_type = "pdf"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{suffix}"
    file_path = upload_dir / filename

    with file_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    item = await process_item(
        db=db,
        user_id=user["id"],
        source_type=source_type,
        file_path=str(file_path),
        original_filename=file.filename,
        background_tasks=background_tasks,
    )
    return RedirectResponse(f"/item/{item.id}", status_code=302)


@router.post("/text")
async def submit_text(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    user = require_login(request)
    item = await process_item(
        db=db,
        user_id=user["id"],
        source_type="text",
        raw_text=content,
        title=title,
        background_tasks=background_tasks,
    )
    return RedirectResponse(f"/item/{item.id}", status_code=302)
