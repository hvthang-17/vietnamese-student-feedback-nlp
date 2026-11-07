"""Explicit local server and migration commands."""
import argparse
from .database import Database
from .settings import Settings


def main():
    parser = argparse.ArgumentParser(description="Feedback API lifecycle")
    parser.add_argument("command", choices=["serve", "migrate"])
    parser.add_argument("--env-file", help="Explicit dotenv file; process environment takes precedence")
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        from pathlib import Path
        target = Path(args.env_file)
        if not target.is_file():
            parser.error("Environment file does not exist")
        load_dotenv(target, override=False)
    settings = Settings.from_env()
    if args.command == "migrate":
        Database(settings.database_path, settings.database_timeout).initialize()
        print("Database migrations completed.")
    else:
        import uvicorn
        uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port,
                    log_level=settings.log_level)


if __name__ == "__main__":
    main()
