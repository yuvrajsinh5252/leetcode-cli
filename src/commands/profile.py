from server.api import fetch_user_data
from lib.ui import display_problem_stats
from rich.spinner import Spinner
from rich.live import Live

def profile():
    """List all available LeetCode problems."""
    spinner = Spinner('dots')
    with Live(spinner, refresh_per_second=10, transient=True) as live:
        live.console.print("[cyan]Fetching user profile...")
        data = fetch_user_data()
    display_problem_stats(data)
