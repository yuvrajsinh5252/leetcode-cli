from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich import box
from rich.text import Text
from rich.columns import Columns
import typer

console = Console()

def display_auth_error():
    """Display error message when not authenticated"""
    console.print(Panel("❌ Please login first using the login command",
                      style="bold red", border_style="red"))
    raise typer.Exit(1)

def display_file_not_found_error(file):
    """Display error message when file is not found"""
    console.print(Panel(f"❌ File not found: {file}", style="bold red", border_style="red"))
    raise typer.Exit(1)

def display_language_detection_message(lang):
    """Display auto-detected language message"""
    console.print(f"🔍 Auto-detected language: [cyan]{lang}[/]")

def display_language_detection_error(extension):
    """Display error message when language cannot be detected"""
    console.print(Panel(f"❌ Could not detect language for {extension} files. Please specify with --lang",
                      style="bold red", border_style="red"))
    raise typer.Exit(1)

def display_problem_not_found_error(problem):
    """Display error message when problem is not found"""
    console.print(Panel(f"❌ Problem not found: {problem}", style="bold red", border_style="red"))
    raise typer.Exit(1)

def display_submission_details(problem, problem_name, lang, file):
    """Display submission details and confirmation prompt using a clean layout"""
    # Create formatted text lines instead of a nested table
    content = [
        f"[cyan]Problem:[/] {problem} - {problem_name}",
        f"[cyan]Language:[/] {lang}",
        f"[cyan]File:[/] {str(file)}"
    ]

    console.print(Panel(
        "\n".join(content),
        title="Submission Details",
        border_style="blue",
        box=box.ROUNDED
    ))

    return typer.confirm("Do you want to submit this solution?")

def display_submission_canceled():
    """Display submission canceled message"""
    console.print("[yellow]Submission canceled[/]")
    raise typer.Exit(0)

def create_submission_progress():
    """Create and return a submission progress context"""
    return Progress(
        TextColumn("[bold yellow]Submitting solution...", justify="right"),
        BarColumn(bar_width=40, style="yellow"),
        transient=True,
    )

def display_submission_results(result):
    """Display submission results with a cleaner layout"""
    if result["success"]:
        status = result['status']

        # Set colors based on status
        if status == "Accepted":
            status_style = "bold green"
            border_style = "green"
            emoji = "✅"
        elif status in ["Runtime Error", "Time Limit Exceeded"]:
            status_style = "bold yellow"
            border_style = "yellow"
            emoji = "⚠️"
        else:
            status_style = "bold red"
            border_style = "red"
            emoji = "❌"

        # Get metrics
        runtime = result.get('runtime', 'N/A')
        memory = result.get('memory', 'N/A')
        passed = result.get('passed_testcases', 0)
        total = result.get('total_testcases', 0)
        test_case_str = f"{passed}/{total} ({passed/total*100:.1f}%)" if total > 0 else "N/A"

        content = [
            f"[cyan]⏱️ Runtime:[/] {runtime}",
            f"[cyan]💾 Memory:[/] {memory}",
            f"[cyan]🧪 Test Cases:[/] {test_case_str}"
        ]

        title = f"{emoji} Submission Result: [{status_style}]{status}[/]"
        console.print(Panel(
            "\n".join(content),
            title=title,
            border_style=border_style,
            box=box.ROUNDED
        ))

        if status != "Accepted" and result.get('error_message'):
            error_msg = result.get('error_message', 'No details available')
            console.print(Panel(error_msg, title="Error Details", border_style="red"))
    else:
        error_panel = Panel(
            f"{result.get('error', 'Unknown error')}",
            title="❌ Submission Failed",
            border_style="red"
        )
        console.print(error_panel)

def display_exception_error(e):
    """Display exception error message"""
    console.print(Panel(f"❌ Error: {str(e)}", style="bold red", border_style="red"))
    raise typer.Exit(1)