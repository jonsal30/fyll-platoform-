from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

# Minimal in-memory storage to preserve current behavior while we refactor.
# Replace with a proper DB adapter (SQLAlchemy or external DB) in a follow-up PR.

_users: Dict[str, Dict[str, Any]] = {}
_idempotency_store: Dict[str, Dict[str, Any]] = {}


def list_users(limit: int = 100):
    return list(_users.values())[:limit]


def get_user(user_id: str):
    return _users.get(user_id)


def create_user(payload: Dict[str, Any], idempotency_key: Optional[str] = None):
    # Idempotency: if idempotency_key present and seen, return stored result
    if idempotency_key:
        if idempotency_key in _idempotency_store:
            return _idempotency_store[idempotency_key]

    user_id = str(uuid4())
    now = datetime.utcnow()
    user = {
        "id": user_id,
        "name": payload["name"],
        "email": payload["email"],
        "picture": payload.get("picture"),
        "created_at": now,
    }
    _users[user_id] = user

    if idempotency_key:
        _idempotency_store[idempotency_key] = user

    return user


def update_user(user_id: str, payload: Dict[str, Any]):
    user = _users.get(user_id)
    if not user:
        return None
    user.update({k: v for k, v in payload.items() if v is not None})
    return user


def delete_user(user_id: str):
    return _users.pop(user_id, None)
