from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SpecKit Extension", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "SpecKit Extension API is running!", "docs_url": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)