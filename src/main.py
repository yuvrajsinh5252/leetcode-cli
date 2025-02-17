import typer
from commands.show import show
from src.commands.details import details

app = typer.Typer()

app.command()(show)
app.command()(details)

if __name__ == "__main__":
  app()
