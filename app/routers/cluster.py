from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
import pandas as pd

router = APIRouter(
    prefix='/clusters'
)
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def list_clusters(request: Request):
    clusters = request.app.state.last_clusters

    if not clusters or "clusters" not in clusters or "stats" not in clusters:
        raise HTTPException(status_code=404, detail="No cluster data available")

    # Check
    import pprint
    pprint.pprint(clusters)

    return templates.TemplateResponse("clusters.html", {"request": request, "clusters": clusters["clusters"], "stats": clusters["stats"]})

@router.get("/{infection}/{idx}")
def cluster_detail(request: Request, infection: str, idx: int):
    clusters = request.app.state.last_clusters
    # clusters_for = clusters.get("clusters")
    # if (not clusters_for)
    cluster = clusters.get("clusters", {}).get(infection, [])[idx]
    return templates.TemplateResponse("detail.html", {"request": request, "infection": infection, "members": cluster})

