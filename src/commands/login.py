import typer


def login():
    """Login to LeetCode"""
    from ..server.auth import Auth

    auth_manager = Auth()

    if auth_manager.is_authenticated:
        saved_session = auth_manager.session_manager.load_session()
        if saved_session:
            typer.echo(
                typer.style(
                    f"Already logged in as {saved_session['user_name']}!",
                    fg=typer.colors.GREEN,
                )
            )
            return

    instruction = """
                    📝 To get your login tokens:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1️  Open LeetCode in your browser
    2️  Press F12 to open Developer Tools
    3️  Go to Application tab → Cookies → leetcode.com
    4️  Find and copy both 'csrftoken' and 'LEETCODE_SESSION'
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """

    typer.echo(typer.style(instruction, fg=typer.colors.BRIGHT_BLACK))

    while True:
        csrf_token = typer.prompt("Please enter your CSRF token")
        csrf_result = auth_manager.verify_csrf_token(csrf_token)

        if not csrf_result["success"]:
            typer.echo(
                typer.style(
                    f"\n✗ CSRF verification failed: {csrf_result['message']}",
                    fg=typer.colors.RED,
                )
            )
            return

        leetcode_session = typer.prompt("Please enter your LEETCODE_SESSION token")
        result = auth_manager.login_with_session(csrf_token, leetcode_session)

        if result["success"]:
            typer.echo(
                typer.style(
                    f"\n✓ Successfully logged in as {result['user_name']}!",
                    fg=typer.colors.GREEN,
                )
            )
            break
        else:
            typer.echo(
                typer.style(
                    f"\n✗ Login failed: {result['message']}", fg=typer.colors.RED
                )
            )
            if not typer.confirm("Do you want to try again?", abort=True):
                break


def logout():
    """Logout from LeetCode"""

    from ..server.auth import Auth

    auth_manager = Auth()

    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ You are not logged in", fg=typer.colors.RED))
        return

    auth_manager.session_manager.clear_session()
    typer.echo(typer.style("✓ Successfully logged out", fg=typer.colors.GREEN))
