from fastapi import Request
from fastapi.responses import Response
from google.protobuf.message import Message
from typing import Any, Type, TypeVar, Callable

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