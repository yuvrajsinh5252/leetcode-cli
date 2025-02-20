from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from bs4 import BeautifulSoup, Tag
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

        # Parse stats from JSON string
        self.stats = {}
        try:
            stats_str = problem_data.get('stats', '{}')
            self.stats = json.loads(stats_str)
        except Exception:
            self.stats = {}

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

        header = (
            f"[bold cyan]{self.question_id}. {self.title}[/]  "
            f"[{difficulty_color}]{self.difficulty}[/]"
        )

        return header

    def _format_description(self, html_content: str) -> str:
        """Format the problem description, removing example test cases"""
        soup = BeautifulSoup(html_content, 'html.parser')

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

        # Format HTML formatting tags
        for tag in soup.find_all(['strong', 'em', 'b', 'i']):
            if not isinstance(tag, Tag):
                continue
            text = tag.text.strip()
            if tag.name in ['strong', 'b']:
                replacement = f"**{text}**"
            elif tag.name in ['em', 'i']:
                replacement = f"_{text}_"
            tag.replace_with(BeautifulSoup(replacement, 'html.parser'))

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

        examples_data = []

        # Find all pre tags containing example data
        for pre in soup.find_all('pre'):
            # Extract input, output, and explanation
            if isinstance(pre, Tag):
                input_tag = pre.find('strong', text='Input:')
                output_tag = pre.find('strong', text='Output:')
                explanation_tag = pre.find('strong', text='Explanation:')

            if input_tag and output_tag:
                input_text = str(input_tag.next_sibling).strip() if input_tag and input_tag.next_sibling else ""
                output_text = str(output_tag.next_sibling).strip() if output_tag and output_tag.next_sibling else ""
                explanation_text = str(explanation_tag.next_sibling).strip() if explanation_tag and explanation_tag.next_sibling else ""

            examples_data.append({
                'input': input_text,
                'output': output_text,
                'explanation': explanation_text
            })

        # Format the examples
        for i, example in enumerate(examples_data, 1):
            formatted_example = (
            f"[bold blue]Example {i}: [/]\n\n"
            f"[cyan]Input: [/]{example['input']}\n"
            f"[cyan]Output: [/]{example['output']}"
            )
            if example['explanation']:
                formatted_example += f"\n[yellow]Explanation: [/]{example['explanation']}"
            test_cases.append(formatted_example)

        return "\n\n".join(test_cases)

    def _format_stats(self) -> str:
        """Format problem statistics"""
        accepted = self.stats.get('totalAccepted', 'N/A')
        submissions = self.stats.get('totalSubmission', 'N/A')
        ac_rate = self.stats.get('acRate', 'N/A')

        return (
            "[bold blue]Problem Stats[/]\n\n"
            f"[cyan]Acceptance Rate:[/] {ac_rate}\n"
            f"[cyan]Total Accepted:[/] {accepted}\n"
            f"[cyan]Total Submissions:[/] {submissions}"
        )

    def display(self):
        """Display the problem details"""
        console.clear()
        console.print()

        test_cases = self._format_test_cases()
        stats = self._format_stats()

        # Create main layout
        layout = Layout()

        # Split into left and right sections
        layout.split_row(
            Layout(name="description", ratio=2),
            Layout(name="right_panel", ratio=1)
        )

        # Split right panel into examples and stats
        layout["right_panel"].split_column(
            Layout(name="examples"),
            Layout(name="stats", size=10)
        )

        # Description panel
        layout["description"].update(Panel(
            Markdown(self._format_description(self.content)),
            box=ROUNDED,
            title=str(self._create_header()),
            border_style="blue",
            padding=(1, 2)
        ))

        # Example test cases panel
        layout["examples"].update(Panel(
            test_cases,
            box=ROUNDED,
            title="[bold blue]Examples",
            border_style="blue",
            padding=(1, 2)
        ))

        # Stats panel
        layout["stats"].update(Panel(
            stats,
            box=ROUNDED,
            title="[bold blue]Statistics",
            border_style="blue",
            padding=(1, 2)
        ))

        console.print(layout)

    def display_only_description(self):
        """Display only the problem description"""
        console.clear()
        console.print()

        console.print(
            Panel(
                Markdown(self._format_description(self.content)),
                box=ROUNDED,
                title=str(self._create_header()),
                border_style="blue",
                padding=(1, 2)
            )
        )

    def display_only_test_cases(self):
        """Display only the test cases"""
        console.clear()
        console.print()

        console.print(
            Panel(
                self._format_test_cases(),
                box=ROUNDED,
                title="[bold blue]Examples",
                border_style="blue",
                padding=(1, 2)
            )
        )

    def display_full(self):
        """Display the full problem details"""
        self.display_only_description()
        self.display_only_test_cases()