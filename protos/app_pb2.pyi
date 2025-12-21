from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Todo(_message.Message):
    __slots__ = ("id", "title", "completed")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELD_NUMBER: _ClassVar[int]
    id: int
    title: str
    completed: bool
    def __init__(self, id: _Optional[int] = ..., title: _Optional[str] = ..., completed: bool = ...) -> None: ...

class TodoList(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Todo]
    def __init__(self, items: _Optional[_Iterable[_Union[Todo, _Mapping]]] = ...) -> None: ...

class CreatePayload(_message.Message):
    __slots__ = ("title",)
    TITLE_FIELD_NUMBER: _ClassVar[int]
    title: str
    def __init__(self, title: _Optional[str] = ...) -> None: ...

class TogglePayload(_message.Message):
    __slots__ = ("id", "completed")
    ID_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELD_NUMBER: _ClassVar[int]
    id: int
    completed: bool
    def __init__(self, id: _Optional[int] = ..., completed: bool = ...) -> None: ...

class DeletePayload(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class FilterPayload(_message.Message):
    __slots__ = ("filter",)
    FILTER_FIELD_NUMBER: _ClassVar[int]
    filter: str
    def __init__(self, filter: _Optional[str] = ...) -> None: ...

class AppContext(_message.Message):
    __slots__ = ("items", "filter", "next_id")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    NEXT_ID_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Todo]
    filter: str
    next_id: int
    def __init__(self, items: _Optional[_Iterable[_Union[Todo, _Mapping]]] = ..., filter: _Optional[str] = ..., next_id: _Optional[int] = ...) -> None: ...

class MachineState(_message.Message):
    __slots__ = ("state", "context", "version")
    STATE_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    state: str
    context: AppContext
    version: int
    def __init__(self, state: _Optional[str] = ..., context: _Optional[_Union[AppContext, _Mapping]] = ..., version: _Optional[int] = ...) -> None: ...

class MachineEvent(_message.Message):
    __slots__ = ("type", "payload", "client_version")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    CLIENT_VERSION_FIELD_NUMBER: _ClassVar[int]
    type: str
    payload: bytes
    client_version: int
    def __init__(self, type: _Optional[str] = ..., payload: _Optional[bytes] = ..., client_version: _Optional[int] = ...) -> None: ...

class SyncMessage(_message.Message):
    __slots__ = ("snapshot", "event", "update", "error")
    SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    snapshot: MachineState
    event: MachineEvent
    update: MachineState
    error: str
    def __init__(self, snapshot: _Optional[_Union[MachineState, _Mapping]] = ..., event: _Optional[_Union[MachineEvent, _Mapping]] = ..., update: _Optional[_Union[MachineState, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...
