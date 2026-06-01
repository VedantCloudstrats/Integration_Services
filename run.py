"""
Entry point — run with: python run.py
Or directly:            uvicorn app.main:app --reload --port 8001
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
