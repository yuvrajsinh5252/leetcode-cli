import typer

from ..server.solution_manager import SolutionManager
from ..server.auth import Auth
from .test import map_lang

solution_manager = SolutionManager(Auth().get_session())

def edit(
  problem: str = typer.Argument(..., help="Problem name or id."),
  lang: str = typer.Argument("cpp", help="Programming language to use."),
  editor: str = typer.Option("code", '-e', '--editor', help="Code editor to use."),
):
  """Solves a problem by passing lang param and open it with your code editor."""
  question_data = solution_manager.get_question_data(problem).get('data', {}).get('question')

  if not question_data:
    typer.echo(f"Problem {problem} not found.")
    return

  def create_file_with_template(lang: str):
    with open(f"{question_data.get('titleSlug')}.{lang}", "w") as f:
      for snippet in question_data.get('codeSnippets', []):
          if snippet.get('langSlug').lower() == map_lang.get(lang):
            f.write(snippet.get('code'))
            return
      typer.echo(f"No template found for language {lang}")

  create_file_with_template(lang)

  import subprocess
  subprocess.run([editor, f"{question_data.get('titleSlug')}.{lang}"])