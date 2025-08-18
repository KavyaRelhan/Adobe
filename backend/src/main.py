# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# from pathlib import Path
from .config import UPLOAD_DIR

# Import the router from our new file. This is like importing a chapter of a book.
from .routers import analysis_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Intelligent Document Reader API")

origins = [
    "http://localhost",
    "http://127.0.0.1:5173",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


# # --- ADD THIS MIDDLEWARE FOR CSP ---
# @app.middleware("http")
# async def add_csp_header(request: Request, call_next):
#     """Middleware to add the Content-Security-Policy header."""
#     response = await call_next(request)
    
#     # This policy is a secure starting point for your app + Adobe Viewer
#     csp_policy = (
#         "default-src 'self'; "
#         "script-src 'self' https://documentcloud.adobe.com; "
#         "connect-src 'self' https://acrobatservices.adobe.com; "
#         "frame-src https://documentcloud.adobe.com; "
#         "style-src 'self' 'unsafe-inline'; "
#         "worker-src blob:; "
#         "img-src 'self' data:;"
#     )
    
#     response.headers['Content-Security-Policy'] = csp_policy
#     return response
# # --- END OF NEW MIDDLEWARE ---


UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(analysis_router.router)

@app.get("/", tags=["Health Check"])
def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the Intelligent Document Reader API!"}