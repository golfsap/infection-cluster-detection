from fastapi import FastAPI
from app.routers import index,cluster

app = FastAPI(title="Infection Clustor Detector")

app.state.last_clusters = {}

app.include_router(index.router)
app.include_router(cluster.router)
