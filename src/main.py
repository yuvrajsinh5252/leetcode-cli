import typer
from commands.show import show
from commands.list import list

app = typer.Typer()

app.command()(show)
app.command()(list)

if __name__ == "__main__":
  app()
