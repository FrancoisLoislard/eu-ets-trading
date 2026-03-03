"""
main.py — CLI Entry Point
=========================
Usage:
    python main.py backtest --strategy momentum --start 2018-01-01 --end 2024-01-01
    python main.py paper-trade --strategy momentum --capital 100000
    python main.py data --fetch-all
    python main.py dashboard
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

BANNER = """
███████╗██╗   ██╗      ███████╗████████╗███████╗
██╔════╝██║   ██║      ██╔════╝╚══██╔══╝██╔════╝
█████╗  ██║   ██║█████╗█████╗     ██║   ███████╗
██╔══╝  ██║   ██║╚════╝██╔══╝     ██║   ╚════██║
███████╗╚██████╔╝      ███████╗   ██║   ███████║
╚══════╝ ╚═════╝       ╚══════╝   ╚═╝   ╚══════╝

   🌍 EU Emissions Trading System — Algorithmic Trading
"""


@click.group()
@click.version_option("0.1.0")
def cli():
    """EU-ETS Algorithmic Trading System."""
    console.print(Panel(BANNER, style="bold green"))


@cli.command()
@click.option("--fetch-all", is_flag=True, help="Download all universe tickers")
@click.option("--start", default="2015-01-01", help="Start date (YYYY-MM-DD)")
def data(fetch_all, start):
    """📥 Data collection and management."""
    if fetch_all:
        console.print("[bold cyan]Fetching all universe data from Yahoo Finance...[/]")
        from data.collector import DataCollector
        collector = DataCollector()
        collector.fetch_all(start=start)
        console.print("[bold green]✓ Data collection complete.[/]")


@cli.command()
@click.option("--strategy", required=True,
              type=click.Choice(["momentum", "mean_reversion", "spread", "seasonal", "ensemble"]),
              help="Strategy to backtest")
@click.option("--start", default="2018-01-01", help="Backtest start date")
@click.option("--end",   default="2024-01-01", help="Backtest end date")
@click.option("--capital", default=100_000, help="Initial capital in EUR")
@click.option("--optimize", is_flag=True, help="Run parameter optimization")
@click.option("--report", default=None, help="Output HTML report path")
def backtest(strategy, start, end, capital, optimize, report):
    """📊 Run backtesting on historical data."""
    console.print(f"[bold cyan]Running backtest: [yellow]{strategy}[/] | {start} → {end}[/]")

    from backtest.engine import BacktestEngine
    engine = BacktestEngine(
        strategy_name=strategy,
        start_date=start,
        end_date=end,
        initial_capital=capital,
    )

    if optimize:
        console.print("[cyan]Running parameter optimization with Optuna...[/]")
        engine.optimize()

    results = engine.run()
    results.print_summary()

    if report:
        results.to_html(report)
        console.print(f"[green]✓ Report saved to {report}[/]")


@cli.command("paper-trade")
@click.option("--strategy", required=True,
              type=click.Choice(["momentum", "mean_reversion", "spread", "seasonal"]),
              help="Strategy to run")
@click.option("--capital", default=100_000, help="Starting paper capital in EUR")
@click.option("--duration", default="30d", help="Duration (e.g. 7d, 30d, 90d)")
def paper_trade(strategy, capital, duration):
    """🔄 Run paper trading simulation with live data."""
    console.print(f"[bold cyan]Starting paper trading: [yellow]{strategy}[/] | Capital: €{capital:,}[/]")
    console.print("[yellow]⚠️  Paper trading mode — no real money involved[/]")

    from execution.paper_trader import PaperTrader
    trader = PaperTrader(
        strategy_name=strategy,
        initial_capital=capital,
    )
    trader.run(duration=duration)


@cli.command()
def dashboard():
    """📈 Launch Streamlit monitoring dashboard."""
    console.print("[cyan]Launching dashboard at http://localhost:8501[/]")
    import subprocess
    subprocess.run(["streamlit", "run", "dashboard/app.py"])


if __name__ == "__main__":
    cli()
