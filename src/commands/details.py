from server.api import fetch_problem_list
from lib.ui import display_problem_stats
from rich.spinner import Spinner
from rich.live import Live

def details():
    """List all available LeetCode problems."""
    spinner = Spinner('dots')
    with Live(spinner, refresh_per_second=10, transient=True) as live:
        live.console.print("[cyan]Fetching problem list...")
        data = fetch_problem_list()
    display_problem_stats(data)
