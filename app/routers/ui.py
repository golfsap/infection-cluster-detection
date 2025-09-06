from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.upload_service import save_uploaded_files

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/upload", response_class=HTMLResponse)
async def upload_ui_files(
    request: Request,
    transfers_file: UploadFile = File(...),
    microbiology_file: UploadFile = File(...)
):
    try:
        save_uploaded_files(transfers_file, microbiology_file)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": "Files uploaded successfully."
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": f"Upload failed: {str(e)}"
        })