import typer
from src.commands import show
from src.commands.edit import edit
from src.server.api import get_daily_question

def daily(
  lang: str = typer.Argument("python", help="Programming language to use."),
  editor: str = typer.Option("code", '-e', help="Code editor to use."),
):
  """Check the daily problem."""
  result = get_daily_question()
  question = result['data']['activeDailyCodingChallengeQuestion']

  show(problem=question['question']['titleSlug'], layout=True)

  if editor:
    edit(problem=question['question']['titleSlug'], lang=lang, editor=editor)