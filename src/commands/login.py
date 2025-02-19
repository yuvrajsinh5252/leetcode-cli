import typer
from src.server.auth import Auth

auth_manager = Auth()

def login():
    """Login to LeetCode"""
    # First try to use saved session
    if auth_manager.is_authenticated:
        saved_session = auth_manager.session_manager.load_session()
        if saved_session:
            typer.echo(typer.style(f"Already logged in as {saved_session['user_name']}!", fg=typer.colors.GREEN))
            return

    typer.echo(typer.style("To login, you'll need your LEETCODE_SESSION token:", fg=typer.colors.YELLOW))
    typer.echo("\n1. Open LeetCode in your browser")
    typer.echo("2. Press F12 to open Developer Tools")
    typer.echo("3. Go to Application tab > Cookies > leetcode.com")
    typer.echo("4. Find and copy the 'LEETCODE_SESSION' value\n")

    leetcode_session = typer.prompt("Please enter your LEETCODE_SESSION token")

    result = auth_manager.login_with_session(leetcode_session)

    if result["success"]:
        typer.echo(typer.style(f"\n✓ Successfully logged in as {result['user_name']}!", fg=typer.colors.GREEN))
    else:
        typer.echo(typer.style(f"\n✗ Login failed: {result['message']}", fg=typer.colors.RED))
