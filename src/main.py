import os
import time
from pathlib import Path
from dotenv import load_dotenv

from discord import Bot, Intents, InteractionContextType, IntegrationType


def main() -> None:
    intents = Intents.default()
    intents.members = True
    bot = Bot(
        intents=intents,
        owner_id=969254887621820526,
        auto_sync_commands=True,
        default_command_contexts={
            InteractionContextType.guild
        },
        default_command_integration_types={
            IntegrationType.guild_install
        }
    )

    cogs_directory = Path(__file__).resolve().parent / "cogs"
    for path in sorted(cogs_directory.glob("*.py")):
        if not path.name.startswith("_"):
            bot.load_extension(f"cogs.{path.stem}")

    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / ".env"
    load_dotenv(env_file, override=True)

    while not (token := os.getenv("TOKEN")):
        print(f"TOKEN is not set in {env_file}; waiting for it to be added...", flush=True)
        time.sleep(10)
        load_dotenv(env_file, override=True)

    bot.run(token)


if __name__ == "__main__":
    main()
