from typing import Any, Dict
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
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
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )

def display_submission_results(result: Dict[str, Any], is_test: bool = False):
    """Display submission results with a cleaner layout"""
    status_code = result.get('status_code')
    status = result.get('status', result.get('status_msg', 'Unknown'))
    run_success = result.get('run_success', result.get('success', False))

    if status == "Accepted" and run_success:
        status_style = "bold green"
        border_style = "green"
        emoji = "✅"
    elif status in ["Runtime Error", "Time Limit Exceeded"] or status_code in [14, 15]:
        status_style = "bold yellow"
        border_style = "yellow"
        emoji = "⚠️"
    elif status == "Compile Error" or status_code == 20:
        status_style = "bold red"
        border_style = "red"
        emoji = "❌"
    else:
        status_style = "bold red"
        border_style = "red"
        emoji = "❌"

    runtime = result.get('status_runtime', result.get('runtime', 'N/A'))
    memory = result.get('status_memory', result.get('memory', 'N/A'))

    if isinstance(memory, int):
        memory = f"{memory / 1000000:.1f} MB"

    memory_warning = None
    if isinstance(result.get('memory'), int):
        memory_value = result.get('memory', 0)
        if memory_value > 200000000:
            memory_warning = f"Your solution is using a large amount of memory ({memory_value/1000000:.1f} MB). Consider optimizing to reduce memory usage."

    if memory_warning:
        memory = f"{memory} [bold yellow](!)[/]"

    passed = result.get('total_correct', 0)
    total = result.get('total_testcases', 0)

    test_case_str = "N/A"
    if total and total > 0:
        percentage = (passed / total) * 100
        test_case_str = f"{passed}/{total} ({percentage:.1f}%)"

    content_parts = []
    content_parts.append(f"[cyan]⏱️ Runtime:[/] {runtime}")
    content_parts.append(f"[cyan]💾 Memory:[/] {memory}")

    if result.get('elapsed_time'):
        content_parts.append(f"[cyan]⏲️ Elapsed Time:[/] {result.get('elapsed_time')} ms")

    content_parts.append(f"[cyan]🧪 Test Cases:[/] {test_case_str}")
    content_string = "\n".join(content_parts)

    title = f"{emoji} {'Test' if is_test else 'Submission'} Result: [{status_style}]{status}[/]"
    console.print(Panel(
        content_string,
        title=title,
        border_style=border_style,
        box=box.ROUNDED,
        padding=(0, 10)
    ))

    # Display specific error messages
    if status == "Compile Error" or status_code == 20:
        error_msg = result.get('compile_error', result.get('error', 'No details available'))
        full_error = result.get('full_compile_error', result.get('full_error', ''))

        if error_msg:
            console.print(Panel(
                error_msg,
                title="Compilation Error",
                border_style="red",
                box=box.ROUNDED,
                padding=(0, 1)
            ))

        if full_error:
            console.print(Panel(
                full_error,
                title="Full Compilation Error",
                border_style="red",
                box=box.ROUNDED,
                padding=(0, 1)
            ))

    elif status == "Runtime Error" or status_code == 15:
        error_msg = result.get('runtime_error', result.get('error', 'No details available'))
        full_error = result.get('full_runtime_error', result.get('full_error', ''))

        if error_msg:
            console.print(Panel(
                error_msg,
                title="Runtime Error",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(0, 1)
            ))

        if full_error:
            console.print(Panel(
                full_error,
                title="Full Error Trace",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(0, 1)
            ))

    # Display memory warning if present
    if memory_warning:
        console.print(Panel(
            memory_warning,
            title="⚠️ Memory Usage Warning",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 1)
        ))

    stdout_lines = []
    if result.get('std_output_list'):
        current_test_case = []
        for line in result.get('std_output_list', []):
            if line and line.strip():
                current_test_case.append(line.rstrip())
            elif current_test_case:
                stdout_lines.extend(current_test_case)
                current_test_case = []

        if current_test_case:
            stdout_lines.extend(current_test_case)

    if stdout_lines:
        console.print(Panel(
            "\n".join(stdout_lines),
            title="📝 Standard Output",
            border_style="blue",
            box=box.ROUNDED,
            padding=(0, 1)
        ))
    elif result.get('stdout') and result.get('stdout', '').strip():
        console.print(Panel(
            result.get('stdout', '').strip(),
            title="📝 Standard Output",
            border_style="blue",
            box=box.ROUNDED,
            padding=(0, 1)
        ))

    if result.get('code_answer') and result.get('expected_code_answer'):
        output_lines = [line for line in result.get('code_answer', []) if line and line.strip()]
        expected_lines = [line for line in result.get('expected_code_answer', []) if line and line.strip()]

        if output_lines or expected_lines:
            output = "\n".join(output_lines)
            expected = "\n".join(expected_lines)

            is_wrong_answer = status == "Wrong Answer" or (not run_success and not (status in ["Compile Error", "Runtime Error", "Time Limit Exceeded"]))

            output_panel = Panel(
                output,
                title="Your Output",
                border_style="red" if is_wrong_answer else "blue",
                padding=(0, 1)
            )
            expected_panel = Panel(
                expected,
                title="Expected Output",
                border_style="green",
                padding=(0, 1)
            )
            console.print(Columns([output_panel, expected_panel]))
    elif result.get('output') or result.get('expected'):
        output = (result.get('output', '') or '').strip()
        expected = (result.get('expected', '') or '').strip()

        is_wrong_answer = status == "Wrong Answer" or (not run_success and not (status in ["Compile Error", "Runtime Error", "Time Limit Exceeded"]))

        output_panel = Panel(
            output,
            title="Your Output",
            border_style="red" if is_wrong_answer else "blue",
            padding=(0, 1)
        )
        expected_panel = Panel(
            expected,
            title="Expected Output",
            border_style="green",
            padding=(0, 1)
        )
        console.print(Columns([output_panel, expected_panel]))

    if not run_success and status not in ["Compile Error", "Runtime Error"] and result.get('error'):
        error_msg = result.get('error', 'No details available')
        console.print(Panel(
            error_msg,
            title="Error Details",
            border_style="red",
            padding=(0, 1)
        ))

        if result.get('full_error'):
            console.print(Panel(
                result.get('full_error', ''),
                title="Full Error Trace",
                border_style="red",
                box=box.ROUNDED,
                padding=(0, 1)
            ))

def display_exception_error(e):
    """Display exception error message"""
    console.print(Panel(f"❌ Error: {str(e)}", style="bold red", border_style="red"))
    raise typer.Exit(1)