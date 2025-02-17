import typer
from server.api import fetch_problem_list

def list():
    """List all available LeetCode problems."""
    typer.echo("Fetching problem list...")
    data = fetch_problem_list()

    for problem in data:
        typer.echo(f"{problem['questionFrontendId']}. {problem['title']}")
        typer.echo(f"Difficulty: {problem['difficulty']}")
        tags = ", ".join(tag["name"] for tag in problem["topicTags"])
        typer.echo(f"Tags: {tags}")
        typer.echo()
