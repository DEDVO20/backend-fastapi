"""
Helpers de autorización RBAC.
"""
from functools import wraps
from typing import Callable, Iterable
from fastapi import HTTPException, status


def _extract_role_keys(current_user) -> set[str]:
    keys = set()
    for user_role in getattr(current_user, "roles", []):
        rol = getattr(user_role, "rol", None)
        clave = getattr(rol, "clave", None)
        if clave:
            keys.add(clave)
    return keys


def ensure_roles(current_user, allowed_roles: Iterable[str]) -> None:
    allowed = set(allowed_roles)
    user_roles = _extract_role_keys(current_user)
    if allowed and allowed.isdisjoint(user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para esta operación",
        )


def require_role(allowed_roles: list[str]) -> Callable:
    """
    Decorador para funciones sync/async que reciban `current_user` como kwarg.
    """
    def decorator(func: Callable) -> Callable:
        if callable(getattr(func, "__await__", None)):
            # Fallback defensivo; se usa la detección principal debajo.
            pass

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            ensure_roles(current_user, allowed_roles)
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            ensure_roles(current_user, allowed_roles)
            return func(*args, **kwargs)

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
