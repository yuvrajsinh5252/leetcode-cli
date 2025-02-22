from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from datetime import datetime

import typer

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

def display_user_stats(data):
    console.clear()
    console.print("\n")

    if not data.get('userProfile'):
        console.print(Panel("Could not fetch user profile", border_style="red"))
        return

    user = data['userProfile']['matchedUser']
    profile = user['profile']

    # Display basic profile info
    profile_table = Table.grid(padding=(0, 2))
    profile_table.add_column(justify="left")

    profile_info = [
        f"[bold cyan]{user['username']}[/bold cyan]",
        f"[dim]Ranking:[/dim] {profile['ranking']}",
        f"[dim]Company:[/dim] {profile['company'] or 'Not specified'}",
        f"[dim]Location:[/dim] {profile['countryName'] or 'Not specified'}"
    ]

    if profile['skillTags']:
        skills = ", ".join(profile['skillTags'])
        profile_info.append(f"[dim]Skills:[/dim] {skills}")

    profile_table.add_row("\n".join(profile_info))
    console.print(Panel(profile_table, title="[bold cyan]Profile Info[/bold cyan]", border_style="cyan"))
    console.print("\n")

    # Display contest info if available
    if data.get('contestInfo') and data['contestInfo'].get('userContestRanking'):
        contest = data['contestInfo']['userContestRanking']
        contest_table = Table.grid(padding=(0, 2))
        contest_table.add_column(justify="left")
        contest_table.add_row(
            f"Rating: [yellow]{contest['rating']}[/yellow]\n"
            f"Global Rank: {contest['globalRanking']}/{contest['totalParticipants']}\n"
            f"Top: {contest['topPercentage']}%\n"
            f"Contests: {contest['attendedContestsCount']}"
        )
        console.print(Panel(contest_table, title="[bold yellow]Contest Stats[/bold yellow]", border_style="yellow"))
        console.print("\n")

    # Display progress
    if data.get('progress'):
        progress = data['progress']
        console.print(create_profile_header(progress))
        console.print("\n")

    # Display language stats
    if data.get('languageStats'):
        lang_stats = data['languageStats']['matchedUser']['languageProblemCount']
        lang_table = Table(title="Languages", box=box.ROUNDED, border_style="cyan")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Problems Solved", justify="right")

        for lang in sorted(lang_stats, key=lambda x: x['problemsSolved'], reverse=True)[:5]:
            lang_table.add_row(
                lang['languageName'],
                str(lang['problemsSolved'])
            )
        console.print(lang_table)
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