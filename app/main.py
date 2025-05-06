# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api.v1.router import api_router

app = FastAPI(
    title="SeaTunnel Job API",
    description="API for creating and managing SeaTunnel jobs",
    version="1.0.0",
    docs_url="/swagger",
    openapi_url="/openapi.json",
    redoc_url=None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider specifying allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="SeaTunnel Job API",
        version="1.0.0",
        description="API for creating and managing SeaTunnel jobs",
        routes=app.routes,
    )
    
    # Add custom logo to OpenAPI schema
    openapi_schema["info"]["x-logo"] = {
        "url": "https://your.cdn/logo.png",
        "backgroundColor": "#FFFFFF",
        "altText": "SeaTunnel Logo"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Override default OpenAPI schema
app.openapi = custom_openapi

@app.get("/")
async def root():
    return {"message": "Welcome to SeaTunnel Job API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Corrected module reference
        host="0.0.0.0",
        port=8000,
        reload=True,  # Note: reload=True should be used only in development
    )