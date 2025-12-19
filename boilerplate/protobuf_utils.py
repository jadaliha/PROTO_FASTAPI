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


async def parse_protobuf_body(request: Request, message_type: Type[T]) -> T:
    """
    Parse protobuf from request body.
    
    Usage:
        async def create_todo(request: Request):
            req = await parse_protobuf_body(request, CreateTodoRequest)
            # Use req.title, etc.
    """
    body = await request.body()
    message = message_type()
    message.ParseFromString(body)
    return message


def ProtobufBody(message_type: Type[T]) -> Callable:
    """
    Dependency factory for FastAPI to automatically parse protobuf bodies.
    
    Usage:
        @app.post("/api/todos")
        async def create_todo(req: CreateTodoRequest = ProtobufBody(CreateTodoRequest)):
            # req is already parsed!
            return response
    """
    async def dependency(request: Request) -> T:
        return await parse_protobuf_body(request, message_type)
    return dependency


def protobuf_response(message: Message) -> ProtobufResponse:
    """Helper function to create a ProtobufResponse"""
    return ProtobufResponse(content=message)


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

    @property
    def get(self): return self._make_method("get")
    
    @property
    def post(self): return self._make_method("post")
    
    @property
    def put(self): return self._make_method("put")
    
    @property
    def delete(self): return self._make_method("delete")
    
    @property
    def patch(self): return self._make_method("patch")