import typer
from rich.console import Console

console = Console()


def get_leetcode_ascii():
    """Return LeetCode ASCII art"""
    return """
        |  _  _ |- _   | _
        |_(/_(/_|_(_()(|(/_
    """


def display_welcome(app: typer.Typer):
    """Display welcome screen with ASCII art and command list"""
    console.print(get_leetcode_ascii())
    console.print("      Welcome to LeetCode CLI", style="bold")
