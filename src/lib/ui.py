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
    if not recent_submissions or 'recentAcSubmissionList' not in recent_submissions:
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

    for sub in recent_submissions['recentAcSubmissionList'][:5]:
        table.add_row(
            format_timestamp(int(sub['timestamp'])),
            sub['title'],
            "[green]✓"
        )

    return table

def display_user_stats(data):
    console.clear()
    width = min(console.width - 4, 150)  # Limit max width
    first_width = width // 3 - 2
    second_width = (width * 2) // 3 - 2

    if not data.get('userProfile'):
        console.print(Panel("Could not fetch user profile", border_style="red"))
        return

    user = data['userProfile']['matchedUser']
    profile = user['profile']

    # Create main profile info
    profile_table = Table.grid(padding=(0, 1))
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

    # Create contest stats if available
    contest_panel = None
    if data.get('contestInfo') and data['contestInfo'].get('userContestRanking'):
        contest = data['contestInfo']['userContestRanking']
        contest_table = Table.grid(padding=(0, 1))
        contest_table.add_column(justify="left")
        contest_table.add_row(
            f"[yellow]Rating: {contest['rating']}[/yellow]\n"
            f"Global Rank: {contest['globalRanking']}\n"
            f"Top: {contest['topPercentage']}%\n"
            f"Contests: {contest['attendedContestsCount']}"
        )
        contest_panel = Panel(
            contest_table,
            title="[bold yellow]Contest Stats[/bold yellow]",
            border_style="yellow",
            width=second_width
        )

    # Create top row grid
    top_grid = Table.grid(padding=(0, 2))
    top_grid.add_column(width=first_width)
    top_grid.add_column(width=second_width)
    top_grid.add_row(
        Panel(profile_table, title="[bold cyan]Profile Info[/bold cyan]", border_style="cyan"),
        contest_panel or ""
    )
    console.print("\n")
    console.print(top_grid)
    console.print("\n")

    # Create bottom row grid
    bottom_grid = Table.grid(padding=(0, 2))
    bottom_grid.add_column(width=first_width)
    bottom_grid.add_column(width=second_width)

    # Language stats
    lang_panel = None
    if data.get('languageStats'):
        lang_stats = data['languageStats']['matchedUser']['languageProblemCount']
        lang_table = Table(
            title="[bold cyan]Languages[/bold cyan]",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 1),
            width=first_width
        )
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Solved", justify="right")

        for lang in sorted(lang_stats, key=lambda x: x['problemsSolved'], reverse=True)[:5]:
            lang_table.add_row(
                lang['languageName'],
                str(lang['problemsSolved'])
            )
        lang_panel = lang_table

    # Recent submissions
    recent_panel = None
    if data.get('recentAcSubmissions'):
        recent_table = create_recent_activity(data['recentAcSubmissions'])
        if recent_table:
            recent_panel = recent_table

    bottom_grid.add_row(
        lang_panel or "",
        recent_panel or ""
    )
    console.print(bottom_grid)
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