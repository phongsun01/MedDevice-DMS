"""
MedDevice DMS - Wiki Agent
Outline.dev integration for auto-generating device wiki pages.
"""
import aiohttp
import structlog

from config import settings
from db import client as db
from agents.search_agent import get_device_profile

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Outline REST API Client
# ---------------------------------------------------------------------------

class OutlineClient:
    """Async client for Outline.dev REST API."""

    def __init__(self, api_url: str | None = None, api_token: str | None = None):
        self.api_url = (api_url or settings.OUTLINE_API_URL).rstrip("/")
        self.api_token = api_token or settings.OUTLINE_API_TOKEN
        self._headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def _post(self, endpoint: str, data: dict) -> dict:
        url = f"{self.api_url}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=self._headers) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    log.error("outline.api_error", status=resp.status, body=body[:200])
                    return {}
                return await resp.json()

    async def create_document(
        self, title: str, content: str, collection_id: str, parent_id: str | None = None
    ) -> str:
        """Create a new Outline document. Returns document ID."""
        payload = {
            "title": title,
            "text": content,
            "collectionId": collection_id,
            "publish": True,
        }
        if parent_id:
            payload["parentDocumentId"] = parent_id

        result = await self._post("/documents.create", payload)
        doc_id = result.get("data", {}).get("id", "")
        log.info("outline.doc_created", title=title, id=doc_id)
        return doc_id

    async def update_document(self, doc_id: str, title: str, content: str) -> bool:
        """Update an existing Outline document."""
        result = await self._post("/documents.update", {
            "id": doc_id,
            "title": title,
            "text": content,
        })
        success = bool(result.get("data"))
        log.info("outline.doc_updated", id=doc_id, success=success)
        return success

    async def find_document_by_title(self, title: str) -> str | None:
        """Search for a document by exact title. Returns document ID or None."""
        result = await self._post("/documents.search", {"query": title})
        docs = result.get("data", [])
        for doc in docs:
            doc_title = doc.get("document", {}).get("title") or ""
            if doc_title.strip() == title.strip():
                return doc["document"]["id"]
        return None

    async def get_or_create_collection(self, name: str) -> str:
        """Find an existing collection by name, or create a new one."""
        # List collections
        result = await self._post("/collections.list", {})
        collections = result.get("data", [])
        for col in collections:
            if col.get("name", "").strip() == name.strip():
                return col["id"]

        # Create new
        result = await self._post("/collections.create", {"name": name})
        col_id = result.get("data", {}).get("id", "")
        log.info("outline.collection_created", name=name, id=col_id)
        return col_id


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

_DOC_TYPE_ICONS = {
    "technical": "📋",
    "config": "⚙️",
    "price": "💰",
    "contract": "📝",
    "comparison": "📊",
    "link": "🔗",
    "other": "📎",
}


def generate_device_page_markdown(device: dict, documents: dict[str, list]) -> str:
    """Generate a professional Markdown page for a device."""
    cat = device.get("category_name", "N/A")
    grp = device.get("group_name", "N/A")
    name = device.get("name", "Unknown")

    lines = [
        f"# {name}",
        f"*{cat} > {grp}*\n",
        "## Thông tin chung\n",
        "| Thuộc tính | Giá trị |",
        "|---|---|",
        f"| Model | {device.get('model', '—')} |",
        f"| Hãng | {device.get('brand', '—')} |",
        f"| Xuất xứ | {device.get('origin', '—')} |",
        f"| Năm SX | {device.get('year', '—')} |",
        "",
    ]

    for doc_type, docs in documents.items():
        icon = _DOC_TYPE_ICONS.get(doc_type, "📄")
        lines.append(f"## {icon} {doc_type.capitalize()}\n")
        for doc in docs:
            title = doc.get("metadata", {}).get("title", doc.get("file_path", "N/A"))
            sub = f" ({doc.get('sub_type')})" if doc.get("sub_type") else ""
            lines.append(f"- {title}{sub}")
        lines.append("")

    if device.get("notes"):
        lines.append(f"## 📌 Ghi chú\n{device['notes']}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Update / create device page
# ---------------------------------------------------------------------------

_outline_client: OutlineClient | None = None


def _get_client() -> OutlineClient:
    global _outline_client
    if _outline_client is None:
        _outline_client = OutlineClient()
    return _outline_client


async def update_device_page(device_id: str, telegram_user_id: str | None = None) -> None:
    """Fetch device profile → generate markdown → push to Outline."""
    profile = await get_device_profile(device_id)
    if not profile:
        log.warning("wiki.device_not_found", device_id=device_id)
        return

    documents = profile.get("documents", {})
    md = generate_device_page_markdown(profile, documents)

    client = _get_client()
    title = str(profile.get("name") or profile.get("display_name") or device_id)
    cat_name = str(profile.get("category_name") or "General")

    collection_id = await client.get_or_create_collection(cat_name)
    existing_id = await client.find_document_by_title(title)

    if existing_id:
        await client.update_document(existing_id, title, md)
    else:
        await client.create_document(title, md, collection_id)

    # Audit
    await db.create_audit_log("wiki_update", "device", str(device_id), telegram_user_id)
    log.info("wiki.page_updated", device=title)


async def generate_index_page(category_id: str | None = None) -> None:
    """Generate / update the master index page for all devices."""
    if category_id:
        surql = """SELECT
                    *,
                    device_group.name AS group_name,
                    device_group.category.name AS category_name
                FROM device WHERE device_group.category = $cat
                ORDER BY device_group.name, name"""
        results = await db.query(surql, {"cat": category_id})
    else:
        surql = """SELECT
                    *,
                    device_group.name AS group_name,
                    device_group.category.name AS category_name
                FROM device ORDER BY device_group.category.name, device_group.name, name"""
        results = await db.query(surql)

    devices = results if results else []

    # Group by category → device_group
    tree: dict[str, dict[str, list]] = {}
    for dev in devices:
        cat = dev.get("category_name", "General")
        grp = dev.get("group_name", "Other")
        tree.setdefault(cat, {}).setdefault(grp, []).append(dev)

    # Build index markdown
    lines = ["# 📚 MedDevice DMS — Danh mục thiết bị\n"]
    for cat, groups in tree.items():
        lines.append(f"## {cat}\n")
        for grp, devs in groups.items():
            lines.append(f"### {grp}\n")
            for dev in devs:
                lines.append(f"- **{dev.get('name', '?')}** — {dev.get('model', '')} ({dev.get('brand', '')})")
            lines.append("")

    md = "\n".join(lines)
    client = _get_client()
    collection_id = await client.get_or_create_collection("MedDevice Index")
    existing = await client.find_document_by_title("Danh mục thiết bị")

    if existing:
        await client.update_document(existing, "Danh mục thiết bị", md)
    else:
        await client.create_document("Danh mục thiết bị", md, collection_id)

    log.info("wiki.index_updated", device_count=len(devices))
