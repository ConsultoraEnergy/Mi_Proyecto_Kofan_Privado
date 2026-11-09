from bson import ObjectId
from bson.errors import InvalidId

from backend.app.core.errors import NotFound


def parse_object_id(value: str | ObjectId | None) -> ObjectId | None:
    """ObjectId válido o None (nunca lanza): un id mal formado se trata como 'no existe'."""
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def require_object_id(value: str | ObjectId | None, entity: str = "Recurso") -> ObjectId:
    oid = parse_object_id(value)
    if oid is None:
        raise NotFound(f"{entity} no encontrado.")
    return oid


def clamp_limit(limit: int, maximum: int = 100) -> int:
    """8.6: el cliente no puede pedir páginas arbitrariamente grandes."""
    return max(1, min(int(limit), maximum))


def page_params(page: int, limit: int, maximum: int = 100) -> tuple[int, int]:
    limit = clamp_limit(limit, maximum)
    page = max(1, int(page))
    return (page - 1) * limit, limit
