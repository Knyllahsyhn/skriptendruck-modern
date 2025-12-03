"""Haupteinstiegspunkt für die CLI."""
from .cli.commands import app


def main() -> None:
    """Hauptfunktion."""
    app()


if __name__ == "__main__":
    main()
