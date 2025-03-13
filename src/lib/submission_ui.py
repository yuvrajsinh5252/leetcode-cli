from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich import box
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

        runtime = result.get('runtime', 'N/A')
        memory = result.get('memory', 'N/A')

        memory_warning = result.get('memory_warning')
        if memory_warning:
            memory = f"{memory} [bold yellow](!)[/]"

        passed = result.get('passed_testcases', 0)
        total = result.get('total_testcases', 0)
        test_case_str = f"{passed}/{total} ({passed/total*100:.1f}%)" if total > 0 else "N/A"

        content = [
            f"[cyan]⏱️ Runtime:[/] {runtime}",
            f"[cyan]💾 Memory:[/] {memory}"
        ]

        if result.get('elapsed_time'):
            content.append(f"[cyan]⏲️ Elapsed Time:[/] {result.get('elapsed_time')} ms")

        content.append(f"[cyan]🧪 Test Cases:[/] {test_case_str}")

        title = f"{emoji} Submission Result: [{status_style}]{status}[/]"
        console.print(Panel(
            "\n".join(content),
            title=title,
            border_style=border_style,
            box=box.ROUNDED
        ))

        if memory_warning:
            console.print(Panel(
                memory_warning,
                title="⚠️ Memory Usage Warning",
                border_style="yellow",
                box=box.ROUNDED
            ))

        if result.get('stdout'):
            console.print(Panel(
                result.get('stdout'),
                title="📝 Standard Output",
                border_style="blue",
                box=box.ROUNDED
            ))

        if result.get('output') and result.get('expected'):
            is_wrong_answer = status == "Wrong Answer"

            output_panel = Panel(
                result.get('output', ''),
                title="Your Output",
                border_style="red" if is_wrong_answer else "blue"
            )
            expected_panel = Panel(
                result.get('expected', ''),
                title="Expected Output",
                border_style="green"
            )
            console.print(Columns([output_panel, expected_panel]))

        if status != "Accepted" and result.get('error'):
            error_msg = result.get('error', 'No details available')
            console.print(Panel(error_msg, title="Error Details", border_style="red"))

            if result.get('full_error'):
                console.print(Panel(
                    result.get('full_error', ''),
                    title="Full Error Trace",
                    border_style="red",
                    box=box.ROUNDED
                ))
    else:
        error_panel = Panel(
            f"{result.get('error', 'Unknown error')}",
            title="❌ Submission Failed",
            border_style="red"
        )
        console.print(error_panel)

        if result.get('stdout'):
            console.print(Panel(
                result.get('stdout'),
                title="📝 Standard Output",
                border_style="blue",
                box=box.ROUNDED
            ))

        if result.get('full_error'):
            console.print(Panel(
                result.get('full_error', ''),
                title="Full Error Trace",
                border_style="red",
                box=box.ROUNDED
            ))

def display_exception_error(e):
    """Display exception error message"""
    console.print(Panel(f"❌ Error: {str(e)}", style="bold red", border_style="red"))
    raise typer.Exit(1)