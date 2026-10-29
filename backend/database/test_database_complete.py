"""
ImmunoGrid — Database Layer Complete Test Suite
Tests ORM models, CRUD operations, migrations, and graceful no-DB fallback.

Run:
    python backend/database/test_database_complete.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
results = []


def check(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        console.print(f"  [green]✅ {name}[/green]")
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        console.print(f"  [red]❌ {name}: {str(e)[:70]}[/red]")


console.print("\n[bold cyan]╔══════════════════════════════════════════════════╗[/bold cyan]")
console.print("[bold cyan]║  ImmunoGrid Database — Complete Test Suite      ║[/bold cyan]")
console.print("[bold cyan]╚══════════════════════════════════════════════════╝[/bold cyan]\n")
