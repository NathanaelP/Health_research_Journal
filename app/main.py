from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.auth import seed_default_user
from app.routes import web, upload, items, search


def create_app() -> FastAPI:
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    # Seed default user on first run
    db = SessionLocal()
    try:
        seed_default_user(db)
    finally:
        db.close()

    # Ensure data directories exist
    for d in [settings.upload_dir, settings.extracted_dir, settings.summaries_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="Health Research Journal", docs_url=None, redoc_url=None)

    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    static_path = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    app.include_router(web.router)
    app.include_router(upload.router)
    app.include_router(items.router)
    app.include_router(search.router)

    return app


app = create_app()
