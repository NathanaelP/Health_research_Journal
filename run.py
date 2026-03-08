"""
Entry point. Run with:
    python run.py
or for production on the Pi:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # set to False on the Pi once stable
    )
