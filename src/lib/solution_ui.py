import webbrowser
from datetime import datetime

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.table import Table

console = Console()


class SolutionUI:
    LEETCODE_BASE_URL = "https://leetcode.com/problems/"
    COLUMNS = ["#", "Title", "Author", "Date", "Stats", "Tags"]
    COLUMN_WIDTHS = {
        "#": 3,
        "Title": 38,
        "Author": 18,
        "Date": 12,
        "Stats": 20,
        "Tags": 35,
    }
    MAX_TAGS = 4
    STYLES = {
        "title": "bold green",
        "author": "yellow",
        "date": "cyan",
        "stats": "blue",
        "tags": "cyan",
        "table_border": "blue",
    }

    def __init__(self, fetched_solution):
        self.solution = fetched_solution
        self.total_solutions = fetched_solution["totalNum"]
        self.solutions = fetched_solution["edges"]

    def _format_date(self, date_str):
        """Format the date string from ISO format"""
        if not date_str:
            return "Unknown"

        try:
            created_date = datetime.fromisoformat(date_str.replace("+00:00", ""))
            return created_date.strftime("%b %d, %Y")
        except Exception:
            return "Unknown"

    def _format_number(self, number):
        """Format numbers to be more readable"""
        if number >= 1000000:
            return f"{number / 1000000:.1f}M"
        elif number >= 1000:
            return f"{number / 1000:.1f}K"
        return str(number)

    def _format_reactions(self, reactions):
        """Format the reactions (upvotes, downvotes)"""
        upvotes = 0
        downvotes = 0

        for reaction in reactions or []:
            if reaction.get("reactionType") == "UPVOTE":
                upvotes = reaction.get("count", 0)
            elif reaction.get("reactionType") == "THUMBS_DOWN":
                downvotes = reaction.get("count", 0)

        up_formatted = self._format_number(upvotes)
        down_formatted = self._format_number(downvotes)

        return f"[green] ▲ {up_formatted}[/green] [red]▼ {down_formatted}[/red]"

    def _truncate_text(self, text, max_length):
        """Truncate text with ellipsis if longer than max_length"""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _format_tags(self, tags):
        """Format the tags with styling, limiting the number shown"""
        if not tags:
            return "[dim]None[/dim]"

        formatted_tags = []
        for i, tag in enumerate(tags):
            if i >= self.MAX_TAGS:
                formatted_tags.append(
                    f"[{self.STYLES['tags']}]+{len(tags) - self.MAX_TAGS}[/{self.STYLES['tags']}]"
                )
                break

            tag_name = tag.get("name", "")
            if tag_name:
                tag_display = tag_name
                if tag_name in ["JavaScript", "TypeScript", "Python3"]:
                    tag_display = (
                        tag_name[:2] + tag_name[-2:] if len(tag_name) > 4 else tag_name
                    )
                elif len(tag_name) > 10:
                    tag_display = self._truncate_text(tag_name, 10)

                formatted_tags.append(
                    f"[{self.STYLES['tags']}]#{escape(tag_display)}[/{self.STYLES['tags']}]"
                )

        return " ".join(formatted_tags)

    def _format_author(self, author_data):
        """Format the author information"""
        author_name = author_data.get("realName", "Unknown")
        author_name = self._truncate_text(author_name, 15)
        return author_name

    def _open_solution_url(self, solution_node):
        """Open solution URL in browser"""
        slug_parts = solution_node.get("slug", "").split("-")
        problem_slug = slug_parts[0] if len(slug_parts) > 0 else ""

        if len(slug_parts) > 1 and slug_parts[1] == "sum":
            problem_slug = f"{slug_parts[0]}-{slug_parts[1]}"

        solution_id = solution_node.get("topicId", "")
        title_slug = solution_node.get("slug", "")

        if problem_slug and solution_id and title_slug:
            url = f"{self.LEETCODE_BASE_URL}{problem_slug}/solutions/{solution_id}/{title_slug}/"
            webbrowser.open(url)
        elif problem_slug:
            url = f"{self.LEETCODE_BASE_URL}{problem_slug}/"
            webbrowser.open(url)

    def show_solution(self):
        console.print("\n")

        table = Table(
            title=f"Solutions Found: {self.total_solutions}",
            box=box.ROUNDED,
            border_style="cyan",
            pad_edge=False,
            show_edge=True,
        )

        for column in self.COLUMNS:
            table.add_column(
                column,
                width=self.COLUMN_WIDTHS.get(column, None),
                justify="left" if column != "#" else "right",
                no_wrap=column not in ["Tags"],
                style="bold" if column in ["Title", "#"] else None,
            )

        for i, solution in enumerate(self.solutions, 1):
            node = solution.get("node", {})

            slug_parts = node.get("slug", "").split("-")
            problem_slug = slug_parts[0] if len(slug_parts) > 0 else ""

            if len(slug_parts) > 1 and slug_parts[1] == "sum":
                problem_slug = f"{problem_slug}-{slug_parts[1]}"

            solution_id = node.get("topicId", "")
            title_slug = node.get("slug", "")

            title_text = node.get("title", "Untitled")
            truncated_title = self._truncate_text(
                title_text, self.COLUMN_WIDTHS["Title"] - 3
            )

            solution_url = f"{self.LEETCODE_BASE_URL}{problem_slug}/solutions/{solution_id}/{title_slug}/"
            title = f"[link={solution_url}][{self.STYLES['title']}]{escape(truncated_title)}[/{self.STYLES['title']}][/link]"

            author_name = self._format_author(node.get("author", {}))
            author = f"[{self.STYLES['author']}]{author_name}[/{self.STYLES['author']}]"

            date = f"[{self.STYLES['date']}]{self._format_date(node.get('createdAt', ''))}[/{self.STYLES['date']}]"

            hit_count = node.get("hitCount", 0)
            hit_count_formatted = self._format_number(hit_count)
            reactions = self._format_reactions(node.get("reactions", []))
            stats = f"[bold blue]{hit_count_formatted}[/bold blue] {reactions}"

            tags = self._format_tags(node.get("tags", []))

            table.add_row(str(i), title, author, date, stats, tags)

        console.print(table)
        console.print(
            "\n[dim italic]Click on solution titles to open them in your browser[/dim italic]\n"
        )

    def handle_solution_selection(self, index):
        """Handle selection of a solution by index (1-based)"""
        if 1 <= index <= len(self.solutions):
            solution = self.solutions[index - 1]
            node = solution.get("node", {})
            if node:
                self._open_solution_url(node)
                return True
        return False
