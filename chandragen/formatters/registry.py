import importlib
import pkgutil
from typing import Any


from chandragen.formatters import __path__
from chandragen.formatters.types import (
    DocumentPreprocessor,
    FormatterRegistry,
    LineFormatter,
    MultilineFormatter,
)

Formatter = type[LineFormatter | DocumentPreprocessor | MultilineFormatter]


def import_builtin_formatters() -> None:
    """Uses importlib to locate and import all formatter modules"""
    for _finder, modname, _ispkg in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{modname}"
        importlib.import_module(full_name)


FORMATTER_REGISTRY: FormatterRegistry = FormatterRegistry()


def register_formatter(registry_dict: dict[str, Any]):
    """decorate that adds a formatter to the registry at import time"""

    def decorator(cls: Formatter):
        instance = cls.create()
        registry_dict[instance.name] = instance
        # Automatically sort by priority after adding
        sort_registry_by_priority(registry_dict)
        return cls

    return decorator


# Decorators for each type
register_line_formatter = register_formatter(FORMATTER_REGISTRY.line)
register_multiline_formatter = register_formatter(FORMATTER_REGISTRY.multiline)
register_preprocessor = register_formatter(FORMATTER_REGISTRY.preprocessor)


def sort_registry_by_priority(registry_dict: dict[str, Any]) -> None:
    """Uses the formatter priority value to sort the registry"""
    # Create a sorted list of tuples from the dictionary items sorted by priority
    sorted_items = sorted(registry_dict.items(), key=lambda item: item[1].priority)

    # Clear the dictionary and reload it in sorted order
    registry_dict.clear()
    registry_dict.update(sorted_items)
