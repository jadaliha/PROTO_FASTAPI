from fastapi import Request
from fastapi.responses import Response
from google.protobuf.message import Message
from typing import Any, Type, TypeVar, Callable, Union
from functools import wraps
import asyncio
import inspect

T = TypeVar('T', bound=Message)

class ProtobufResponse(Response):
    """Custom FastAPI response class for Protobuf messages"""
    media_type = "application/x-protobuf"
    
    def render(self, content: Any) -> bytes:
        """Serialize protobuf message to bytes"""
        if isinstance(content, Message):
            return content.SerializeToString()
        elif isinstance(content, bytes):
            return content
        else:
            raise ValueError(f"Content must be a protobuf Message or bytes, got {type(content)}")


class ProtobufBody:
    """Dependency for FastAPI to automatically parse protobuf bodies."""
    def __init__(self, message_type: Type[T]):
        self.message_type = message_type

    async def __call__(self, request: Request) -> T:
        body = await request.body()
        msg = self.message_type()
        msg.ParseFromString(body)
        return msg


class ProtobufRouter:
    """ Wrapper for FastAPI/APIRouter to handle Protobuf serialization automatically """
    def __init__(self, app_or_router: Any):
        self.router = app_or_router

    def _wrap_endpoint(self, func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                if isinstance(result, Message):
                    return ProtobufResponse(result)
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                if isinstance(result, Message):
                    return ProtobufResponse(result)
                return result
            return sync_wrapper

    def _make_method(self, name: str):
        def method(path: str, **kwargs):
            kwargs.setdefault("response_class", ProtobufResponse)
            def decorator(func: Callable):
                wrapped = self._wrap_endpoint(func)
                # Register the wrapped function with the original router method
                getattr(self.router, name)(path, **kwargs)(wrapped)
                return func # Return original for potential reuse or testing
            return decorator
        return method

    def __getattr__(self, name: str):
        if name in ("get", "post", "put", "delete", "patch"):
            return self._make_method(name)
        return getattr(self.router, name)