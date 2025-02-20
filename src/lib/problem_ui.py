from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from rich.style import Style
from rich.text import Text
from rich.align import Align
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

import typer

console = Console()

@dataclass
class FunctionMetadata:
    name: str
    params: List[Dict[str, str]]
    return_type: str

class ProblemDetails:
    def __init__(self, problem_data: dict):
        self.data = problem_data
        self.question_id: int = problem_data['questionId']
        self.title: str = problem_data['title']
        self.difficulty: str = problem_data['difficulty']
        self.content: str = problem_data['content']
        self.test_cases: List[str] = (
            problem_data['exampleTestcaseList']
            if isinstance(problem_data['exampleTestcaseList'], list)
            else problem_data.get('exampleTestcases', '').split('\n')
        )
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

    def _create_header(self):
        """Create the problem header with title and difficulty"""
        difficulty_colors = {
            'Easy': 'bright_green',
            'Medium': 'yellow',
            'Hard': 'red'
        }
        difficulty_color = difficulty_colors.get(self.difficulty, 'white')

        header = Text()
        header.append(f"{self.question_id}. {self.title}", style="bold cyan")
        header.append("  ", style="dim")
        header.append(self.difficulty, style=difficulty_color)

        return Align.center(header)

    def _format_description(self, html_content: str) -> str:
        """Format the problem description, removing example test cases"""
        soup = BeautifulSoup(html_content, 'html.parser')
        typer.echo(soup.prettify())

        # Remove all pre tags and example sections
        for pre in soup.find_all('pre'):
            pre.decompose()
        for strong in soup.find_all('strong', class_='example'):
            strong.decompose()
        for tag in soup.find_all():
            if not tag.get_text(strip=True):
                tag.decompose()

        # Format remaining HTML elements
        for code in soup.find_all('code'):
            code.replace_with(BeautifulSoup(f'`{code.text}`', 'html.parser'))

        # Format strong and em tags
        for strong in soup.find_all('strong'):
            strong.replace_with(BeautifulSoup(f'**{strong.text}**', 'html.parser'))

        for em in soup.find_all('em'):
            em.replace_with(BeautifulSoup(f'_{em.text}_', 'html.parser'))

        for pre in soup.find_all('pre'):
            lines = pre.text.strip().split('\n')
            formatted = '\n'.join(f'    {line}' for line in lines)
            pre.replace_with(BeautifulSoup(f'\n```\n{formatted}\n```\n', 'html.parser'))

        return soup.get_text('\n').strip()

    def _format_test_cases(self):
        """Format test cases with explanations"""
        test_cases = []
        examples = self.test_cases

        # Extract example explanations from HTML content
        soup = BeautifulSoup(self.content, 'html.parser')
        explanations = []
        for strong in soup.find_all('strong'):
            if 'Example' in strong.text:
                parent = strong.find_parent(['p', 'div'])
                if parent:
                    explanations.append(parent.get_text())

        # Combine test cases with their explanations
        for i, (test, explanation) in enumerate(zip(examples, explanations)):
            test_cases.append(
                f"[bold blue]Example {i + 1}:[/]\n"
                f"[cyan]Input:[/] {test}\n"
                f"{explanation.replace('Example ' + str(i + 1) + ':', '[yellow]Explanation:[/]')}"
            )

        return "\n\n".join(test_cases)

    def display(self):
        """Display the problem details"""
        # Clear screen and show header
        console.clear()
        console.print(self._create_header())
        console.print()

        # Create main layout
        layout = Layout()
        layout.split_row(
            Layout(name="description", ratio=2),
            Layout(name="examples", ratio=1)
        )

        # Description panel
        description = self._format_description(self.content)
        layout["description"].update(Panel(
            Markdown(description),
            box=ROUNDED,
            title="[bold blue]Description",
            border_style="blue",
            padding=(1, 2)
        ))

        # Example test cases panel
        test_cases = self._format_test_cases()
        layout["examples"].update(Panel(
            test_cases,
            box=ROUNDED,
            title="[bold blue]Examples",
            border_style="blue",
            padding=(1, 2)
        ))

        # Display the layout
        console.print(layout)