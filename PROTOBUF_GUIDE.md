# Protobuf Integration Guide

This guide documents the architecture and implementation of the Protocol Buffers integration in this application.

## Architecture Overview

The application uses an "API-first" approach where the contract between the frontend and backend is defined in a `.proto` file.

1.  **Schema**: `protos/todo.proto` defines the data structures and messages.
2.  **Backend (Python)**: `main.py` uses `protobuf_utils.py` to automatically serialize and deserialize protobuf messages.
3.  **Frontend (JS)**: `static/app.js` uses `protobufjs` to load the schema at runtime and communicate with the backend.

## ProtobufResponse and ProtobufBody Patterns

We've implemented a custom FastAPI serialization layer to make working with protobuf as easy as JSON.

### ProtobufResponse

A custom FastAPI `Response` class that:
- Automatically calls `SerializeToString()` on protobuf messages.
- Sets the `Content-Type` to `application/x-protobuf`.
- Efficiently handles binary data.

### ProtobufBody

A FastAPI dependency factory that:
- Automatically reads the binary request body.
- Parses it into the specified protobuf message type.
- Handled via `Depends(ProtobufBody(MessageType))`.

## Before/After Code Examples

### Without this integration (Standard FastAPI + Protobuf)
```python
@app.post("/api/todos")
async def create_todo(request: Request):
    body = await request.body()
    req = CreateTodoRequest()
    req.ParseFromString(body)
    
    # ... logic ...
    
    res = ApiResponse(success=True)
    return Response(content=res.SerializeToString(), media_type="application/x-protobuf")
```

### With our integration
```python
@app.post("/api/todos", response_class=ProtobufResponse)
async def create_todo(req: CreateTodoRequest = Depends(ProtobufBody(CreateTodoRequest))):
    # req is already a typed CreateTodoRequest object!
    
    # ... logic ...
    
    res = ApiResponse(success=True)
    return ProtobufResponse(res)  # Clean!
```

## Testing Examples

### Using `curl`
To test a protobuf endpoint with `curl`, you need to send binary data.

```bash
# Get todos
curl http://localhost:8080/api/todos

# Create a todo (using python to generate binary request)
python3 -c 'import protos.todo_pb2 as todo_pb; import sys; sys.stdout.buffer.write(todo_pb.CreateTodoRequest(title="Test").SerializeToString())' | \
curl -X POST http://localhost:8080/api/todos \
     -H "Content-Type: application/x-protobuf" \
     --data-binary @-
```

## How to Add New Endpoints

1.  **Define messages** in `protos/todo.proto`.
2.  **Regenerate code**:
    ```bash
    ./setup.sh
    ```
3.  **Implement in `main.py`**:
    ```python
    @app.post("/api/my-new-endpoint", response_class=ProtobufResponse)
    async def my_new_endpoint(req: MyRequest = Depends(ProtobufBody(MyRequest))):
        return ProtobufResponse(MyResponse(success=True))
    ```
4.  **Implement in `app.js`**:
    ```javascript
    const MyRequest = protoRoot.lookupType('todo.MyRequest');
    const request = MyRequest.create({ ... });
    const buffer = MyRequest.encode(request).finish();
    const response = await fetch('/api/my-new-endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-protobuf' },
        body: buffer
    });
    ```
