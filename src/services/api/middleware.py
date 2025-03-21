import json
from fasthtml.common import RedirectResponse
from functools import wraps
from fastapi import Request
from typing import Optional
import logging
from fasthtml.common import Redirect
from src.services.api.types import ErrorResponse

logger = logging.getLogger("wilab_app")

def login_required(route_handler):
    @wraps(route_handler)
    async def wrapper(request, *args, **kwargs):
        if isinstance(request, dict):
            session = request
        else:
            session = request.session

        if "user" not in session:
            return RedirectResponse("/login", status_code=303)

        response = await route_handler(request, *args, **kwargs)
        response_str = str(response)

        if "UNAUTHORIZED" in response_str:
            message = "Your session expired, please login again."
            return Redirect(f"/api/logout?message={message}")

        return response
    return wrapper
