import typer
from src.server.auth import Auth

auth_manager = Auth()

def login():
    """Login to LeetCode"""
    if auth_manager.is_authenticated:
        saved_session = auth_manager.session_manager.load_session()
        if saved_session:
            typer.echo(typer.style(f"Already logged in as {saved_session['user_name']}!", fg=typer.colors.GREEN))
            return

    typer.echo(typer.style("To login, you'll need both CSRF and LEETCODE_SESSION tokens:", fg=typer.colors.YELLOW))
    typer.echo("\n1. Open LeetCode in your browser")
    typer.echo("2. Press F12 to open Developer Tools")
    typer.echo("3. Go to Application tab > Cookies > leetcode.com")
    typer.echo("4. Find and copy both 'csrftoken' and 'LEETCODE_SESSION' values\n")

    csrf_token = typer.prompt("Please enter your CSRF token")
    csrf_result = auth_manager.verify_csrf_token(csrf_token)

    if not csrf_result["success"]:
        typer.echo(typer.style(f"\n✗ CSRF verification failed: {csrf_result['message']}", fg=typer.colors.RED))
        return

    leetcode_session = typer.prompt("Please enter your LEETCODE_SESSION token")
    result = auth_manager.login_with_session(csrf_token, leetcode_session)

    if result["success"]:
        typer.echo(typer.style(f"\n✓ Successfully logged in as {result['user_name']}!", fg=typer.colors.GREEN))
    else:
        typer.echo(typer.style(f"\n✗ Login failed: {result['message']}", fg=typer.colors.RED))

def logout():
    """Logout from LeetCode"""
    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ You are not logged in", fg=typer.colors.RED))
        return

    auth_manager.session_manager.clear_session()
    typer.echo(typer.style("✓ Successfully logged out", fg=typer.colors.GREEN))