from rich.console import Console
from rich.table import Table

console = Console()

def create_problems_table(data):
  table = Table(title="LeetCode Problems Count")
  table.add_column("Difficulty", style="cyan")
  table.add_column("Count", justify="right", style="green")

  for item in data['allQuestionsCount']:
    table.add_row(item['difficulty'], str(item['count']))
  return table

def create_user_stats_table(data):
  if not data.get('matchedUser'):
    return None

  table = Table(title="Your Statistics")
  table.add_column("Difficulty", style="cyan")
  table.add_column("Solved", justify="right", style="green")
  table.add_column("Beats", justify="right", style="yellow")

  user_data = data['matchedUser']
  solved = user_data['submitStatsGlobal']['acSubmissionNum']
  beats = user_data['problemsSolvedBeatsStats']

  difficulties = ['Easy', 'Medium', 'Hard']
  for diff in difficulties:
    solved_count = next((item['count'] for item in solved if item['difficulty'] == diff), 0)
    beats_percent = next((f"{item['percentage']:.1f}%" for item in beats if item['difficulty'] == diff), "N/A")
    table.add_row(diff, str(solved_count), beats_percent)

  return table

def display_problem_stats(data):
    problems_table = create_problems_table(data)
    console.print(problems_table)

    user_stats = create_user_stats_table(data)
    if user_stats:
        console.print("\n")
        console.print(user_stats)