from __future__ import annotations

import json
from dataclasses import is_dataclass, asdict
from typing import Any, Callable, Dict


class _UnsetType:
    pass


UNSET = _UnsetType()


class FieldInfo:
    def __init__(self, default: Any = UNSET, default_factory: Callable[[], Any] | None = None, **kwargs: Any) -> None:
        self.default = default
        self.default_factory = default_factory
        self.metadata = kwargs


def Field(*, default: Any = UNSET, default_factory: Callable[[], Any] | None = None, **kwargs: Any) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory, **kwargs)


class BaseModelMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: Dict[str, Any]) -> type:
        annotations = namespace.get("__annotations__", {})
        field_defaults: Dict[str, FieldInfo | Any] = {}
        for key in list(annotations.keys()):
            if key in namespace:
                value = namespace[key]
                if isinstance(value, FieldInfo):
                    field_defaults[key] = value
                    namespace.pop(key)
                else:
                    field_defaults[key] = value
        namespace.setdefault("_field_defaults", {})
        namespace["_field_defaults"] = {**namespace["_field_defaults"], **field_defaults}
        return super().__new__(mcls, name, bases, namespace)


class BaseModel(metaclass=BaseModelMeta):
    __annotations__: Dict[str, Any] = {}
    _field_defaults: Dict[str, FieldInfo | Any]

    def __init__(self, **data: Any) -> None:
        fields: Dict[str, FieldInfo | Any] = {}
        for cls in reversed(self.__class__.__mro__):
            annotations = getattr(cls, "__annotations__", {})
            defaults = getattr(cls, "_field_defaults", {})
            for name in annotations:
                if name not in fields:
                    fields[name] = defaults.get(name, UNSET)
        self.__fields__ = list(fields.keys())
        for name, default in fields.items():
            if name in data:
                value = data[name]
            elif isinstance(default, FieldInfo):
                if default.default_factory is not None:
                    value = default.default_factory()
                elif default.default is not UNSET:
                    value = default.default
                else:
                    value = None
            elif default is not UNSET:
                value = default
            else:
                value = None
            setattr(self, name, value)
        for extra_key, extra_value in data.items():
            if extra_key not in fields:
                setattr(self, extra_key, extra_value)

    def dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name in getattr(self, "__fields__", []):
            value = getattr(self, name, None)
            if is_dataclass(value):
                result[name] = asdict(value)
            elif isinstance(value, BaseModel):
                result[name] = value.dict()
            elif isinstance(value, list):
                result[name] = [item.dict() if isinstance(item, BaseModel) else item for item in value]
            else:
                result[name] = value
        return result

    def json(self, *, indent: int | None = None, ensure_ascii: bool = True) -> str:
        return json.dumps(self.dict(), indent=indent, ensure_ascii=ensure_ascii)

    def __iter__(self):
        for key in getattr(self, "__fields__", []):
            yield key, getattr(self, key, None)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        fields = ", ".join(f"{key}={getattr(self, key, None)!r}" for key in getattr(self, "__fields__", []))
        return f"{self.__class__.__name__}({fields})"
