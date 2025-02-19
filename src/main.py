import typer
from src import show, details
from src.commands.login import login
from src.commands.submit import submit
from src.commands.test import test

app = typer.Typer()

app.command(name="show")(show)
app.command(name="user-details")(details)
app.command(name="login")(login)
app.command(name="submit")(submit)
app.command(name="test")(test)

if __name__ == "__main__":
    app()