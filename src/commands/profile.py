from ..server.api import fetch_user_profile
from rich.spinner import Spinner
from ..lib.ui import display_user_stats
from rich.live import Live

def profile():
    """List all available LeetCode problems."""
    spinner = Spinner('dots')
    with Live(spinner, refresh_per_second=10, transient=True) as live:
        live.console.print("[cyan]Fetching user profile...")
        data = fetch_user_profile()
    display_user_stats(data)
