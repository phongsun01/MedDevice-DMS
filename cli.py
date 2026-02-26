"""
MedDevice DMS — CLI Interface (v2.0)
Usage:
    python cli.py --help
"""
import argparse
import asyncio
import sys
from rich.console import Console

console = Console()

# ─── Commands implementation (Placeholders for now) ──────────────────────────

async def get_db():
    from db import client as db
    await db.connect()
    return db

async def cmd_stats(args):
    console.print("[bold cyan]MedDevice DMS Stats[/bold cyan]")
    try:
        db = await get_db()
        results = await db.query("SELECT count() FROM category GROUP ALL")
        cat_count = results[0]['count'] if isinstance(results, list) and results else 0
        
        results = await db.query("SELECT count() FROM group GROUP ALL")
        group_count = results[0]['count'] if isinstance(results, list) and results else 0

        results = await db.query("SELECT count() FROM device GROUP ALL")
        dev_count = results[0]['count'] if isinstance(results, list) and results else 0

        results = await db.query("SELECT count() FROM document GROUP ALL")
        doc_count = results[0]['count'] if isinstance(results, list) and results else 0

        from rich.table import Table
        table = Table(title="Database Summary", show_header=True, header_style="bold magenta")
        table.add_column("Entity", justify="left")
        table.add_column("Count", justify="right")
        table.add_row("Categories", str(cat_count))
        table.add_row("Groups", str(group_count))
        table.add_row("Devices", str(dev_count))
        table.add_row("Documents", str(doc_count))
        console.print(table)
        
        console.print("- System health: [green]OK[/green]")
        if args.verbose:
             console.print("\n[dim]--verbose flag not fully implemented yet.[/dim]")
    except Exception as e:
        console.print(f"[red]Error fetching stats: {e}[/red]")


async def cmd_scan(args):
    tag = "[DRY-RUN] " if args.dry_run else ""
    console.print(f"[bold yellow]{tag}Scanning storage/files...[/bold yellow]")
    scan_path = args.path if args.path else "storage/files"
    if args.path:
         console.print(f"Path override: {args.path}")
         
    try:
        await get_db()
        from agents.scan_agent import scan_directory
        report = await scan_directory(base_dir=scan_path, dry_run=args.dry_run)
        
        from rich.table import Table
        table = Table(title=f"{tag}Scan Report", show_header=True, header_style="bold magenta")
        table.add_column("Metric", justify="left", style="cyan")
        table.add_column("Value", justify="right", style="green")
        
        table.add_row("Total Files", str(report.get("total_files", 0)))
        table.add_row("Processed", str(report.get("processed", 0)))
        table.add_row("Skipped", str(report.get("skipped", 0)))
        table.add_row("Errors", str(report.get("errors", 0)))
        table.add_row("Unclassified", str(report.get("unclassified", 0)))
        
        console.print(table)
        
        if report.get("details"):
             console.print(f"\n[red]Found {len(report['details'])} issues. Check storage/import_log.jsonl (TODO) for details.[/red]")
        else:
             console.print("\n[green]Scan completed successfully.[/green]")
             
    except Exception as e:
        console.print(f"[red]Error during scan: {e}[/red]")


async def cmd_health(args):
    console.print("[bold cyan]System Health Check[/bold cyan]")
    try:
        db = await get_db()
        console.print("✅ SurrealDB Connection: [green]OK[/green]")
        # Do a test query
        res = await db.query("INFO FOR DB;")
        if res:
             console.print("✅ SurrealDB Ready: [green]OK[/green]")
    except Exception as e:
        console.print(f"❌ SurrealDB Connection: [red]FAILED[/red] ({e})")
        return
    # TODO: Check Wiki Outline connection too

    
async def cmd_search(args):
    console.print(f"Searching for: [bold]'{args.query}'[/bold]...")
    try:
        await get_db()
        from agents.search_agent import search_documents
        results = await search_documents(args.query) # removed limit=10
        
        if args.json:
            import json
            console.print(json.dumps(results, indent=2, ensure_ascii=False))
            return
            
        if not results:
            console.print("No results found.")
            return

        from rich.table import Table
        table = Table(title="Search Results", show_header=True, header_style="bold magenta")
        table.add_column("Device", justify="left", style="cyan", no_wrap=True)
        table.add_column("Type", justify="left", style="green")
        table.add_column("Filename", justify="left")
        
        for raw_doc in results:
            doc = raw_doc[0] if isinstance(raw_doc, list) and len(raw_doc) > 0 else raw_doc
            if not isinstance(doc, dict):
                continue
            device = doc.get('device', 'Unknown')
            if isinstance(device, dict):
                device = device.get('name', 'Unknown')
            doc_type = doc.get('doc_type', 'Unknown')
            filename = doc.get('filename', 'Unknown')
            table.add_row(str(device), str(doc_type), str(filename))
            
        console.print(table)
    except Exception as e:
        import traceback
        console.print(f"[red]Error searching: {e}[/red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")



async def cmd_missing(args):
    console.print("[bold cyan]Missing Documents Report[/bold cyan]")
    if args.group:
        console.print(f"Filter by group: {args.group}")
    
    try:
        db = await get_db()
        from rich.table import Table
        
        target_doc_types = [args.doc_type] if args.doc_type else ['price', 'technical']
        
        # Query devices to see which don't have these docs
        query = """
        SELECT id, name, display_name,
            (SELECT doc_type FROM document WHERE device = $parent.id) AS docs
        FROM device
        """
        if args.group:
            query += f" WHERE group = '{args.group}'"
        
        results = await db.query(query)
        # Results structure handling for surreal v3.0 logic
        devices = []
        if isinstance(results, list):
            # Sometimes wrapping list, sometimes direct
            devices = results if isinstance(results[0], dict) else results[0]
            
        table = Table(title="Devices Missing Documents", show_header=True, header_style="bold magenta")
        table.add_column("Device Name", justify="left", style="cyan")
        table.add_column("Missing Types", justify="left", style="red")
        
        missing_count = 0
        for dev in devices:
             if not isinstance(dev, dict):
                 continue
                 
             dev_docs = dev.get('docs', [])
             types_found = [d.get('doc_type') for d in dev_docs if isinstance(d, dict)]
             missing = [t for t in target_doc_types if t not in types_found]
             
             if missing:
                 dev_name = dev.get('display_name') or dev.get('name') or str(dev.get('id', 'Unknown'))
                 table.add_row(dev_name, ", ".join(missing))
                 missing_count += 1
                 
        if missing_count == 0:
            console.print("[green]No devices are missing the specified documents![/green]")
        else:
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error checking missing docs: {e}[/red]")



async def cmd_wiki(args):
    if args.action == "sync":
        console.print("[bold cyan]Syncing to Outline Wiki...[/bold cyan]")
        if args.device:
             console.print(f"Only syncing device: {args.device}")
        # TODO: Call wiki_agent

async def cmd_normalize(args):
    import subprocess
    cmd = ["python", "scripts/normalize_folders.py", "--recursive"]
    if args.dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd)

async def cmd_merge_dupes(args):
    # Already handled by normalize_folders.py 
    console.print("Please use [bold]python cli.py normalize[/bold] instead. It handles merging.")


# ─── CLI setup ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MedDevice DMS — CLI Manager v2.0")
    subparsers = parser.add_subparsers(dest="command", required=True, title="Commands")

    # Command: stats
    p_stats = subparsers.add_parser("stats", help="Hiển thị thống kê tổng quan hệ thống")
    p_stats.add_argument("--verbose", action="store_true", help="Hiển thị chi tiết (biểu đồ text, file lớn)")
    p_stats.set_defaults(func=cmd_stats)

    # Command: health
    p_health = subparsers.add_parser("health", help="Kiểm tra kết nối DB và Wiki")
    p_health.set_defaults(func=cmd_health)

    # Command: scan
    p_scan = subparsers.add_parser("scan", help="Quét và nạp thiết bị mới từ storage/files")
    p_scan.add_argument("--dry-run", action="store_true", help="Preview kết quả không ghi DB")
    p_scan.add_argument("--path", help="Chỉ định thư mục quét (default: storage/files/all)")
    p_scan.set_defaults(func=cmd_scan)

    # Command: search
    p_search = subparsers.add_parser("search", help="Tìm kiếm nội dung tài liệu")
    p_search.add_argument("query", help="Từ khóa tìm kiếm")
    p_search.add_argument("--json", action="store_true", help="Output JSON dataset RAW")
    p_search.set_defaults(func=cmd_search)

    # Command: missing
    p_miss = subparsers.add_parser("missing", help="Tìm các thiết bị đang thiếu loại tài liệu quan trọng")
    p_miss.add_argument("--group", help="Lọc riêng The group (VD: ct-scan)")
    p_miss.add_argument("--doc-type", help="Chỉ kiểm tra thiếu loại doc cụ thể (VD: price)")
    p_miss.set_defaults(func=cmd_missing)

    # Command: wiki
    p_wiki = subparsers.add_parser("wiki", help="Công cụ quản lý Outline Wiki")
    p_wiki.add_argument("action", choices=["sync"], help="Thực hiện đồng bộ")
    p_wiki.add_argument("--device", help="Chỉ đồng bộ 1 thiết bị cụ thể")
    p_wiki.set_defaults(func=cmd_wiki)

    # Command: normalize (Phase 0 shortcut)
    p_norm = subparsers.add_parser("normalize", help="(Phase 0) Chuẩn hóa lại tên folder và merge trùng lặp")
    p_norm.add_argument("--dry-run", action="store_true", help="Preview thay đổi")
    p_norm.set_defaults(func=cmd_normalize)

    # Command: merge-dupes (alias pointer)
    p_dupe = subparsers.add_parser("merge-dupes", help="Alias cho lệnh normalize")
    p_dupe.set_defaults(func=cmd_merge_dupes)

    # Execute
    args = parser.parse_args()
    
    # Run async function mapping
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop and loop.is_running():
        # Handle case where event loop is already running
        asyncio.create_task(args.func(args))
    else:
        asyncio.run(args.func(args))


if __name__ == "__main__":
    main()

