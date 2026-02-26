"""
MedDevice DMS - SurrealDB Async Client (Singleton)
"""
import asyncio
from pathlib import Path
from typing import Optional

import structlog
from surrealdb import AsyncSurreal

from config import settings

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------

_client: Optional[AsyncSurreal] = None
_lock = asyncio.Lock()
_MAX_RETRIES = 3
_RETRY_DELAY = 2  # seconds


async def _get_client() -> AsyncSurreal:
    """Return the singleton AsyncSurreal instance, creating it if needed."""
    global _client
    async with _lock:
        if _client is None:
            _client = AsyncSurreal(settings.SURREAL_URL)
        return _client


async def connect() -> AsyncSurreal:
    """Connect (or reconnect) to SurrealDB with retry logic."""
    global _client
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            client = await _get_client()
            await client.signin({"username": settings.SURREAL_USER, "password": settings.SURREAL_PASS})
            await client.use(settings.SURREAL_NS, settings.SURREAL_DB)
            log.info("surrealdb.connected", attempt=attempt)
            return client
        except Exception as exc:
            log.warning("surrealdb.connect_failed", attempt=attempt, error=str(exc))
            _client = None
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_DELAY * attempt)
            else:
                raise ConnectionError(f"Cannot connect to SurrealDB after {_MAX_RETRIES} attempts") from exc


async def disconnect() -> None:
    """Close the SurrealDB connection."""
    global _client
    if _client:
        try:
            await _client.close()
        except Exception:
            pass
        _client = None
        log.info("surrealdb.disconnected")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

async def query(surql: str, params: Optional[dict] = None) -> list:
    """Execute a raw SurrealQL query with auto-reconnect."""
    client = await _get_client()
    try:
        result = await client.query(surql, params or {})
        return result
    except Exception as exc:
        log.error("surrealdb.query_failed", query=surql[:120], error=str(exc))
        # Try reconnect once
        await connect()
        client = await _get_client()
        return await client.query(surql, params or {})


async def create(table: str, data: dict) -> dict:
    """Create a record in the given table."""
    client = await _get_client()
    result = await client.create(table, data)
    # Handle list return or string ID return
    if isinstance(result, list) and result:
        result = result[0]
    
    rec_id = result.get("id") if isinstance(result, dict) else str(result)
    log.info("surrealdb.created", table=table, id=rec_id)
    return result if isinstance(result, dict) else {"id": result}


async def update(record_id: str, data: dict) -> dict:
    """Update an existing record by its full ID (e.g. 'device:abc123')."""
    client = await _get_client()
    result = await client.merge(record_id, data)
    if isinstance(result, list) and result:
        result = result[0]
    log.info("surrealdb.updated", record_id=record_id)
    return result if isinstance(result, dict) else {"id": result}


async def delete(record_id: str) -> None:
    """Delete a record by its full ID."""
    client = await _get_client()
    await client.delete(record_id)
    log.info("surrealdb.deleted", record_id=record_id)


# ---------------------------------------------------------------------------
# Audit logging (bắt buộc cho phần mềm y tế)
# ---------------------------------------------------------------------------

async def create_audit_log(
    action: str,
    table_name: str,
    record_id: str,
    telegram_user_id: Optional[str] = None,
    changes: Optional[dict] = None,
) -> dict:
    """Write an immutable audit log entry."""
    entry = {
        "action": action,
        "table_name": table_name,
        "record_id": str(record_id),
        "telegram_user_id": telegram_user_id or "system",
        "changes": changes or {},
    }
    result = await create("audit_log", entry)
    log.info("audit.logged", action=action, table=table_name, record=record_id)
    return result


# ---------------------------------------------------------------------------
# Schema loader
# ---------------------------------------------------------------------------

async def apply_schema(schema_path: Optional[str] = None) -> None:
    """Load and execute the schema.surql file against the database."""
    path = Path(schema_path or "db/schema.surql")
    if not path.exists():
        log.warning("schema.not_found", path=str(path))
        return
    surql = path.read_text(encoding="utf-8")
    try:
        await query(surql)
        log.info("schema.applied", path=str(path))
    except Exception as exc:
        log.warning("schema.apply_error", error=str(exc)[:200],
                    msg="Schema may already be applied — continuing")
