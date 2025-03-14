import typer


def solutions(
    problem: str = typer.Argument(
        ..., help="Problem slug or number (e.g., 'two-sum' or '1')"
    ),
    best: bool = typer.Option(
        False, "--best", "-b", help="Show the best solution for the problem"
    ),
):
    """Fetch solution for a problem"""
    pass
