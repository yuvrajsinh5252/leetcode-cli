import json
import re

import markdownify
from rich.box import ROUNDED
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()

COLORS = {
    "problem_number": "orange1",
    "title": "bold bright_cyan",
    "difficulty": {
        "Easy": "bold bright_green",
        "Medium": "bold yellow",
        "Hard": "bold red",
    },
    "section_title": "bold blue",
    "stats_label": "bright_cyan",
    "border": "bright_blue",
    "image_link": "dim italic cyan",
}

STYLES = {"panel_padding": (1, 2), "box_style": ROUNDED}


class ProblemDetails:
    def __init__(self, problem_data: dict):
        self.problem_number = problem_data["questionFrontendId"]
        self.title = problem_data["title"]
        self.content = problem_data["content"]
        self.difficulty = problem_data["difficulty"]
        self.stats = problem_data["stats"]
        self.topics = problem_data.get("topicTags", [])
        self.similar_questions = problem_data.get("similarQuestionList", [])

        if isinstance(self.stats, str):
            try:
                self.stats = json.loads(self.stats)
            except json.JSONDecodeError:
                self.stats = {}

    def _format_markdown(self, content):
        md = markdownify.markdownify(content, heading_style="ATX", bullet_style="-")
        md = re.sub(r"^(Example \d+:)", r"### \1", md, flags=re.MULTILINE)
        md = re.sub(r"```([^`]+)```", r"```\n\1\n```", md)
        md = re.sub(r"\*\*Input:\*\*", r"**Input:** ", md)
        md = re.sub(r"\*\*Output:\*\*", r"**Output:** ", md)
        md = re.sub(r"\*\*Explanation:\*\*", r"**Explanation:** ", md)
        md = re.sub(r"\n{2,}", "\n\n", md)
        return md

    def _format_stats(self) -> str:
        stats = {
            "Acceptance Rate": self.stats.get("acRate", "N/A"),
            "Total Accepted": self.stats.get("totalAccepted", "N/A"),
            "Total Submissions": self.stats.get("totalSubmission", "N/A"),
        }

        formatted = [f"● [{COLORS['section_title']}]Problem Statistics:[/]"]
        for label, value in stats.items():
            formatted.append(f"  - [{COLORS['stats_label']}]{label}:[/] {value}")

        return "\n".join(formatted)

    def _create_header(self) -> str:
        difficulty_color = COLORS["difficulty"].get(self.difficulty, "white")
        return (
            f"[{COLORS['problem_number']}]{self.problem_number}. [/]\n"
            f"[{COLORS['title']}]{self.title}[/]\n"
            f"[{difficulty_color}] ● {self.difficulty}[/]"
        )

    def _format_topics(self) -> str:
        if not self.topics:
            return ""

        topic_names = [tag.get("name", "") for tag in self.topics if "name" in tag]
        if not topic_names:
            return ""

        return f"● [{COLORS['section_title']}]Topics:[/] {', '.join(topic_names)}"

    def _format_similar_questions(self) -> str:
        if not self.similar_questions:
            return ""

        lines = [f"● [{COLORS['section_title']}]Similar Questions:[/]"]
        for q in self.similar_questions[:5]:
            title = q.get("title", "")
            difficulty = q.get("difficulty", "")
            question_id = q.get("questionId", "") or q.get("titleSlug", "")
            lock_symbol = " 🔒" if q.get("isPaidOnly", False) else ""
            diff_color = COLORS["difficulty"].get(difficulty, "white")

            if title and difficulty:
                if "titleSlug" in q:
                    slug = q.get("titleSlug")
                    title_display = (
                        f"[link=https://leetcode.com/problems/{slug}/]{title}[/link]"
                    )
                else:
                    title_display = title

                question_line = f"  - [{COLORS['problem_number']}]#{question_id}[/] {title_display} {lock_symbol} ([{diff_color}]{difficulty}[/{diff_color}])"
                lines.append(question_line)

        if len(lines) <= 1:
            return ""

        return "\n".join(lines)

    def display_probelm(self):
        formatted_md = self._format_markdown(self.content)

        content_panel = Panel(
            Markdown(formatted_md),
            box=STYLES["box_style"],
            title=self._create_header(),
            title_align="center",
            border_style=COLORS["border"],
            padding=STYLES["panel_padding"],
        )
        console.print(content_panel)

    def display_stats(self):
        stats_panel = Panel(
            self._format_stats(),
            title=f"[{COLORS['section_title']}]Statistics[/]",
            box=STYLES["box_style"],
            border_style=COLORS["border"],
            padding=STYLES["panel_padding"],
        )
        console.print(stats_panel)

    def display_additional_info(self):
        info_content = []

        topics = self._format_topics()
        if topics:
            info_content.append(topics)

        similar_questions = self._format_similar_questions()
        if similar_questions:
            if info_content:
                info_content.append("")
            info_content.append(similar_questions)

        if info_content:
            info_panel = Panel(
                Text.from_markup("\n".join(info_content)),
                title=f"[{COLORS['section_title']}]Additional Information[/]",
                box=STYLES["box_style"],
                border_style=COLORS["border"],
                padding=STYLES["panel_padding"],
            )
            console.print(info_panel)
