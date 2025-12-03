"""CLI-Befehle für das Skriptendruckprogramm."""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import get_logger, settings, setup_logging
from ..database.service import DatabaseService
from ..models import OrderStatus
from ..processing.pipeline import OrderPipeline
from ..services import PricingService
from ..services.excel_service import ExcelExportService

app = typer.Typer(
    name="skriptendruck",
    help="Modernisiertes Skriptendruckprogramm für die Fachschaft",
    add_completion=False,
)

console = Console()
logger = get_logger("cli")


@app.command()
def process(
    orders_dir: Optional[Path] = typer.Option(
        None,
        "--orders-dir",
        "-i",
        help="Verzeichnis mit Aufträgen (Standard: aus Settings)"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Ausgabeverzeichnis (Standard: aus Settings)"
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        help="Sequenzielle statt parallele Verarbeitung"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Ausführliche Ausgabe"
    ),
) -> None:
    """
    Verarbeitet Druckaufträge.

    Liest PDF-Dateien aus dem Auftragsverzeichnis, validiert Benutzer,
    berechnet Preise und erstellt Deckblätter.
    """
    # Logging einrichten
    log_level = "DEBUG" if verbose else settings.log_level
    setup_logging(level=log_level, log_file=settings.log_file)

    # Verzeichnisse
    orders_dir = orders_dir or settings.get_orders_directory()
    output_dir = output_dir or settings.get_output_directory()

    # Parallel-Option
    settings.parallel_processing = not sequential

    console.print(f"\n[bold blue]Skriptendruck - Verarbeitung[/bold blue]")
    console.print(f"Aufträge: {orders_dir}")
    console.print(f"Ausgabe: {output_dir}\n")

    # Pipeline initialisieren
    pipeline = OrderPipeline()

    # Aufträge finden
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Suche nach Aufträgen...", total=None)
        orders = pipeline.discover_orders(orders_dir)
        progress.update(task, completed=True)

    if not orders:
        console.print("[yellow]Keine Aufträge gefunden.[/yellow]")
        return

    console.print(f"[green]Gefunden: {len(orders)} Aufträge[/green]\n")

    # Aufträge verarbeiten
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Verarbeite {len(orders)} Aufträge...",
            total=len(orders)
        )

        processed_orders = pipeline.process_orders(orders, output_dir)
        progress.update(task, completed=len(orders))

    # Zusammenfassung
    _display_summary(processed_orders)


@app.command()
def init_data() -> None:
    """
    Initialisiert Beispieldaten und Konfigurationsdateien.

    Erstellt:
    - Beispiel-Ringbindungsgrößen (binding_sizes.json)
    - Beispiel-Blacklist
    - Beispiel-.env-Datei
    """
    console.print("\n[bold blue]Initialisiere Daten...[/bold blue]\n")

    # Binding Sizes JSON
    pricing_service = PricingService()
    binding_path = Path("data/binding_sizes.json")

    if binding_path.exists():
        console.print(f"[yellow]Überspringe: {binding_path} existiert bereits[/yellow]")
    else:
        pricing_service.export_default_binding_sizes_json(binding_path)
        console.print(f"[green]✓[/green] Erstellt: {binding_path}")

    # Blacklist
    blacklist_path = Path("data/blacklist.txt")
    if blacklist_path.exists():
        console.print(f"[yellow]Überspringe: {blacklist_path} existiert bereits[/yellow]")
    else:
        blacklist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(blacklist_path, "w", encoding="utf-8") as f:
            f.write("# Blockierte Benutzer (RZ-Kennungen)\n")
            f.write("# Ein Username pro Zeile\n")
        console.print(f"[green]✓[/green] Erstellt: {blacklist_path}")

    # Users CSV (Fallback)
    users_csv_path = Path("data/users_fallback.csv")
    if users_csv_path.exists():
        console.print(f"[yellow]Überspringe: {users_csv_path} existiert bereits[/yellow]")
    else:
        users_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(users_csv_path, "w", encoding="utf-8") as f:
            f.write("# Format: username firstname lastname faculty\n")
            f.write("# Beispiel:\n")
            f.write("# mus43225 Sebastian Müllner M\n")
        console.print(f"[green]✓[/green] Erstellt: {users_csv_path}")

    # .env Beispiel
    env_example_path = Path(".env.example")
    if not env_example_path.exists():
        with open(env_example_path, "w", encoding="utf-8") as f:
            f.write("# Basis-Konfiguration\n")
            f.write("BASE_PATH=H:/stud/fsmb/03_Dienste/01_Skriptendruck\n")
            f.write("ORDERS_PATH=01_Auftraege\n")
            f.write("OUTPUT_PATH=output\n\n")
            f.write("# LDAP Konfiguration\n")
            f.write("LDAP_ENABLED=false\n")
            f.write("#LDAP_SERVER=adldap.hs-regensburg.de\n")
            f.write("#LDAP_BASE_DN=dc=hs-regensburg,dc=de\n\n")
            f.write("# Logging\n")
            f.write("LOG_LEVEL=INFO\n")
            f.write("#LOG_FILE=skriptendruck.log\n")
        console.print(f"[green]✓[/green] Erstellt: {env_example_path}")

    console.print("\n[green]Initialisierung abgeschlossen![/green]")


@app.command()
def stats(
    orders_dir: Optional[Path] = typer.Option(
        None,
        "--orders-dir",
        "-i",
        help="Verzeichnis mit Aufträgen"
    ),
) -> None:
    """
    Zeigt Statistiken über vorhandene Aufträge.
    """
    orders_dir = orders_dir or settings.get_orders_directory()

    pipeline = OrderPipeline()
    orders = pipeline.discover_orders(orders_dir)

    if not orders:
        console.print("[yellow]Keine Aufträge gefunden.[/yellow]")
        return

    # Einfache Statistik
    table = Table(title=f"Statistik: {orders_dir}")
    table.add_column("Metrik", style="cyan")
    table.add_column("Wert", style="green")

    table.add_row("Anzahl Aufträge", str(len(orders)))

    total_size = sum(o.file_size_bytes for o in orders)
    table.add_row("Gesamtgröße", f"{total_size / 1024 / 1024:.2f} MB")

    console.print()
    console.print(table)


@app.command()
def export_excel(
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Ausgabeverzeichnis für Excel-Dateien"
    ),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Anzahl Tage rückwirkend"
    ),
) -> None:
    """
    Exportiert Auftrags- und Abrechnungslisten nach Excel.

    Erstellt zwei Excel-Dateien:
    - Auftragsliste.xlsx: Alle Aufträge
    - Abrechnungsliste.xlsx: Offene Abrechnungen
    """
    console.print(f"\n[bold blue]Excel-Export[/bold blue]\n")

    output_dir = output_dir or settings.get_output_directory()
    output_dir.mkdir(parents=True, exist_ok=True)

    db_service = DatabaseService()
    excel_service = ExcelExportService()

    # Zeitraum berechnen
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Aufträge exportieren
        task = progress.add_task("Exportiere Auftragsliste...", total=None)
        orders = db_service.get_orders_by_date_range(start_date, end_date)

        if orders:
            orders_path = output_dir / f"Auftragsliste_{end_date.strftime('%Y%m%d')}.xlsx"
            if excel_service.export_orders_list(orders, orders_path):
                console.print(f"[green]✓[/green] Auftragsliste: {orders_path}")
            else:
                console.print(f"[red]✗[/red] Fehler beim Export der Auftragsliste")
        else:
            console.print("[yellow]Keine Aufträge im Zeitraum gefunden[/yellow]")

        progress.update(task, completed=True)

        # Abrechnungen exportieren
        task = progress.add_task("Exportiere Abrechnungsliste...", total=None)
        billings = db_service.get_unpaid_billings()

        if billings:
            billings_path = output_dir / f"Abrechnungsliste_{end_date.strftime('%Y%m%d')}.xlsx"
            if excel_service.export_billing_list(billings, billings_path):
                console.print(f"[green]✓[/green] Abrechnungsliste: {billings_path}")
            else:
                console.print(f"[red]✗[/red] Fehler beim Export der Abrechnungsliste")
        else:
            console.print("[yellow]Keine offenen Abrechnungen[/yellow]")

        progress.update(task, completed=True)

    console.print()


@app.command()
def db_stats() -> None:
    """
    Zeigt Datenbank-Statistiken.
    """
    console.print(f"\n[bold blue]Datenbank-Statistiken[/bold blue]\n")

    db_service = DatabaseService()
    stats = db_service.get_statistics()

    table = Table()
    table.add_column("Metrik", style="cyan")
    table.add_column("Wert", style="green")

    table.add_row("Gesamt Aufträge", str(stats["total_orders"]))
    table.add_row("Erfolgreich", str(stats["successful_orders"]))
    table.add_row("Fehler", str(stats["error_orders"]))
    table.add_row("Gesamtumsatz", f"{stats['total_revenue']:.2f} €")

    console.print(table)
    console.print()


def _display_summary(orders: list) -> None:
    """Zeigt Zusammenfassung der verarbeiteten Aufträge."""
    console.print("\n[bold blue]Zusammenfassung[/bold blue]\n")

    # Statistik
    total = len(orders)
    success = sum(1 for o in orders if o.status == OrderStatus.PROCESSED)
    errors = total - success

    console.print(f"Gesamt: {total}")
    console.print(f"[green]Erfolgreich: {success}[/green]")
    console.print(f"[red]Fehler: {errors}[/red]\n")

    # Fehler-Details
    if errors > 0:
        error_table = Table(title="Fehler")
        error_table.add_column("Order ID", style="cyan")
        error_table.add_column("Dateiname")
        error_table.add_column("Status", style="red")
        error_table.add_column("Nachricht")

        for order in orders:
            if order.is_error:
                error_table.add_row(
                    str(order.order_id),
                    order.filename,
                    order.status.value,
                    order.error_message or ""
                )

        console.print(error_table)
        console.print()


@app.callback()
def main() -> None:
    """Skriptendruck - Modernisiertes Druckauftrags-Verwaltungssystem."""
    pass