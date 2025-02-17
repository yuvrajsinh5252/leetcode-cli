import typer

def show(problem_id: int):
    """Show details of a specific problem."""
    typer.echo(f"Fetching details for problem {problem_id}...")
