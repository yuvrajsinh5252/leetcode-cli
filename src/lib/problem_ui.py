from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from bs4 import BeautifulSoup, Tag
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import typer

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
    'border': 'bright_blue',
    'image_link': 'dim italic cyan'
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
    """Class to parse and display LeetCode problem details"""

    def __init__(self, problem_data: dict):
        required_fields = ['questionFrontendId', 'title', 'content', 'difficulty']
        if not all(field in problem_data for field in required_fields):
            raise ValueError("Missing required problem data fields")

        # Extract basic metadata
        self.question_id = problem_data['questionFrontendId']
        self.title = problem_data['title']
        self.difficulty = problem_data['difficulty']
        self.content = problem_data['content']

        # Extract test cases
        self.test_cases = (
            problem_data.get('exampleTestcaseList', [])
            if isinstance(problem_data.get('exampleTestcaseList'), list)
            else problem_data.get('exampleTestcases', '').split('\n')
        )

        # Code snippets and metadata
        self.code_snippets = problem_data.get('codeSnippets', [])
        self.function_metadata = self._parse_metadata(problem_data.get('metaData', '{}'))
        self.stats = self._parse_stats(problem_data.get('stats', '{}'))

        # Initialize content containers
        self.example_images = []
        self.console_width = console.width

    def _parse_metadata(self, metadata_str: str) -> Optional[FunctionMetadata]:
        """Parse function metadata with error handling"""
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
        """Parse problem statistics with error handling"""
        try:
            return json.loads(stats_str)
        except Exception:
            return {}

    def _is_example_image(self, img_tag: Tag) -> bool:
        """Determine if an image belongs to an example section"""
        if not isinstance(img_tag, Tag):
            return False

        # Check parent elements
        parent = img_tag.parent
        for _ in range(3):
            if parent and isinstance(parent, Tag):
                if any(marker in parent.get_text().lower()
                       for marker in ['example', 'input:', 'output:', 'explanation:']):
                    return True
                parent = parent.parent
            else:
                break

        # Check siblings
        siblings = list(img_tag.previous_siblings) + list(img_tag.next_siblings)
        for sibling in siblings:
            if isinstance(sibling, Tag):
                text = sibling.get_text().lower()
                # Check for example indicators
                if (any(marker in text for marker in ['example', 'input:', 'output:', 'explanation:']) or
                    (sibling.name == 'pre' and ('input:' in text or 'output:' in text)) or
                    (sibling.name in ['h4', 'strong', 'b'] and 'example' in text)):
                    return True

        return False

    def _create_header(self) -> str:
        """Create a stylized header with title, difficulty and problem ID"""
        difficulty_color = COLORS['difficulty'].get(self.difficulty, 'white')
        return f"[{COLORS['title']}]{self.question_id}. {self.title}[/]\n" \
               f"[{difficulty_color}]{self.difficulty}[/] • "

    def _format_description(self, html_content: str) -> str:
        """Format problem description, removing examples and handling images"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Remove examples from description
        self._remove_examples_from_soup(soup)

        # 2. Process images
        self._process_images(soup)

        # 3. Clean and format content
        self._format_text_elements(soup)

        # 4. Final cleanup of any example text
        return self._clean_example_text(soup.get_text('\n').strip())

    def _remove_examples_from_soup(self, soup: BeautifulSoup) -> None:
        """Remove all example sections from the soup"""
        # Remove elements with example headers
        for element in soup.find_all(['strong', 'p', 'pre']):
            if not isinstance(element, Tag):
                continue

            text = element.get_text().lower()

            # Example headers
            if element.name == 'strong' and 'example' in text:
                if element.parent:
                    element.parent.decompose()
                else:
                    element.decompose()
                continue

            # Example paragraphs
            if element.name == 'p' and text.startswith('example'):
                element.decompose()
                continue

            # Example code blocks
            if element.name == 'pre' and any(marker in text for marker in ['input:', 'output:', 'explanation:']):
                element.decompose()
                continue

    def _process_images(self, soup: BeautifulSoup) -> None:
        """Process images in the problem content"""
        for img in soup.find_all('img'):
            if not isinstance(img, Tag):
                continue

            alt_text = str(img.get('alt', 'Image'))
            src = str(img.get('src', ''))

            # Skip empty images
            if not src:
                img.decompose()
                continue

            # Handle example vs description images
            if self._is_example_image(img):
                self.example_images.append({'alt': alt_text, 'src': src})
                img.decompose()
            else:
                # Format description images
                img_block = f"\n[{COLORS['image_link']}]Image: {alt_text if alt_text else 'Problem illustration'}\nURL: {src}[/]\n"
                img.replace_with(BeautifulSoup(img_block, 'html.parser'))

    def _format_text_elements(self, soup: BeautifulSoup) -> None:
        """Format code and text styling elements"""
        # Format code elements
        for code in soup.find_all('code'):
            code.replace_with(BeautifulSoup(f'`{code.text}`', 'html.parser'))

        # Format styling elements
        for tag in soup.find_all(['strong', 'em', 'b', 'i']):
            if not isinstance(tag, Tag):
                continue
            text = tag.text.strip()
            if tag.name in ['strong', 'b']:
                tag.replace_with(BeautifulSoup(f"**{text}**", 'html.parser'))
            elif tag.name in ['em', 'i']:
                tag.replace_with(BeautifulSoup(f"_{text}_", 'html.parser'))

        # Format pre elements
        for pre in soup.find_all('pre'):
            lines = pre.text.strip().split('\n')
            formatted = '\n'.join(f'    {line}' for line in lines)
            pre.replace_with(BeautifulSoup(f'\n```\n{formatted}\n```\n', 'html.parser'))

    def _clean_example_text(self, text: str) -> str:
        """Remove any remaining example text from the formatted content"""
        lines = []
        skip_line = False

        for line in text.split('\n'):
            lower_line = line.lower()
            # Skip example headers
            if 'example' in lower_line and any(char.isdigit() for char in lower_line):
                skip_line = True
                continue

            if not skip_line:
                lines.append(line)

            # Stop skipping after empty line
            if skip_line and line.strip() == '':
                skip_line = False

        return '\n'.join(lines)

    def _extract_examples_from_html(self) -> List[Dict]:
        """Extract examples and their content from HTML"""
        soup = BeautifulSoup(self.content, 'html.parser')

        # Find all examples
        example_containers = []
        current_example = None
        example_num = 0

        # First pass: find example headers
        for element in soup.find_all(['p', 'pre', 'img', 'strong']):
            if not isinstance(element, Tag):
                continue

            text = element.get_text().strip().lower()

            # New example detected
            if 'example' in text and any(char.isdigit() for char in text):
                example_num += 1
                current_example = {
                    'num': example_num,
                    'title': element.get_text().strip(),
                    'sections': [('title', element.get_text().strip())],
                    'input': '',
                    'output': '',
                    'explanation': '',
                    'images': []
                }
                example_containers.append(current_example)
                continue

            # Process elements within an example
            if current_example:
                # Image handling
                if element.name == 'img':
                    alt_text = str(element.get('alt', 'Image'))
                    src = str(element.get('src', ''))
                    if src:
                        current_example['images'].append({'alt': alt_text, 'src': src})
                        current_example['sections'].append(('image', {'alt': alt_text, 'src': src}))
                # Pre element (usually input/output)
                elif element.name == 'pre':
                    for line in element.get_text().strip().split('\n'):
                        line = line.strip()
                        if line.lower().startswith('input:'):
                            content = line[6:].strip()
                            current_example['input'] = content
                            current_example['sections'].append(('input', content))
                        elif line.lower().startswith('output:'):
                            content = line[7:].strip()
                            current_example['output'] = content
                            current_example['sections'].append(('output', content))
                        elif line.lower().startswith('explanation:'):
                            content = line[12:].strip()
                            current_example['explanation'] = content
                            current_example['sections'].append(('explanation', content))
                # Other text (explanation)
                elif element.name == 'p' and not any(marker in text for marker in ['example', 'input:', 'output:']):
                    if text:
                        current_example['sections'].append(('explanation_text', text))

        # Add stored example images to appropriate examples
        self._match_images_to_examples(example_containers)

        return example_containers

    def _match_images_to_examples(self, examples: List[Dict]) -> None:
        """Match stored example images to their corresponding examples"""
        for example in examples:
            for img in self.example_images:
                img_alt = img.get('alt', '').lower()
                if f"example {example['num']}" in img_alt:
                    example['sections'].append(('image', img))

    def _format_test_cases(self) -> str:
        """Format examples for display"""
        examples_data = self._extract_examples_from_html()

        # Handle no examples case
        if not examples_data:
            if self.test_cases:
                # Use test cases as fallback
                return self._format_fallback_test_cases()
            return "\n[italic dim]No examples available for this problem.[/]"

        # Format example sections
        test_cases = []
        for example in examples_data:
            formatted_parts = []

            # Process each section type
            for section_type, content in example['sections']:
                if section_type == 'title':
                    formatted_parts.append(f"[{COLORS['section_title']}]{content}[/]")
                elif section_type == 'input':
                    formatted_parts.append(f"[{COLORS['input_label']}]Input:[/] {content}")
                elif section_type == 'output':
                    formatted_parts.append(f"[{COLORS['output_label']}]Output:[/] {content}")
                elif section_type == 'explanation':
                    formatted_parts.append(f"[{COLORS['explanation_label']}]Explanation:[/] {content}")
                elif section_type == 'image':
                    if isinstance(content, dict):
                        src = content.get('src', '')
                        alt = content.get('alt', '')
                        if src:
                            formatted_parts.append(
                                f"[{COLORS['image_link']}]Image: {alt if alt else 'Example illustration'}\n"
                                f"URL: {src}[/]"
                            )
                elif section_type == 'explanation_text':
                    formatted_parts.append(content)

            test_cases.append("\n".join(formatted_parts))

        return "\n\n" + "\n\n".join(test_cases)

    def _format_fallback_test_cases(self) -> str:
        """Format test cases from raw test case data when HTML parsing fails"""
        test_cases = []
        for i, test_case in enumerate(self.test_cases, 1):
            if not test_case.strip():
                continue

            lines = test_case.split('\n')
            if not lines:
                continue

            input_text = lines[0]
            output_text = lines[1] if len(lines) > 1 else ""

            test_cases.append(
                f"[{COLORS['section_title']}]Example {i}:[/]\n" +
                f"[{COLORS['input_label']}]Input:[/] {input_text}\n" +
                f"[{COLORS['output_label']}]Output:[/] {output_text}"
            )

        return "\n\n" + "\n\n".join(test_cases)

    def _format_stats(self) -> str:
        """Format problem statistics"""
        stats = {
            'Acceptance Rate': self.stats.get('acRate', 'N/A'),
            'Total Accepted': self.stats.get('totalAccepted', 'N/A'),
            'Total Submissions': self.stats.get('totalSubmission', 'N/A')
        }

        formatted = [f"[{COLORS['section_title']}]Problem Statistics[/]\n"]
        for label, value in stats.items():
            formatted.append(f"[{COLORS['stats_label']}]{label}:[/] {value}")

        return "\n".join(formatted)

    def display(self):
        """Display problem details in a three-panel layout"""
        console.clear()
        console.print()

        # Create layout
        layout = Layout()
        layout.split_row(
            Layout(name="main", ratio=2),
            Layout(name="side", ratio=1)
        )
        layout["side"].split_column(
            Layout(name="examples", ratio=3),
            Layout(name="stats", ratio=1)
        )

        # Update panels
        layout["main"].update(Panel(
            Markdown(self._format_description(self.content)),
            title=self._create_header(),
            box=STYLES['box_style'],
            border_style=COLORS['border'],
            padding=STYLES['panel_padding']
        ))

        layout["examples"].update(Panel(
            self._format_test_cases(),
            title=f"[{COLORS['section_title']}]Examples[/]",
            box=STYLES['box_style'],
            border_style=COLORS['border'],
            padding=STYLES['panel_padding']
        ))

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