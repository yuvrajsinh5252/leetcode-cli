from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")


def create_recent_activity(recent_submissions):
    if not recent_submissions or "recentAcSubmissionList" not in recent_submissions:
        return None

    table = Table(
        title="Recent Submissions",
        box=box.ROUNDED,
        border_style="cyan",
        pad_edge=False,
        show_edge=True,
        width=65,
    )
    table.add_column("Time", style="dim", width=16)
    table.add_column("Problem", style="cyan")

    for sub in recent_submissions["recentAcSubmissionList"][:5]:
        table.add_row(
            format_timestamp(int(sub["timestamp"])),
            sub["title"],
        )
    return table


def create_progress_panel(data):
    if not data.get("progress"):
        return None

    progress = data["progress"]
    all_count = progress["allQuestionsCount"]
    submit_stats = progress["matchedUser"]["submitStats"]
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left")

    for diff in ["Easy", "Medium", "Hard"]:
        total = next((q["count"] for q in all_count if q["difficulty"] == diff), 0)
        solved = next(
            (
                s["count"]
                for s in submit_stats["acSubmissionNum"]
                if s["difficulty"] == diff
            ),
            0,
        )
        table.add_row(f"[dim]{diff}:[/dim] {solved}/{total}")

    return Panel(table, title="[bold green]Progress[/bold green]", border_style="green")


def create_social_links(user, websites=None):
    links = []
    if user["githubUrl"]:
        links.append(f"[blue]GitHub[/blue]: {user['githubUrl']}")
    if user["linkedinUrl"]:
        links.append(f"[blue]LinkedIn[/blue]: {user['linkedinUrl']}")
    if user["twitterUrl"]:
        links.append(f"[blue]Twitter[/blue]: {user['twitterUrl']}")

    if websites:
        for site in websites:
            url = (
                f"https://{site}"
                if not site.startswith(("http://", "https://"))
                else site
            )
            links.append(f"[blue]Website[/blue]: {url}")

    return "\n".join(links) if links else "No social links"


def create_language_stats(data):
    if not data or "matchedUser" not in data:
        return None

    lang_stats = data["matchedUser"]["languageProblemCount"]
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left")
    rows = []
    sorted_stats = sorted(lang_stats, key=lambda x: x["problemsSolved"], reverse=True)

    for lang in sorted_stats[:5]:
        rows.append(f"[dim]{lang['languageName']}:[/dim] {lang['problemsSolved']}")

    table.add_row("\n".join(rows))
    return Panel(
        table,
        title="[bold blue]Languages[/bold blue]",
        border_style="blue",
        width=35,
        padding=(0, 1),
    )


def create_contest_stats(contest_info):
    stats = []
    ranking = contest_info.get("userContestRanking", {}) if contest_info else {}
    if not ranking:
        return "No contest stats"

    rating = ranking.get("rating", 0)
    attended = ranking.get("attendedContestsCount", 0)
    stats.append(f"[dim]Rating:[/dim] {rating:.1f}")
    stats.append(f"[dim]Contests:[/dim] {attended}")
    return "\n".join(stats)


def create_skill_stats(data):
    if not data.get("skillStats"):
        return None

    skills = data["skillStats"]["matchedUser"]["tagProblemCounts"]
    table = Table(
        title="[bold magenta]Skills[/bold magenta]",
        box=box.ROUNDED,
        border_style="magenta",
        width=65,
        pad_edge=False,
    )
    table.add_column("Level", style="magenta")
    table.add_column("Tag", style="cyan")
    table.add_column("Solved", justify="right")

    for level in ["advanced", "intermediate", "fundamental"]:
        for skill in skills[level][:2]:
            table.add_row(
                level.capitalize(), skill["tagName"], str(skill["problemsSolved"])
            )

    return table


def display_user_stats(data):
    console.clear()
    profile_width, stats_width, progress_width = 65, 35, 30

    if not data.get("userProfile"):
        console.print(Panel("Could not fetch user profile", border_style="red"))
        return

    user = data["userProfile"]["matchedUser"]
    profile = user["profile"]

    profile_table = Table.grid(padding=(0, 1))
    profile_table.add_column(justify="left")
    profile_info = [
        f"[bold cyan]{user.get('username', 'N/A')}[/bold cyan]",
        f"[dim]Name:[/dim] {profile.get('realName') or 'Not specified'}",
        f"[dim]Ranking:[/dim] {profile.get('ranking', 'N/A')}",
    ]

    for label, field in [
        ("Company", "company"),
        ("Job Title", "jobTitle"),
        ("School", "school"),
        ("Location", "countryName"),
    ]:
        if field in profile and profile[field]:
            profile_info.append(f"[dim]{label}:[/dim] {profile[field]}")

    if profile.get("skillTags"):
        profile_info.append(f"[dim]Skills:[/dim] {', '.join(profile['skillTags'])}")

    social_links = create_social_links(user, profile.get("websites", []))
    if social_links != "No social links":
        profile_info.append("\n" + social_links)

    profile_table.add_row("\n".join(profile_info))
    profile_panel = Panel(
        profile_table,
        title="[bold cyan]Profile Info[/bold cyan]",
        border_style="cyan",
        width=profile_width,
        padding=(0, 1),
    )

    stats_table = Table.grid(padding=(0, 1))
    stats_table.add_column(justify="left")
    stats = [
        f"[dim]Solutions:[/dim] {profile.get('solutionCount', 0)} ({profile.get('solutionCountDiff', 0):+d})",
        f"[dim]Reputation:[/dim] {profile.get('reputation', 0)} ({profile.get('reputationDiff', 0):+d})",
        f"[dim]Views:[/dim] {profile.get('postViewCount', 0)} ({profile.get('postViewCountDiff', 0):+d})",
    ]
    if "categoryDiscussCount" in profile:
        stats.append(
            f"[dim]Discussions:[/dim] {profile['categoryDiscussCount']} ({profile.get('categoryDiscussCountDiff', 0):+d})"
        )
    stats_table.add_row("\n".join(stats))

    progress = create_progress_panel(data)
    if progress:
        progress.width = progress_width

    middle_column = Table.grid(padding=(0, 1))
    if data.get("languageStats"):
        middle_column.add_row(create_language_stats(data["languageStats"]))
        middle_column.add_row("")
    if "contestInfo" in data and data.get("contestInfo"):
        contest_panel = Panel(
            create_contest_stats(data["contestInfo"]),
            title="[bold yellow]Contest Stats[/bold yellow]",
            border_style="yellow",
            width=stats_width,
            padding=(0, 1),
        )
        middle_column.add_row(contest_panel)

    right_column = Table.grid()
    if progress:
        right_column.add_row(progress)
        right_column.add_row("")
    stats_panel = Panel(
        stats_table,
        title="[bold blue]Activity Stats[/bold blue]",
        border_style="blue",
        width=progress_width,
        padding=(0, 1),
    )
    right_column.add_row(stats_panel)

    top_grid = Table.grid(padding=(0, 2))
    top_grid.add_row(profile_panel, middle_column, right_column)

    bottom_grid = Table.grid(padding=(0, 2))
    bottom_grid.add_column(width=65)
    bottom_grid.add_column(width=65)
    bottom_grid.add_row(
        create_skill_stats(data) if data.get("skillStats") else "",
        create_recent_activity(data["recentAcSubmissions"])
        if data.get("recentAcSubmissions")
        else "",
    )

    console.print("\n")
    console.print(top_grid)
    console.print("\n")
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
        show_edge=True,
    )

    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", style="cyan")
    table.add_column("Difficulty", justify="center", width=10)
    table.add_column("Status", justify="center", width=8)
    table.add_column("AC Rate", justify="right", width=8)

    for problem in data["problemsetQuestionList"]["questions"]:
        status_icon = "[green]✓" if problem["status"] == "ac" else "[red]✗"
        ac_rate = f"{problem['acRate']:.1f}%"
        table.add_row(
            problem["frontendQuestionId"],
            problem["title"],
            problem["difficulty"],
            status_icon,
            ac_rate,
        )

    console.print(table)
    console.print("\n")
