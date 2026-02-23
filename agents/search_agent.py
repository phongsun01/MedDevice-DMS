"""
MedDevice DMS - Search Agent
Full-text search and device lookup using SurrealDB.
"""
import structlog

from db import client as db

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Full-text document search
# ---------------------------------------------------------------------------

async def search_documents(query: str, filters: dict | None = None) -> list[dict]:
    """Search documents with SurrealQL FULLTEXT and optional filters.

    filters keys: category_id, device_group_id, device_id, doc_type
    """
    filters = filters or {}

    where_clauses = ["content_text @1@ $query"]
    params: dict = {"query": query}

    if filters.get("device_id"):
        where_clauses.append("device = $device_id")
        params["device_id"] = filters["device_id"]
    if filters.get("doc_type"):
        where_clauses.append("doc_type = $doc_type")
        params["doc_type"] = filters["doc_type"]

    where_sql = " AND ".join(where_clauses)

    surql = f"""
        SELECT
            *,
            search::highlight('<b>', '</b>', 1) AS highlight_snippet,
            device.name AS device_name,
            device.device_group.name AS group_name,
            device.device_group.category.name AS category_name
        FROM document
        WHERE {where_sql}
        ORDER BY search::score(1) DESC
        LIMIT 10;
    """

    try:
        results = await db.query(surql, params)
        rows = results[0] if results else []
        log.info("search.documents", query=query[:50], count=len(rows))
        return rows
    except Exception as exc:
        log.error("search.documents_failed", error=str(exc))
        return []


# ---------------------------------------------------------------------------
# 2. Device search
# ---------------------------------------------------------------------------

async def search_devices(query: str) -> list[dict]:
    """Search devices by name, model, or brand."""
    surql = """
        SELECT
            *,
            device_group.name AS group_name,
            device_group.category.name AS category_name
        FROM device
        WHERE name ~ $q OR model ~ $q OR brand ~ $q
        LIMIT 20;
    """
    try:
        results = await db.query(surql, {"q": query})
        rows = results[0] if results else []
        log.info("search.devices", query=query, count=len(rows))
        return rows
    except Exception as exc:
        log.error("search.devices_failed", error=str(exc))
        return []


# ---------------------------------------------------------------------------
# 3. Telegram formatting
# ---------------------------------------------------------------------------

def format_search_results_telegram(results: list[dict]) -> str:
    """Format search results as a Telegram-friendly numbered list."""
    if not results:
        return "🔍 Không tìm thấy kết quả nào."

    lines: list[str] = [f"🔍 Tìm thấy {len(results)} kết quả:\n"]
    for i, doc in enumerate(results, 1):
        device_name = doc.get("device_name", "N/A")
        doc_type = doc.get("doc_type", "")
        sub_type = doc.get("sub_type", "")
        snippet = doc.get("highlight_snippet", "")[:120]
        doc_id = doc.get("id", "")

        type_label = f"{doc_type}" + (f" ({sub_type})" if sub_type else "")
        lines.append(f"{i}. <b>{device_name}</b> — {type_label}")
        if snippet:
            lines.append(f"   📄 {snippet}")
        lines.append(f"   ID: <code>{doc_id}</code>\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Device profile
# ---------------------------------------------------------------------------

async def get_device_profile(device_id: str) -> dict:
    """Fetch a device with all its documents grouped by doc_type."""
    dev_result = await db.query(
        """SELECT
            *,
            device_group.name AS group_name,
            device_group.category.name AS category_name
        FROM device WHERE id = $id""",
        {"id": device_id},
    )

    if not dev_result or not dev_result[0]:
        return {}

    device = dev_result[0][0] if isinstance(dev_result[0], list) else dev_result[0]

    docs_result = await db.query(
        "SELECT * FROM document WHERE device = $id ORDER BY doc_type, uploaded_at DESC",
        {"id": device_id},
    )
    docs = docs_result[0] if docs_result and docs_result[0] else []

    # Group by doc_type
    grouped: dict[str, list] = {}
    for doc in docs:
        dt = doc.get("doc_type", "other")
        grouped.setdefault(dt, []).append(doc)

    device["documents"] = grouped
    device["total_docs"] = len(docs)
    return device
