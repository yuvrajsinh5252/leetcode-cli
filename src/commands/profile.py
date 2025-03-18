def profile():
    """List all available LeetCode problems."""
    from rich.live import Live
    from rich.spinner import Spinner

    from ..lib.profile_ui import display_user_stats
    from ..server.api import fetch_user_profile

    spinner = Spinner("dots")
    with Live(spinner, refresh_per_second=10, transient=True) as live:
        live.console.print("[cyan]Fetching user profile...")
        data = fetch_user_profile()
    display_user_stats(data)
