import typer
from src import show, details

app = typer.Typer()

app.command()(show)
app.command()(details)

if __name__ == "__main__":
    app()