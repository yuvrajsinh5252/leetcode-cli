from typing import Any, Dict, List, Optional, Tuple

import typer
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..server.config import STATUS_CODES

console = Console()


def display_auth_error():
    """Display error message when not authenticated"""
    console.print(
        Panel(
            "❌ Please login first using the login command",
            style="bold red",
            border_style="red",
        )
    )
    raise typer.Exit(1)


def display_file_not_found_error(file):
    """Display error message when file is not found"""
    console.print(
        Panel(f"❌ File not found: {file}", style="bold red", border_style="red")
    )
    raise typer.Exit(1)


def display_language_detection_message(lang):
    """Display auto-detected language message"""
    console.print(f"🔍 Auto-detected language: [cyan]{lang}[/]")


def display_language_detection_error(extension):
    """Display error message when language cannot be detected"""
    console.print(
        Panel(
            f"❌ Could not detect language for {extension} files. Please specify with --lang",
            style="bold red",
            border_style="red",
        )
    )
    raise typer.Exit(1)


def display_problem_not_found_error(problem):
    """Display error message when problem is not found"""
    console.print(
        Panel(f"❌ Problem not found: {problem}", style="bold red", border_style="red")
    )
    raise typer.Exit(1)


def display_submission_details(problem, problem_name, lang, file):
    """Display submission details and confirmation prompt using a clean layout"""
    content = [
        f"[cyan]Problem:[/] {problem} - {problem_name}",
        f"[cyan]Language:[/] {lang}",
        f"[cyan]File:[/] {str(file)}",
    ]

    console.print(
        Panel(
            "\n".join(content),
            title="Submission Details",
            border_style="blue",
            box=box.ROUNDED,
        )
    )

    return typer.confirm("Do you want to submit this solution?")


def display_submission_canceled():
    """Display submission canceled message"""
    console.print("[yellow]Submission canceled[/]")


def create_submission_progress():
    """Create and return a submission progress context"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


def display_submission_results(result: Dict[str, Any], is_test: bool = False):
    """Display submission results with a cleaner layout"""
    status_code = result.get("status_code")

    # Determine status and success based on result type
    status, run_success = _determine_status(result, is_test)

    # Get styling for the status display
    status_style, border_style, emoji = _get_status_styling(
        status, status_code, run_success, is_test, result
    )

    # Format metrics and build display content
    content_parts = _build_content_parts(result, status, run_success, status_style)

    # Display the main result panel
    title = f"{emoji} {'Test' if is_test else 'Submission'} Result"
    console.print(
        Panel(
            "\n".join(content_parts),
            title=title,
            title_align="center",
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    # Display additional details based on status
    _display_error_details(result, status, status_code)
    _display_memory_warning(result)
    _display_stdout(result)
    _display_output_comparison(result, status, run_success)
    _display_general_error(result, run_success, status)


def _determine_status(result: Dict[str, Any], is_test: bool) -> Tuple[str, bool]:
    """Determine status and success based on result type"""
    if is_test:
        correct_answer = result.get("correct_answer", None)
        if correct_answer is False:
            return "Wrong Answer", False

        run_success = result.get("run_success", result.get("success", False))
        if run_success:
            return "Accepted", True
        return result.get("status_msg", result.get("status", "Unknown")), run_success
    else:
        status_code = result.get("status_code")
        if status_code in STATUS_CODES:
            status = STATUS_CODES[status_code]
        else:
            status = result.get("status", result.get("status_msg", "Unknown"))
        return status, result.get("run_success", result.get("success", False))


def _get_status_styling(
    status: str,
    status_code: Optional[int],
    run_success: bool,
    is_test: bool,
    result: Dict[str, Any],
) -> Tuple[str, str, str]:
    """Get the styling for status display"""
    if is_test and result.get("correct_answer") is False:
        return "bold red", "red", "❌"
    elif (status_code == 10 or status == "Accepted") and run_success:
        return "bold green", "green", "✅"
    elif status_code in [14, 15] or status in ["Runtime Error", "Time Limit Exceeded"]:
        return "bold yellow", "yellow", "⚠️"
    elif status_code in [12, 13]:  # Memory/Output Limit Exceeded
        return "bold yellow", "yellow", "⚠️"
    elif status_code == 20 or status == "Compile Error":
        return "bold red", "red", "❌"
    elif status_code == 11:  # Wrong Answer
        return "bold red", "red", "❌"
    elif status_code in [16, 30]:  # Internal Error, Timeout
        return "bold red", "red", "⚠️"
    else:
        return "bold red", "red", "❌"


def _build_content_parts(
    result: Dict[str, Any], status: str, run_success: bool, status_style: str
) -> List[str]:
    """Build content parts for the main display panel"""
    # Format runtime and memory metrics
    runtime = result.get("status_runtime", result.get("runtime", "N/A"))
    memory = result.get("status_memory", result.get("memory", "N/A"))

    if isinstance(memory, int):
        memory = f"{memory / 1000000:.2f} MB"

    memory_warning = None
    memory_value = result.get("memory", 0)
    if isinstance(memory_value, int) and memory_value > 200000000:
        memory_warning = " [bold yellow](!)[/]"
    else:
        memory_warning = ""

    # Build content parts
    content_parts = [
        f"📊 [bold cyan]Status:[/] [{status_style}]{status}[/]\n",
        f"[bold cyan]🕒 Runtime:[/] {runtime}",
        f"[bold cyan]📝 Memory:[/] {memory}{memory_warning}",
    ]

    if result.get("elapsed_time"):
        content_parts.append(f"⌛ [bold cyan]Time:[/] {result.get('elapsed_time')} ms")

    # Test case statistics
    content_parts.append(f"🧪 [bold cyan]Tests:[/] {_format_test_case_stats(result)}")

    # Performance indicator
    if status == "Accepted" and run_success:
        runtime_str = str(runtime).lower()
        if "beats" in runtime_str or "percentile" in runtime_str:
            content_parts.append("[bold green]🚀 Great performance![/]")

    return content_parts


def _format_test_case_stats(result: Dict[str, Any]) -> str:
    """Format test case statistics"""
    passed = result.get("total_correct", 0)
    total = result.get("total_testcases", 0)

    if not total:
        return "N/A"

    percentage = (passed / total) * 100
    stats = f"{passed}/{total} ({percentage:.1f}%)"

    if percentage == 100:
        return f"[bold green]{stats}[/]"
    elif percentage >= 80:
        return f"[bold yellow]{stats}[/]"
    else:
        return f"[bold red]{stats}[/]"


def _display_error_details(
    result: Dict[str, Any], status: str, status_code: Optional[int]
) -> None:
    """Display error details based on status"""
    if status == "Compile Error" or status_code == 20:
        error_msg = result.get(
            "compile_error", result.get("error", "No details available")
        )
        full_error = result.get("full_compile_error", result.get("full_error", ""))

        if error_msg:
            console.print(
                Panel(
                    f"[red]{error_msg}[/]",
                    title="⛔ Compilation Error",
                    border_style="red",
                    box=box.ROUNDED,
                    padding=(1, 1),
                )
            )

        if full_error and full_error != error_msg:
            console.print(
                Panel(
                    f"[dim]{full_error}[/]",
                    title="Full Compilation Error",
                    border_style="red",
                    box=box.ROUNDED,
                    padding=(1, 1),
                )
            )

    elif status == "Runtime Error" or status_code == 15:
        error_msg = result.get(
            "runtime_error", result.get("error", "No details available")
        )
        full_error = result.get("full_runtime_error", result.get("full_error", ""))

        if error_msg:
            console.print(
                Panel(
                    f"[yellow]{error_msg}[/]",
                    title="⚠️ Runtime Error",
                    border_style="yellow",
                    box=box.ROUNDED,
                    padding=(1, 1),
                )
            )

        if full_error and full_error != error_msg:
            console.print(
                Panel(
                    f"[dim]{full_error}[/]",
                    title="Full Error Trace",
                    border_style="yellow",
                    box=box.ROUNDED,
                    padding=(1, 1),
                )
            )


def _display_memory_warning(result: Dict[str, Any]) -> None:
    """Display memory warning if needed"""
    memory_value = result.get("memory", 0)
    if isinstance(memory_value, int) and memory_value > 200000000:
        warning = f"Your solution is using a large amount of memory ({memory_value / 1000000:.2f} MB). Consider optimizing to reduce memory usage."
        console.print(
            Panel(
                f"[yellow]{warning}[/]",
                title="⚠️ Memory Usage Warning",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 1),
            )
        )


def _display_stdout(result: Dict[str, Any]) -> None:
    """Display standard output if available"""
    stdout_lines = []

    if result.get("std_output_list"):
        current_test_case = []
        for line in result.get("std_output_list", []):
            if line and line.strip():
                current_test_case.append(line.rstrip())
            elif current_test_case:
                stdout_lines.extend(current_test_case)
                current_test_case = []

        if current_test_case:
            stdout_lines.extend(current_test_case)

    if stdout_lines:
        console.print(
            Panel(
                "\n".join(stdout_lines),
                title="📝 Standard Output",
                border_style="blue",
                box=box.ROUNDED,
                padding=(1, 1),
            )
        )
    elif result.get("stdout") and result.get("stdout", "").strip():
        console.print(
            Panel(
                result.get("stdout", "").strip(),
                title="📝 Standard Output",
                border_style="blue",
                box=box.ROUNDED,
                padding=(1, 1),
            )
        )


def _display_output_comparison(
    result: Dict[str, Any], status: str, run_success: bool
) -> None:
    """Display output comparison when available"""
    is_wrong_answer = status == "Wrong Answer" or (
        not run_success
        and status not in ["Compile Error", "Runtime Error", "Time Limit Exceeded"]
    )

    if result.get("code_answer") and result.get("expected_code_answer"):
        output_lines = [
            line for line in result.get("code_answer", []) if line and line.strip()
        ]
        expected_lines = [
            line
            for line in result.get("expected_code_answer", [])
            if line and line.strip()
        ]

        if output_lines or expected_lines:
            output = "\n".join(output_lines)
            expected = "\n".join(expected_lines)

            output_panel = Panel(
                output,
                title="🔍 Your Output",
                border_style="red" if is_wrong_answer else "blue",
                padding=(1, 1),
            )
            expected_panel = Panel(
                expected,
                title="✓ Expected Output",
                border_style="green",
                padding=(1, 1),
            )

            if is_wrong_answer:
                console.print(
                    Panel(
                        "[bold red]Output does not match expected result[/]",
                        title="❌ Wrong Answer",
                        border_style="red",
                        padding=(0, 1),
                    )
                )

            console.print(Columns([output_panel, expected_panel]))

    elif result.get("output") or result.get("expected"):
        output = (result.get("output", "") or "").strip()
        expected = (result.get("expected", "") or "").strip()

        if is_wrong_answer:
            console.print(
                Panel(
                    "[bold red]Output does not match expected result[/]",
                    title="❌ Wrong Answer",
                    border_style="red",
                    padding=(0, 1),
                )
            )

        output_panel = Panel(
            output,
            title="🔍 Your Output",
            border_style="red" if is_wrong_answer else "blue",
            padding=(1, 1),
        )
        expected_panel = Panel(
            expected,
            title="✓ Expected Output",
            border_style="green",
            padding=(1, 1),
        )
        console.print(Columns([output_panel, expected_panel]))


def _display_general_error(
    result: Dict[str, Any], run_success: bool, status: str
) -> None:
    """Display general error information if needed"""
    if (
        not run_success
        and status not in ["Compile Error", "Runtime Error"]
        and result.get("error")
    ):
        error_msg = result.get("error", "No details available")
        console.print(
            Panel(
                f"[red]{error_msg}[/]",
                title="⛔ Error Details",
                border_style="red",
                padding=(1, 1),
            )
        )

        if result.get("full_error") and result.get("full_error") != error_msg:
            console.print(
                Panel(
                    f"[dim]{result.get('full_error', '')}[/]",
                    title="Full Error Trace",
                    border_style="red",
                    box=box.ROUNDED,
                    padding=(1, 1),
                )
            )


def display_exception_error(e):
    """Display exception error message"""
    console.print(Panel(f"❌ Error: {str(e)}", style="bold red", border_style="red"))
    raise typer.Exit(1)
