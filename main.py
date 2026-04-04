from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.db.database import init_db
from src.routes import auth, users, records, dashboard

app = FastAPI(title="Finance Backend API", version="1.0.0")

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()

# Routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

# Global error handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
