"""
POTALE Stock Collector - Textual TUI Application
Claude Code style interactive terminal interface with multi-panel layout

Phase 1: Multi-Panel Layout (Sidebar + Main + Log)
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, Label, Input,
    DataTable, ProgressBar, Log, ListView, ListItem
)
from textual.screen import Screen
from textual.binding import Binding
from textual.reactive import reactive
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class Sidebar(Container):
    """Left sidebar navigation"""

    def compose(self) -> ComposeResult:
        """Create sidebar"""
        yield Static("[bold]POTALE[/bold]", id="sidebar-title")

        with ListView(id="nav-list"):
            yield ListItem(Static("[1] Dashboard"), id="nav-dashboard")
            yield ListItem(Static("[2] Collect All"), id="nav-collect-all")
            yield ListItem(Static("[3] Collect Specific"), id="nav-collect-specific")
            yield ListItem(Static("[4] Validate"), id="nav-validate")
            yield ListItem(Static("[5] Analyze"), id="nav-analyze")
            yield ListItem(Static("[6] Settings"), id="nav-settings")
            yield ListItem(Static("[Q] Exit"), id="nav-exit")


class MainPanel(Container):
    """Right main content panel"""

    current_view = reactive("dashboard")

    def compose(self) -> ComposeResult:
        """Create main panel"""
        yield Static("[bold cyan]Dashboard[/bold cyan]", id="panel-title")
        with ScrollableContainer(id="panel-content"):
            yield Static(self._get_dashboard_content(), id="content-display")

    def _get_dashboard_content(self) -> str:
        """Get dashboard content"""
        return """[bold]POTALE Stock Data Collector[/bold]

[yellow]Professional Korean Stock Market Data Collection Tool[/yellow]

[dim]Key Features:[/dim]
- 100% Naver Finance Data Source
- Hybrid Mode (Adjusted Price + Volume)
- 4,189 Stocks (KOSPI + KOSDAQ)
- Real-time Collection
- Data Validation
- Analysis Tools

[dim]Navigation:[/dim]
- Use number keys [1-6] or arrow keys to navigate
- Press [Q] to exit
- Press [ESC] to go back

[dim]Database:[/dim] data/database/stock_data.db
[dim]Version:[/dim] 1.0.0
"""

    def update_view(self, view_name: str, content: str = None) -> None:
        """Update current view"""
        self.current_view = view_name
        title_widget = self.query_one("#panel-title", Static)
        content_widget = self.query_one("#content-display", Static)

        title_mapping = {
            "dashboard": "[bold cyan]Dashboard[/bold cyan]",
            "collect-all": "[bold cyan]Collect All Stocks[/bold cyan]",
            "collect-specific": "[bold cyan]Collect Specific Tickers[/bold cyan]",
            "validate": "[bold cyan]Data Validation[/bold cyan]",
            "analyze": "[bold cyan]Data Analysis[/bold cyan]",
            "settings": "[bold cyan]Settings[/bold cyan]",
        }

        title_widget.update(title_mapping.get(view_name, "[bold]Unknown[/bold]"))

        if content:
            content_widget.update(content)
        else:
            # Generate default content based on view
            if view_name == "dashboard":
                content_widget.update(self._get_dashboard_content())


class LogPanel(Container):
    """Bottom log panel"""

    def compose(self) -> ComposeResult:
        """Create log panel"""
        yield Static("[bold]Activity Log[/bold]", id="log-title")
        yield Log(id="activity-log", auto_scroll=True)

    def write_log(self, message: str, level: str = "info") -> None:
        """Write to log with timestamp"""
        log = self.query_one("#activity-log", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")

        color_map = {
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }

        color = color_map.get(level, "white")
        log.write_line(f"[dim]{timestamp}[/dim] [{color}]{message}[/{color}]")


class CollectionScreen(Screen):
    """Dedicated screen for data collection with real-time progress"""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("s", "start_collection", "Start"),
        Binding("p", "pause_collection", "Pause"),
        Binding("c", "cancel_collection", "Cancel"),
    ]

    def __init__(self, collect_all: bool = True, tickers: Optional[List[str]] = None):
        super().__init__()
        self.collect_all = collect_all
        self.tickers = tickers or []
        self.worker: Optional['CollectionWorker'] = None
        self.is_collecting = False
        self.is_paused = False

    def compose(self) -> ComposeResult:
        """Create collection screen layout"""
        yield Header(show_clock=True)

        with Container(id="collection-screen"):
            yield Static("[bold cyan]Stock Data Collection[/bold cyan]", id="collection-title")

            # Configuration panel
            with Vertical(id="config-panel"):
                yield Label("From Date:")
                yield Input(value="2024-01-01", placeholder="YYYY-MM-DD", id="from-date")
                yield Label("To Date:")
                yield Input(value=str(date.today()), placeholder="YYYY-MM-DD", id="to-date")

                if not self.collect_all:
                    yield Label("Tickers (comma-separated):")
                    yield Input(placeholder="005930,000660,035720", id="tickers-input")

            # Progress panel
            with Vertical(id="progress-panel"):
                yield Static("[dim]Progress:[/dim]", id="progress-label")
                yield ProgressBar(total=100, show_eta=False, id="collection-progress")
                yield Static("Ready to start...", id="progress-status")

            # Control buttons
            with Horizontal(id="control-buttons"):
                yield Button("Start [S]", id="start-btn", variant="success")
                yield Button("Pause [P]", id="pause-btn", variant="warning", disabled=True)
                yield Button("Cancel [C]", id="cancel-btn", variant="error", disabled=True)
                yield Button("Back [ESC]", id="back-btn")

            # Collection log
            yield Log(id="collection-log", auto_scroll=True)

        yield Footer()

    def on_mount(self) -> None:
        """Initialize on mount"""
        log = self.query_one("#collection-log", Log)
        if self.collect_all:
            log.write_line("[cyan]Collect All Stocks Mode[/cyan]")
            log.write_line("[dim]Will collect data for all 4,189 tickers[/dim]")
        else:
            log.write_line("[cyan]Collect Specific Tickers Mode[/cyan]")
            log.write_line("[dim]Enter ticker codes to collect[/dim]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id

        if button_id == "start-btn":
            self.action_start_collection()
        elif button_id == "pause-btn":
            self.action_pause_collection()
        elif button_id == "cancel-btn":
            self.action_cancel_collection()
        elif button_id == "back-btn":
            self.app.pop_screen()

    def action_start_collection(self) -> None:
        """Start or resume collection"""
        if self.is_collecting and self.is_paused:
            # Resume
            if self.worker:
                self.worker.resume()
                self.is_paused = False
                self._update_button_states()
                self._log("[green]Collection resumed[/green]")
            return

        # Get parameters
        from_date_str = self.query_one("#from-date", Input).value
        to_date_str = self.query_one("#to-date", Input).value

        try:
            from_date_obj = datetime.strptime(from_date_str, "%Y-%m-%d").date()
            to_date_obj = datetime.strptime(to_date_str, "%Y-%m-%d").date()
        except ValueError:
            self._log("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            return

        # Get tickers
        if self.collect_all:
            # Load all tickers
            self._log("[cyan]Loading ticker list...[/cyan]")
            tickers = self._load_all_tickers()
        else:
            tickers_input = self.query_one("#tickers-input", Input).value
            if not tickers_input:
                self._log("[red]Please enter ticker codes[/red]")
                return
            tickers = [t.strip() for t in tickers_input.split(',')]

        if not tickers:
            self._log("[red]No tickers to collect[/red]")
            return

        # Start collection
        self._log(f"[cyan]Starting collection for {len(tickers)} tickers...[/cyan]")
        self._log(f"[dim]Period: {from_date_obj} to {to_date_obj}[/dim]")

        # Import worker
        from src.cli.tui_workers import CollectionWorker

        # Create and start worker
        self.worker = CollectionWorker(
            tickers=tickers,
            from_date=from_date_obj,
            to_date=to_date_obj,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

        self.worker.start()
        self.is_collecting = True
        self._update_button_states()

        # Update progress bar total
        progress_bar = self.query_one("#collection-progress", ProgressBar)
        progress_bar.update(total=len(tickers))

    def action_pause_collection(self) -> None:
        """Pause collection"""
        if self.worker and self.is_collecting:
            if self.is_paused:
                self.worker.resume()
                self.is_paused = False
                self._log("[green]Resumed[/green]")
            else:
                self.worker.pause()
                self.is_paused = True
                self._log("[yellow]Paused[/yellow]")

            self._update_button_states()

    def action_cancel_collection(self) -> None:
        """Cancel collection"""
        if self.worker and self.is_collecting:
            self.worker.stop()
            self.is_collecting = False
            self.is_paused = False
            self._update_button_states()
            self._log("[red]Collection cancelled[/red]")

    def _load_all_tickers(self) -> List[str]:
        """Load all ticker codes from database or API"""
        try:
            from src.infrastructure.collectors.naver.naver_ticker_list import NaverTickerListCollector

            collector = NaverTickerListCollector()
            result = collector.collect()

            if result.success:
                tickers = [item.ticker for item in result.data]
                self._log(f"[green]Loaded {len(tickers)} tickers[/green]")
                return tickers
            else:
                self._log(f"[red]Failed to load tickers: {result.error_message}[/red]")
                return []
        except Exception as e:
            self._log(f"[red]Error loading tickers: {str(e)}[/red]")
            return []

    def _on_progress(self, ticker: str, current: int, total: int, records: int) -> None:
        """Progress callback from worker"""
        # Update progress bar
        progress_bar = self.query_one("#collection-progress", ProgressBar)
        progress_bar.update(progress=current)

        # Update status
        status = self.query_one("#progress-status", Static)
        percentage = (current / total * 100) if total > 0 else 0
        status.update(f"[cyan]{current}/{total}[/cyan] ({percentage:.1f}%) - {ticker} - {records:,} records collected")

        # Log progress
        self._log(f"[dim]{current}/{total}[/dim] {ticker} - {records:,} total records")

    def _on_complete(self, stats: dict) -> None:
        """Completion callback from worker"""
        self.is_collecting = False
        self._update_button_states()

        # Log completion
        self._log("")
        self._log("[green]Collection Complete![/green]")
        self._log(f"[cyan]Total Tickers:[/cyan] {stats['total_tickers']}")
        self._log(f"[cyan]Completed:[/cyan] {stats['completed']}")
        self._log(f"[cyan]Failed:[/cyan] {stats['failed']}")
        self._log(f"[cyan]Total Records:[/cyan] {stats['total_records']:,}")

        # Update status
        status = self.query_one("#progress-status", Static)
        status.update(f"[green]Complete! {stats['total_records']:,} records collected[/green]")

        self.notify("Collection completed successfully!", severity="information")

    def _on_error(self, error_msg: str) -> None:
        """Error callback from worker"""
        self.is_collecting = False
        self._update_button_states()

        self._log(f"[red]Error: {error_msg}[/red]")
        self.notify(f"Collection error: {error_msg}", severity="error")

    def _log(self, message: str) -> None:
        """Write to collection log"""
        log = self.query_one("#collection-log", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[dim]{timestamp}[/dim] {message}")

    def _update_button_states(self) -> None:
        """Update button enabled/disabled states"""
        start_btn = self.query_one("#start-btn", Button)
        pause_btn = self.query_one("#pause-btn", Button)
        cancel_btn = self.query_one("#cancel-btn", Button)

        if self.is_collecting:
            start_btn.disabled = True
            pause_btn.disabled = False
            cancel_btn.disabled = False

            if self.is_paused:
                pause_btn.label = "Resume [P]"
            else:
                pause_btn.label = "Pause [P]"
        else:
            start_btn.disabled = False
            pause_btn.disabled = True
            cancel_btn.disabled = True


class CommandPaletteScreen(Screen):
    """Command Palette - Quick command search (Ctrl+P)"""

    BINDINGS = [
        Binding("escape", "pop_screen", "Close"),
        Binding("enter", "execute_command", "Execute"),
    ]

    COMMANDS = [
        ("Dashboard", "nav_dashboard", "View main dashboard"),
        ("Collect All Stocks", "nav_collect_all", "Collect data for all 4,189 stocks"),
        ("Collect Specific Tickers", "nav_collect_specific", "Collect data for specific tickers"),
        ("Validate Data", "nav_validate", "Run data validation checks"),
        ("Analyze Data", "nav_analyze", "View data analysis and statistics"),
        ("Settings", "nav_settings", "View application settings"),
        ("Exit Application", "quit_app", "Quit the application"),
    ]

    def compose(self) -> ComposeResult:
        """Create command palette layout"""
        yield Header(show_clock=True)

        with Container(id="palette-container"):
            yield Static("[bold cyan]Command Palette[/bold cyan]", id="palette-title")
            yield Label("Type to search commands...")
            yield Input(placeholder="Search...", id="palette-search")

            with ScrollableContainer(id="command-list"):
                for name, action, desc in self.COMMANDS:
                    yield Button(f"{name}\n[dim]{desc}[/dim]", id=f"cmd-{action}", classes="command-button")

        yield Footer()

    def on_mount(self) -> None:
        """Focus search input on mount"""
        search_input = self.query_one("#palette-search", Input)
        search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands based on search"""
        if event.input.id == "palette-search":
            query = event.value.lower()

            # Show/hide buttons based on search
            for name, action, desc in self.COMMANDS:
                button = self.query_one(f"#cmd-{action}", Button)
                if query in name.lower() or query in desc.lower():
                    button.display = True
                else:
                    button.display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Execute command when button pressed"""
        button_id = event.button.id
        if button_id.startswith("cmd-"):
            action = button_id.replace("cmd-", "")
            self.app.pop_screen()  # Close palette
            # Execute action on main screen
            main_screen = self.app.screen_stack[0]
            if hasattr(main_screen, f"action_{action}"):
                getattr(main_screen, f"action_{action}")()

    def action_execute_command(self) -> None:
        """Execute first visible command on Enter"""
        for name, action, desc in self.COMMANDS:
            button = self.query_one(f"#cmd-{action}", Button)
            if button.display:
                self.on_button_pressed(Button.Pressed(button))
                break


class MainScreen(Screen):
    """Main screen with multi-panel layout"""

    BINDINGS = [
        Binding("q", "quit_app", "Quit"),
        Binding("1", "nav_dashboard", "Dashboard"),
        Binding("2", "nav_collect_all", "Collect All"),
        Binding("3", "nav_collect_specific", "Collect Specific"),
        Binding("4", "nav_validate", "Validate"),
        Binding("5", "nav_analyze", "Analyze"),
        Binding("6", "nav_settings", "Settings"),
        Binding("escape", "go_back", "Back"),
        Binding("ctrl+p", "command_palette", "Command Palette"),
    ]

    def compose(self) -> ComposeResult:
        """Create main screen layout"""
        yield Header(show_clock=True)

        with Horizontal(id="main-layout"):
            yield Sidebar()
            yield MainPanel()

        yield LogPanel()
        yield Footer()

    def on_mount(self) -> None:
        """Initialize on mount"""
        log_panel = self.query_one(LogPanel)
        log_panel.write_log("TUI initialized successfully", "success")
        log_panel.write_log("Ready to collect stock data", "info")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle sidebar navigation"""
        item_id = event.item.id

        if item_id == "nav-dashboard":
            self.action_nav_dashboard()
        elif item_id == "nav-collect-all":
            self.action_nav_collect_all()
        elif item_id == "nav-collect-specific":
            self.action_nav_collect_specific()
        elif item_id == "nav-validate":
            self.action_nav_validate()
        elif item_id == "nav-analyze":
            self.action_nav_analyze()
        elif item_id == "nav-settings":
            self.action_nav_settings()
        elif item_id == "nav-exit":
            self.action_quit_app()

    def action_nav_dashboard(self) -> None:
        """Navigate to dashboard"""
        main_panel = self.query_one(MainPanel)
        main_panel.update_view("dashboard")

        log_panel = self.query_one(LogPanel)
        log_panel.write_log("Navigated to Dashboard", "info")

    def action_nav_collect_all(self) -> None:
        """Navigate to collect all - Push new screen"""
        log_panel = self.query_one(LogPanel)
        log_panel.write_log("Opening Collect All screen...", "info")
        self.app.push_screen(CollectionScreen(collect_all=True))

    def action_nav_collect_specific(self) -> None:
        """Navigate to collect specific - Push new screen"""
        log_panel = self.query_one(LogPanel)
        log_panel.write_log("Opening Collect Specific screen...", "info")
        self.app.push_screen(CollectionScreen(collect_all=False))

    def action_nav_validate(self) -> None:
        """Navigate to validate"""
        main_panel = self.query_one(MainPanel)
        log_panel = self.query_one(LogPanel)

        log_panel.write_log("Running data validation...", "info")

        try:
            from src.infrastructure.database.connection import DatabaseConnection
            from src.infrastructure.database.models import StockPrice, StockInfo

            db_path = "data/database/stock_data.db"

            if not Path(db_path).exists():
                content = """[red]Database not found[/red]

The database file does not exist at:
[dim]{db_path}[/dim]

Please run data collection first.
"""
                main_panel.update_view("validate", content)
                log_panel.write_log("Database not found", "error")
                return

            db_conn = DatabaseConnection(db_path)
            session = db_conn.get_session()

            total_stocks = session.query(StockInfo).count()
            total_records = session.query(StockPrice).count()

            if total_records > 0:
                from sqlalchemy import func
                min_date = session.query(func.min(StockPrice.date)).scalar()
                max_date = session.query(func.max(StockPrice.date)).scalar()

                content = f"""[green]Validation Results[/green]

[yellow]Database Status:[/yellow] [green]OK[/green]

[dim]Statistics:[/dim]
- Total Stocks: {total_stocks:,}
- Total Records: {total_records:,}
- Date Range: {min_date} to {max_date}

[green]Data quality check passed successfully![/green]

Press [5] to view detailed analysis.
"""
                log_panel.write_log(f"Validation complete: {total_records:,} records", "success")
            else:
                content = """[yellow]No data found in database[/yellow]

The database exists but contains no price records.

Please run data collection first.
"""
                log_panel.write_log("No data found in database", "warning")

            session.close()
            main_panel.update_view("validate", content)

        except Exception as e:
            content = f"""[red]Validation Error[/red]

{str(e)}

Please check database integrity.
"""
            main_panel.update_view("validate", content)
            log_panel.write_log(f"Validation error: {str(e)}", "error")

    def action_nav_analyze(self) -> None:
        """Navigate to analyze"""
        main_panel = self.query_one(MainPanel)
        log_panel = self.query_one(LogPanel)

        log_panel.write_log("Running analysis...", "info")

        try:
            from src.infrastructure.database.connection import DatabaseConnection
            from src.infrastructure.database.models import StockPrice, StockInfo, InvestorTrading

            db_path = "data/database/stock_data.db"

            if not Path(db_path).exists():
                content = """[red]Database not found[/red]

Cannot run analysis without data.
"""
                main_panel.update_view("analyze", content)
                log_panel.write_log("Database not found", "error")
                return

            db_conn = DatabaseConnection(db_path)
            session = db_conn.get_session()

            total_stocks = session.query(StockInfo).count()
            total_price_records = session.query(StockPrice).count()
            total_investor_records = session.query(InvestorTrading).count()

            size_mb = 0
            if Path(db_path).exists():
                size_bytes = Path(db_path).stat().st_size
                size_mb = size_bytes / (1024 * 1024)

            content = f"""[yellow]Data Analysis Summary[/yellow]

[dim]Stock Information:[/dim]
- Total Stocks: {total_stocks:,}
- Price Records: {total_price_records:,}
- Investor Records: {total_investor_records:,}

[dim]Database:[/dim]
- Path: {db_path}
- Size: {size_mb:.2f} MB

"""

            if total_price_records > 0:
                from sqlalchemy import func
                min_date = session.query(func.min(StockPrice.date)).scalar()
                max_date = session.query(func.max(StockPrice.date)).scalar()
                trading_days = session.query(StockPrice.date).distinct().count()

                content += f"""[dim]Date Coverage:[/dim]
- First Date: {min_date}
- Last Date: {max_date}
- Trading Days: {trading_days:,}

[green]Analysis complete![/green]
"""
                log_panel.write_log(f"Analysis complete: {total_price_records:,} records", "success")
            else:
                content += "[yellow]No price data available for analysis[/yellow]\n"
                log_panel.write_log("No data available for analysis", "warning")

            session.close()
            main_panel.update_view("analyze", content)

        except Exception as e:
            content = f"""[red]Analysis Error[/red]

{str(e)}
"""
            main_panel.update_view("analyze", content)
            log_panel.write_log(f"Analysis error: {str(e)}", "error")

    def action_nav_settings(self) -> None:
        """Navigate to settings"""
        main_panel = self.query_one(MainPanel)

        content = """[yellow]Settings[/yellow]

[dim]Application Configuration:[/dim]

[bold]Data Collection:[/bold]
- Mode: Hybrid (Adjusted Price + Volume)
- Source: 100% Naver Finance
- API Delay: 0.2 seconds
- Retry Count: 3

[bold]Database:[/bold]
- Path: data/database/stock_data.db
- Engine: SQLite
- Auto-commit: Enabled

[bold]Tickers:[/bold]
- Total: 4,189
- KOSPI: ~2,500
- KOSDAQ: ~1,689

[dim]Phase 7 will add interactive configuration.[/dim]

Press [ESC] to go back.
"""

        main_panel.update_view("settings", content)

        log_panel = self.query_one(LogPanel)
        log_panel.write_log("Navigated to Settings", "info")

    def action_go_back(self) -> None:
        """Go back to dashboard"""
        self.action_nav_dashboard()

    def action_command_palette(self) -> None:
        """Open command palette"""
        log_panel = self.query_one(LogPanel)
        log_panel.write_log("Opening Command Palette...", "info")
        self.app.push_screen(CommandPaletteScreen())

    def action_quit_app(self) -> None:
        """Quit application"""
        log_panel = self.query_one(LogPanel)
        log_panel.write_log("Shutting down TUI...", "info")
        self.app.exit()


class POTALEApp(App):
    """POTALE Stock Collector TUI Application"""

    CSS = """
    /* ============================================
       POTALE TUI - Claude Code Dark Theme
       VSCode Dark+ inspired color scheme
       ============================================ */

    /* Color Variables */
    $accent: #007acc;           /* Primary accent (blue) */
    $accent-light: #4fc3f7;     /* Light accent */
    $success: #4ec9b0;          /* Success (teal) */
    $warning: #ce9178;          /* Warning (orange) */
    $error: #f48771;            /* Error (red) */
    $surface: #1e1e1e;          /* Main background */
    $panel: #252526;            /* Panel background */
    $panel-dark: #1a1a1a;       /* Darker panel */
    $border: #3c3c3c;           /* Border color */
    $border-light: #454545;     /* Light border */
    $text: #d4d4d4;             /* Primary text */
    $text-muted: #858585;       /* Muted text */
    $text-bright: #ffffff;      /* Bright text */
    $highlight: #264f78;        /* Selection highlight */
    $hover: #2a2d2e;            /* Hover background */

    /* Global Styles */
    Screen {
        background: $surface;
    }

    #main-layout {
        height: 100%;
    }

    /* Sidebar Enhancements */
    Sidebar {
        width: 25;
        height: 100%;
        dock: left;
        background: $panel-dark;
        border-right: thick $border;
    }

    Sidebar Static#sidebar-title {
        background: $accent;
        color: $text-bright;
        text-style: bold;
    }

    Sidebar ListView {
        height: auto;
        padding: 0 1;
        background: $panel-dark;
    }

    Sidebar ListItem {
        padding: 1 2;
        background: $panel-dark;
        color: $text;
    }

    Sidebar ListItem:hover {
        background: $hover;
        color: $accent-light;
    }

    Sidebar ListItem:focus {
        background: $highlight;
        color: $text-bright;
        text-style: bold;
    }

    /* Main Panel Enhancements */
    MainPanel {
        height: 100%;
        background: $surface;
        padding: 1 2;
    }

    MainPanel #panel-title {
        color: $accent-light;
        text-style: bold;
        padding: 0 0 1 0;
    }

    MainPanel #panel-content {
        height: auto;
        background: $surface;
    }

    MainPanel #content-display {
        padding: 1;
        color: $text;
    }

    /* Log Panel Enhancements */
    LogPanel {
        height: 12;
        dock: bottom;
        background: $panel;
        border-top: thick $border;
    }

    LogPanel Static#log-title {
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }

    LogPanel Log#activity-log {
        height: 10;
        background: $panel-dark;
        border: solid $border;
        scrollbar-background: $panel;
        scrollbar-color: $border-light;
    }

    /* Header & Footer */
    Header {
        background: $panel;
        color: $text;
        dock: top;
    }

    Footer {
        background: $panel;
        color: $text-muted;
    }

    Footer .footer--highlight {
        background: $accent;
        color: $text-bright;
    }

    Footer .footer--key {
        background: $border;
        color: $text-bright;
    }

    /* Collection Screen Styles */
    #collection-screen {
        align: center middle;
        width: 100;
        height: auto;
        padding: 2;
    }

    #collection-title {
        text-align: center;
        margin-bottom: 1;
        color: $accent-light;
    }

    #config-panel {
        border: solid $border;
        background: $panel;
        padding: 1 2;
        margin: 1 0;
    }

    #config-panel Label {
        margin-top: 1;
        color: $text-muted;
    }

    #config-panel Input {
        margin-bottom: 1;
    }

    #progress-panel {
        border: solid $border;
        background: $panel;
        padding: 1 2;
        margin: 1 0;
    }

    #progress-label {
        color: $text-muted;
        margin-bottom: 1;
    }

    #collection-progress {
        margin: 1 0;
    }

    #progress-status {
        margin-top: 1;
        color: $text;
    }

    #control-buttons {
        height: auto;
        margin: 1 0;
    }

    #control-buttons Button {
        margin: 0 1;
    }

    #collection-log {
        height: 20;
        border: solid $border;
        background: $panel-dark;
        margin-top: 1;
    }

    /* Command Palette Styles */
    #palette-container {
        align: center middle;
        width: 80;
        height: auto;
        max-height: 90%;
        background: $panel;
        border: thick $accent;
        padding: 2;
    }

    #palette-title {
        text-align: center;
        margin-bottom: 1;
        color: $accent-light;
    }

    #palette-search {
        margin: 1 0;
        border: solid $accent;
    }

    #command-list {
        height: 30;
        margin: 1 0;
    }

    .command-button {
        width: 100%;
        margin: 0 0 1 0;
        text-align: left;
        border: solid $border;
    }

    .command-button:hover {
        background: $hover;
        border: solid $accent;
    }

    .command-button:focus {
        background: $highlight;
        border: solid $accent-light;
    }
    """

    TITLE = "POTALE Stock Collector"
    SUB_TITLE = "Professional Korean Stock Market Data Collection"

    def on_mount(self) -> None:
        """Initialize app"""
        self.push_screen(MainScreen())


def run_tui():
    """Run the TUI application"""
    app = POTALEApp()
    app.run()


if __name__ == "__main__":
    run_tui()
