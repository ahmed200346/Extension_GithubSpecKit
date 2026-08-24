from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure consistent API responses.
    """
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal server error occurred.",
            "detail": str(exc)
        }
    )

def api_response(data=None, message="Success", status_code=200):
    """
    Standard API response wrapper.
    """
    return {
        "status": "success" if status_code < 400 else "error",
        "message": message,
        "data": data
    }
