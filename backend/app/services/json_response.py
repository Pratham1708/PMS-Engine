import math
from typing import Any
from fastapi.responses import JSONResponse

def clean_float_values(data: Any) -> Any:
    """
    Recursively replaces out-of-range floats (nan, inf, -inf) with None
    so that they can be safely serialized to standard JSON (null).
    """
    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, dict):
        return {k: clean_float_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_float_values(v) for v in data]
    elif isinstance(data, tuple):
        return tuple(clean_float_values(v) for v in data)
    return data

class SafeJSONResponse(JSONResponse):
    """
    A custom FastAPI/Starlette JSONResponse that cleans out-of-range float
    values (NaN, Infinity, -Infinity) to None (null) before rendering.
    """
    def render(self, content: Any) -> bytes:
        cleaned = clean_float_values(content)
        return super().render(cleaned)
