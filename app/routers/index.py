from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.services.upload_service import save_uploaded_files
from app.services.cluster_service import detect_clusters
from app.services.persistence import save_clusters, load_clusters

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

SAMPLE_PATH = Path("sample_data")

@router.get("/", response_class=HTMLResponse)
def index(request: Request, use_sample: bool = False):
    clusters = None
    stats = None
    if use_sample:
        t_path = SAMPLE_PATH / "transfers.csv"
        m_path = SAMPLE_PATH / "microbiology.csv"
        clusters = detect_clusters(t_path, m_path)
        request.app.state.last_clusters = clusters
        save_clusters(clusters)
        return RedirectResponse("/clusters", status_code=303)
    
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
        request.app.state.last_clusters = clusters
        save_clusters(clusters)

        return RedirectResponse("/clusters", status_code=303)
       
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")