import typer
from src import show, details
from src.commands.login import login

app = typer.Typer()

app.command(name="show")(show)
app.command(name="user-details")(details)
app.command(name="login")(login)

if __name__ == "__main__":
    app()