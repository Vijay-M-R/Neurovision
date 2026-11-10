import logging
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("neurovision.api")


class NeuroVisionException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class InvalidMRIError(NeuroVisionException):
    def __init__(self, detail: str = "Invalid MRI file"):
        super().__init__(status_code=422, detail=detail)


class FileTooLargeError(NeuroVisionException):
    def __init__(self, detail: str = "File exceeds maximum upload size limit"):
        super().__init__(status_code=413, detail=detail)


class JobNotFoundError(NeuroVisionException):
    def __init__(self, detail: str = "Job ID not found"):
        super().__init__(status_code=404, detail=detail)


class ResourceNotFoundError(NeuroVisionException):
    def __init__(self, detail: str = "Requested resource not found"):
        super().__init__(status_code=404, detail=detail)


class AIServiceUnavailableError(NeuroVisionException):
    def __init__(self, detail: str = "AI engine or model is currently unavailable"):
        super().__init__(status_code=503, detail=detail)


class GPUOutOfMemoryError(NeuroVisionException):
    def __init__(self, detail: str = "GPU memory exhausted during inference"):
        super().__init__(status_code=503, detail=detail)


async def neurovision_exception_handler(request: Request, exc: NeuroVisionException):
    logger.warning("NeuroVisionException on %s: %s (status %d)", request.url.path, exc.detail, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error on %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."}
    )
