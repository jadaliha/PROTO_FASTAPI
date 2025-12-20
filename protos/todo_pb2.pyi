from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CREATED: _ClassVar[EventType]
    UPDATED: _ClassVar[EventType]
    DELETED: _ClassVar[EventType]
CREATED: EventType
UPDATED: EventType
DELETED: EventType

class Todo(_message.Message):
    __slots__ = ("id", "title", "completed", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: int
    title: str
    completed: bool
    created_at: int
    def __init__(self, id: _Optional[int] = ..., title: _Optional[str] = ..., completed: bool = ..., created_at: _Optional[int] = ...) -> None: ...

class TodoList(_message.Message):
    __slots__ = ("todos",)
    TODOS_FIELD_NUMBER: _ClassVar[int]
    todos: _containers.RepeatedCompositeFieldContainer[Todo]
    def __init__(self, todos: _Optional[_Iterable[_Union[Todo, _Mapping]]] = ...) -> None: ...

class CreateTodoRequest(_message.Message):
    __slots__ = ("title",)
    TITLE_FIELD_NUMBER: _ClassVar[int]
    title: str
    def __init__(self, title: _Optional[str] = ...) -> None: ...

class UpdateTodoRequest(_message.Message):
    __slots__ = ("id", "completed")
    ID_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELD_NUMBER: _ClassVar[int]
    id: int
    completed: bool
    def __init__(self, id: _Optional[int] = ..., completed: bool = ...) -> None: ...

class DeleteTodoRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class TodoStats(_message.Message):
    __slots__ = ("total", "active", "completed")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_FIELD_NUMBER: _ClassVar[int]
    total: int
    active: int
    completed: int
    def __init__(self, total: _Optional[int] = ..., active: _Optional[int] = ..., completed: _Optional[int] = ...) -> None: ...

class ApiResponse(_message.Message):
    __slots__ = ("success", "message", "todo", "todo_list", "stats")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TODO_FIELD_NUMBER: _ClassVar[int]
    TODO_LIST_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    todo: Todo
    todo_list: TodoList
    stats: TodoStats
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., todo: _Optional[_Union[Todo, _Mapping]] = ..., todo_list: _Optional[_Union[TodoList, _Mapping]] = ..., stats: _Optional[_Union[TodoStats, _Mapping]] = ...) -> None: ...

class TodoEvent(_message.Message):
    __slots__ = ("type", "todo", "deleted_id", "stats")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TODO_FIELD_NUMBER: _ClassVar[int]
    DELETED_ID_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    type: EventType
    todo: Todo
    deleted_id: int
    stats: TodoStats
    def __init__(self, type: _Optional[_Union[EventType, str]] = ..., todo: _Optional[_Union[Todo, _Mapping]] = ..., deleted_id: _Optional[int] = ..., stats: _Optional[_Union[TodoStats, _Mapping]] = ...) -> None: ...
