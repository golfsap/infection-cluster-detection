from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.upload_service import save_uploaded_files
from app.services.cluster_service import detect_clusters

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/ingest")
async def ingest(
    request: Request,
    transfers_file: UploadFile = File(...),
    microbiology_file: UploadFile = File(...)
): 
    try:
        t_path, m_path = save_uploaded_files(transfers_file, microbiology_file)
        clusters = detect_clusters(t_path, m_path)
        print(clusters)
        # save into FastAPI state
        request.app.state.last_clusters = clusters

        return RedirectResponse("/clusters", status_code=303)
       

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")