from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from rich.text import Text
from rich.align import Align
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

console = Console()

@dataclass
class FunctionMetadata:
    name: str
    params: List[Dict[str, str]]
    return_type: str

class ProblemDetails:
    def __init__(self, problem_data: dict):
        self.question_id: int = problem_data['questionId']
        self.title: str = problem_data['title']
        self.difficulty: str = problem_data['difficulty']
        self.content: str = problem_data['content']
        self.test_cases: List[str] = problem_data['exampleTestcases'].split('\n')
        self.code_snippets: List[Dict] = problem_data['codeSnippets']

        # Parse metadata
        self.function_metadata: Optional[FunctionMetadata] = None
        try:
            metadata = json.loads(problem_data['metaData'])
            self.function_metadata = FunctionMetadata(
                name=metadata.get('name', 'solution'),
                params=metadata.get('params', []),
                return_type=metadata.get('return', {}).get('type', 'void')
            )
        except Exception:
            pass

        self._parse_content()
        self.console_width = console.width

    def _parse_content(self):
        """Parse the HTML content into different sections"""
        soup = BeautifulSoup(self.content, 'html.parser')

        for code in soup.find_all('code'):
            code.replace_with(soup.new_string(f'`{code.text}`'))

        self.description: List[str] = []
        self.examples: List[str] = []
        self.constraints: List[str] = []

        current_section = self.description

        for p in soup.find_all('p'):
            text = p.text.strip()
            if not text:
                continue

            if 'Example' in text:
                current_section = self.examples
                current_section.append('\n' + text)
            elif 'Constraints:' in text:
                current_section = self.constraints
                current_section.append('\n' + text)
            elif any(marker in text for marker in ['Input:', 'Output:', 'Explanation:']):
                current_section.append('  ' + text)
            elif current_section == self.examples and not text.startswith('Example'):
                current_section.append('  ' + text)
            else:
                current_section.append(text)

    @property
    def formatted_description(self) -> str:
        """Get the formatted problem description"""
        sections = [
            ' '.join(self.description),
            *self.examples,
            *self.constraints
        ]
        return '\n'.join(line for line in sections if line.strip())

    @property
    def available_languages(self) -> List[str]:
        """Get list of available programming languages"""
        return [snippet['lang'] for snippet in self.code_snippets]

    @property
    def formatted_function_signature(self) -> str:
        """Get the formatted function signature"""
        if not self.function_metadata:
            return "[red]Error loading function signature[/]"

        param_str = ', '.join(
            f"{p['name']}: {p['type']}"
            for p in self.function_metadata.params
        )

        return (
            "[bold blue]Function Signature:[/]\n"
            f"[bold cyan]def[/] [yellow]{self.function_metadata.name}[/](\n"
            f"    [green]{param_str}[/]\n"
            f") -> [green]{self.function_metadata.return_type}[/]"
        )

    def get_code_snippet(self, language: str) -> Optional[str]:
        """Get code snippet for specific language"""
        for snippet in self.code_snippets:
            if snippet['lang'].lower() == language.lower():
                return snippet['code']
        return None

    def format_test_case(self, input_str: str, expected_str: str, case_num: int) -> str:
        return (
            f"[bold blue]Ex {case_num}:[/] "
            f"[bold cyan]In:[/] {input_str} → "
            f"[bold green]Out:[/] {expected_str}"
        )

    def create_header(self):
        difficulty_colors = {
            'Easy': 'bright_green',
            'Medium': 'yellow',
            'Hard': 'red'
        }
        difficulty_color = difficulty_colors.get(self.difficulty, 'white')

        header = Text()
        header.append("🔹 ", style="blue")
        header.append(f"{self.question_id}. {self.title}", style="bold cyan")
        header.append(" • ", style="dim")
        header.append(self.difficulty, style=difficulty_color)

        return Align.center(header)

    def display(self):
        console.clear()

        console.print(self.create_header())
        console.print()

        layout = Layout()
        layout.split_row(
            Layout(name="left_section"),
            Layout(name="sidebar", size=self.console_width // 4)
        )

        layout["left_section"].split_column(
            Layout(name="description", ratio=85),
            Layout(name="bottom", ratio=15)
        )

        # Update description panel
        layout["description"].update(Panel(
            Markdown(self.formatted_description, justify="left", style="white"),
            box=ROUNDED,
            title="[bold blue]Description",
            border_style="blue",
            padding=(1, 2),
            expand=True
        ))

        # Update sidebar panel
        sidebar_content = (
            f"{self.formatted_function_signature}\n\n"
            "[bold blue]Available Languages:[/]\n"
            f"[green]{self.available_languages}[/]"
        )

        layout["sidebar"].update(Panel(
            sidebar_content,
            box=ROUNDED,
            border_style="blue",
            padding=(1, 2),
            expand=True
        ))

        # Update test cases panel
        test_cases_content = []

        for i in range(0, len(self.test_cases), 2):
            if i + 1 < len(self.test_cases):
                case_num = i // 2 + 1
                test_case = self.format_test_case(
                    self.test_cases[i],
                    self.test_cases[i+1],
                    case_num
                )
                test_cases_content.append(test_case)

        layout["bottom"].update(Panel(
            "\n\n".join(test_cases_content),
            box=ROUNDED,
            title="[bold blue]Sample Test Cases",
            border_style="blue",
            padding=(1, 2),
        ))

        console.print(layout)