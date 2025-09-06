from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# import pandas as pd

router = APIRouter(
    prefix='/clusters', tags=["clusters"]
)
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_clusters(request: Request):
    clusters_state = request.app.state.last_clusters

    if not clusters_state or "clusters" not in clusters_state or "stats" not in clusters_state:
        return templates.TemplateResponse(
            "no_data.html",
            {"request": request, "message": "No cluster data available."}, status_code=200
        )
        # raise HTTPException(status_code=404, detail="No cluster data available")

    return templates.TemplateResponse("clusters.html", {"request": request, "clusters": clusters_state["clusters"], "stats": clusters_state["stats"]})

@router.get("/{infection}/{idx}", response_class=HTMLResponse)
def cluster_detail(request: Request, infection: str, idx: int):
    clusters_state = request.app.state.last_clusters

    if not clusters_state or "clusters" not in clusters_state or "stats" not in clusters_state:
        raise HTTPException(status_code=404, detail="No cluster data available")
    
    groups = clusters_state["clusters"].get(infection)
    # infection not found or no clusters for this infection
    if not groups:
        raise HTTPException(status_code=404, detail=f"Infection {infection} not found.")
    
    # index bounds check
    if idx < 0 or idx >= len(groups):
        raise HTTPException(status_code=404, detail=f"Cluster index {idx} out of range.")

    cluster = clusters_state.get("clusters", {}).get(infection, [])[idx]
    return templates.TemplateResponse("detail.html", {"request": request, "infection": infection, "members": cluster})

