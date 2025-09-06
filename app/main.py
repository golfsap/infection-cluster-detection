from fastapi import FastAPI
from app.routers import index,cluster
from app.services.persistence import load_clusters

app = FastAPI(title="Infection Clustor Detector")

app.state.last_clusters = {}

@app.on_event("startup")
def load_last():
    app.state.last_clusters = load_clusters()

app.include_router(index.router)
app.include_router(cluster.router)

