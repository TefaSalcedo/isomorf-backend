from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, catalog, documents, elements, folders, loads, projects, teams
from app.core.config import settings

app = FastAPI(title='ISOMORF API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(elements.router)
app.include_router(folders.router)
app.include_router(loads.router)
app.include_router(documents.router)
app.include_router(teams.router)
app.include_router(catalog.presets_router)
app.include_router(catalog.materials_router)
app.include_router(catalog.sections_router)


@app.get('/health', tags=['health'])
def health() -> dict[str, str]:
    return {'status': 'ok'}
