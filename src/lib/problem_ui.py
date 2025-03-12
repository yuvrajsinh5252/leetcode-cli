from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from bs4 import BeautifulSoup, Tag
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

console = Console()

COLORS = {
    'title': 'bold bright_cyan',
    'difficulty': {
        'Easy': 'bold bright_green',
        'Medium': 'bold yellow',
        'Hard': 'bold red'
    },
    'section_title': 'bold blue',
    'input_label': 'bright_cyan',
    'output_label': 'bright_green',
    'explanation_label': 'bright_yellow',
    'stats_label': 'bright_cyan',
    'border': 'bright_blue'
}

STYLES = {
    'panel_padding': (1, 2),
    'box_style': ROUNDED
}

@dataclass
class FunctionMetadata:
    name: str
    params: List[Dict[str, str]]
    return_type: str

class ProblemDetails:
    def __init__(self, problem_data: dict):
        required_fields = ['questionFrontendId', 'title', 'content', 'difficulty']
        if not all(field in problem_data for field in required_fields):
            raise ValueError("Missing required problem data fields")

        self.data = problem_data
        self.question_id: int = problem_data['questionFrontendId']
        self.title: str = problem_data['title']
        self.difficulty: str = problem_data['difficulty']
        self.content: str = problem_data['content']

        self.test_cases: List[str] = (
            problem_data.get('exampleTestcaseList', [])
            if isinstance(problem_data.get('exampleTestcaseList'), list)
            else problem_data.get('exampleTestcases', '').split('\n')
        )
        self.code_snippets: List[Dict] = problem_data.get('codeSnippets', [])

        # Parse metadata
        self.function_metadata = self._parse_metadata(problem_data.get('metaData', '{}'))

        # Parse stats
        self.stats = self._parse_stats(problem_data.get('stats', '{}'))

        self.example_sections = []
        self.example_images = []
        self._parse_content()
        self.console_width = console.width

    def _parse_metadata(self, metadata_str: str) -> Optional[FunctionMetadata]:
        """Parse function metadata with better error handling"""
        try:
            metadata = json.loads(metadata_str)
            return FunctionMetadata(
                name=metadata.get('name', 'solution'),
                params=metadata.get('params', []),
                return_type=metadata.get('return', {}).get('type', 'void')
            )
        except Exception:
            return None

    def _parse_stats(self, stats_str: str) -> Dict[str, str]:
        """Parse problem statistics with better error handling"""
        try:
            return json.loads(stats_str)
        except Exception:
            return {}

    def _is_example_image(self, img_tag: Tag) -> bool:
        """Check if an image belongs to an example by examining nearby text"""
        if not isinstance(img_tag, Tag):
            return False

        # Look at previous and next siblings for example-related text
        for sibling in list(img_tag.previous_siblings) + list(img_tag.next_siblings):
            if isinstance(sibling, Tag):
                text = sibling.get_text().lower()
                if any(marker in text for marker in ['example', 'input:', 'output:', 'explanation:']):
                    return True
        return False

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

    def _create_header(self) -> str:
        """Create a stylized header with title, difficulty and problem ID"""
        difficulty_color = COLORS['difficulty'].get(self.difficulty, 'white')

        header = (
            f"[{COLORS['title']}]{self.question_id}. {self.title}[/]"
            f"\n[{difficulty_color}]{self.difficulty}[/] • "
        )
        return header

    def _format_description(self, html_content: str) -> str:
        """Format the problem description, excluding example images"""
        soup = BeautifulSoup(html_content, 'html.parser')

        for img in soup.find_all('img'):
            if isinstance(img, Tag):
                if self._is_example_image(img):
                    self.example_images.append({
                        'alt': str(img.get('alt', 'Image')),
                        'src': str(img.get('src', '')),
                        'position': len(self.example_images)
                    })
                    img.decompose()
                else:
                    alt_text = str(img.get('alt', 'Image'))
                    src = str(img.get('src', ''))
                    if src:
                        img_block = (
                            "\n─────────── Image ───────────\n"
                            f"Description: {alt_text}\n"
                            f"URL: {src}\n"
                            "─────────────────────────────\n"
                        )
                        img.replace_with(BeautifulSoup(img_block, 'html.parser'))

        for pre in soup.find_all('pre'):
            pre.decompose()
        for strong in soup.find_all('strong', class_='example'):
            strong.decompose()
        for tag in soup.find_all():
            if not tag.get_text(strip=True):
                tag.decompose()

        for code in soup.find_all('code'):
            code.replace_with(BeautifulSoup(f'`{code.text}`', 'html.parser'))

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

    def _extract_examples_from_html(self) -> List[Dict[str, str]]:
        """Extract and parse examples with their associated images and explanations"""
        soup = BeautifulSoup(self.content, 'html.parser')
        examples_data = []
        current_example = None
        current_explanation = []

        def add_explanation_if_exists():
            if current_explanation and current_example:
                text = ' '.join(current_explanation)
                current_example['sections'].append(('explanation_text', text))
                current_explanation.clear()

        for element in soup.find_all(['pre', 'p', 'img']):
            if not isinstance(element, Tag):
                continue

            if element.name == 'pre' and 'Example' not in element.text:
                if current_example:
                    add_explanation_if_exists()
                    examples_data.append(current_example)
                current_example = {'input': '', 'output': '', 'explanation': '', 'sections': []}

                for strong in element.find_all('strong'):
                    if not strong.next_sibling:
                        continue
                    text = str(strong.next_sibling).strip()
                    if 'Input:' in strong.text:
                        current_example['input'] = text
                        current_example['sections'].append(('input', text))
                    elif 'Output:' in strong.text:
                        current_example['output'] = text
                        current_example['sections'].append(('output', text))
                    elif 'Explanation:' in strong.text:
                        current_example['explanation'] = text
                        current_example['sections'].append(('explanation', text))

            elif element.name == 'img' and current_example:
                add_explanation_if_exists()
                alt_text = str(element.get('alt', 'Image'))
                src = str(element.get('src', ''))
                if src:
                    current_example['sections'].append(('image', {
                        'alt': alt_text,
                        'src': src
                    }))

            elif element.name == 'p' and current_example:
                text = element.get_text().strip()
                if text and not text.startswith('Example') and not text.startswith('Constraints'):
                    current_explanation.append(text)

        if current_example:
            add_explanation_if_exists()
            examples_data.append(current_example)

        return examples_data

    def _format_test_cases(self) -> str:
        """Format test cases with properly ordered images and explanations"""
        examples_data = self._extract_examples_from_html()

        test_cases = []
        for i, example in enumerate(examples_data, 1):
            formatted_parts = [f"[{COLORS['section_title']}]Example {i}:[/]"]

            for section_type, content in example['sections']:
                if section_type == 'input':
                    formatted_parts.append(
                        f"[{COLORS['input_label']}]Input:[/] {content}"
                    )
                elif section_type == 'output':
                    formatted_parts.append(
                        f"[{COLORS['output_label']}]Output:[/] {content}"
                    )
                elif section_type == 'explanation':
                    formatted_parts.append(
                        f"[{COLORS['explanation_label']}]Explanation:[/] {content}"
                    )
                elif section_type == 'image':
                    src = content.get('src', '') if isinstance(content, dict) else ''
                    if src:
                        formatted_parts.append(f"[dim]{src}[/]")
                elif section_type == 'explanation_text':
                    formatted_parts.append(content)

            test_cases.append("\n".join(formatted_parts))

        return "\n\n" + "\n\n".join(test_cases)

    def _format_stats(self) -> str:
        """Format problem statistics with enhanced styling"""
        stats = {
            'Acceptance Rate': self.stats.get('acRate', 'N/A'),
            'Total Accepted': self.stats.get('totalAccepted', 'N/A'),
            'Total Submissions': self.stats.get('totalSubmission', 'N/A')
        }

        formatted_stats = [
            f"[{COLORS['section_title']}]Problem Statistics[/]\n"
        ]

        for label, value in stats.items():
            formatted_stats.append(
                f"[{COLORS['stats_label']}]{label}:[/] {value}"
            )

        return "\n".join(formatted_stats)

    def display(self):
        """Display the problem details in a three-panel layout"""
        console.clear()
        console.print()

        layout = Layout()
        layout.split_row(
            Layout(name="main", ratio=2),
            Layout(name="side", ratio=1)
        )

        layout["side"].split_column(
            Layout(name="examples", ratio=3),
            Layout(name="stats", ratio=1)
        )

        # Main description panel
        layout["main"].update(Panel(
            Markdown(self._format_description(self.content)),
            title=self._create_header(),
            box=STYLES['box_style'],
            border_style=COLORS['border'],
            padding=STYLES['panel_padding']
        ))

        # Examples panel
        layout["examples"].update(Panel(
            self._format_test_cases(),
            title=f"[{COLORS['section_title']}]Examples[/]",
            box=STYLES['box_style'],
            border_style=COLORS['border'],
            padding=STYLES['panel_padding']
        ))

        # Stats panel
        layout["stats"].update(Panel(
            self._format_stats(),
            title=f"[{COLORS['section_title']}]Statistics[/]",
            box=STYLES['box_style'],
            border_style=COLORS['border'],
            padding=STYLES['panel_padding']
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