from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from datetime import datetime

console = Console()

def format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")

def create_recent_activity(recent_submissions):
    if not recent_submissions:
        return None

    table = Table(
        title="Recent Submissions",
        box=box.ROUNDED,
        border_style="cyan",
        pad_edge=False,
        show_edge=True
    )

    table.add_column("Time", style="dim", width=16)
    table.add_column("Problem", style="cyan")
    table.add_column("Status", justify="center", width=8)

    for sub in recent_submissions[:5]:  # Show last 5 submissions
        status_icon = "[green]✓" if sub['statusDisplay'] == "Accepted" else "[red]✗"
        table.add_row(
            format_timestamp(sub['timestamp']),
            sub['title'],
            status_icon
        )

    return table

def create_profile_header(data):
    username = data.get('matchedUser', {}).get('username', 'Leetcoder')
    user_data = data.get('matchedUser', {})
    solved = user_data.get('submitStatsGlobal', {}).get('acSubmissionNum', [])

    table = Table.grid(padding=(0, 2))
    table.add_column(justify="left", width=130)
    table.add_column(justify="left", width=45)

    # Calculate stats
    total_solved = next((item['count'] for item in solved if item['difficulty'] == 'All'), 0)
    total_problems = next((item['count'] for item in data['allQuestionsCount'] if item['difficulty'] == 'All'), 0)
    solve_percentage = (total_solved / total_problems) * 100 if total_problems > 0 else 0

    # Left column - compact formatting
    profile_text = (
        f"[bold cyan]{username}[/bold cyan]\n"
        f"Solved: [cyan]{total_solved}[/cyan]/[cyan]{total_problems}[/cyan]\n"
        f"[dim]({solve_percentage:.1f}%)[/dim]"
    )

    # Right column - clean difficulty stats
    difficulties = ['Easy', 'Medium', 'Hard']
    colors = ['green', 'yellow', 'red']
    stats_text = []

    for diff, color in zip(difficulties, colors):
        solved_count = next((item['count'] for item in solved if item['difficulty'] == diff), 0)
        total_count = next((item['count'] for item in data['allQuestionsCount'] if item['difficulty'] == diff), 0)
        percentage = (solved_count / total_count) * 100 if total_count > 0 else 0

        dots = "●" * int(percentage/10) + "○" * (10 - int(percentage/10))
        stats_text.append(
            f"[{color}]{diff:<6} {solved_count:>3}/{total_count:<4} {dots} {percentage:>5.1f}%[/{color}]"
        )

    table.add_row(
        profile_text,
        "\n".join(stats_text)
    )

    return Panel(
        table,
        border_style="cyan",
        padding=(1, 2),
        title="[bold cyan]LeetCode Profile[/bold cyan]"
    )

def display_problem_stats(data):
    console.clear()
    console.print("\n")

    # Display profile header
    console.print(create_profile_header(data))
    console.print("\n")

    # Display recent submissions
    recent_submissions = data.get('matchedUser', {}).get('recentSubmissionList', [])
    if recent_submissions:
        recent_activity = create_recent_activity(recent_submissions)
        if recent_activity:
            console.print(recent_activity)
    else:
        console.print(Panel("No recent activity", border_style="cyan"))

    console.print("\n")

def display_problem_list(data):
    console.clear()
    console.print("\n")

    table = Table(
        title="Problem List",
        box=box.ROUNDED,
        border_style="cyan",
        pad_edge=False,
        show_edge=True
    )

    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", style="cyan")
    table.add_column("Difficulty", justify="center", width=10)
    table.add_column("Status", justify="center", width=8)
    table.add_column("AC Rate", justify="right", width=8)

    for problem in data['problemsetQuestionList']['questions']:
        status_icon = "[green]✓" if problem['status'] == "ac" else "[red]✗"
        ac_rate = f"{problem['acRate']:.1f}%"
        table.add_row(
            problem['frontendQuestionId'],
            problem['title'],
            problem['difficulty'],
            status_icon,
            ac_rate
        )

    console.print(table)
    console.print("\n")