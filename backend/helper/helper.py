from typing import Any, Dict


def _get_field(item: Any, field: str) -> Any:
    """Get field from dict or Pydantic model"""
    if isinstance(item, dict):
        return item.get(field)
    return getattr(item, field, None)


def _to_raw_item(item: Any) -> Dict[str, Any]:
    """Convert item to dictionary"""
    if hasattr(item, "model_dump") and callable(getattr(item, "model_dump")):
        try:
            return item.model_dump()
        except Exception:
            pass
    if isinstance(item, dict):
        return item
    return {
        "name": _get_field(item, "name"),
        "local_name": _get_field(item, "local_name"),
        "portion_description": _get_field(item, "portion_description"),
        "quantity": _get_field(item, "quantity"),
        "meal_type": str(_get_field(item, "meal_type"))
        if _get_field(item, "meal_type")
        else None,
    }
