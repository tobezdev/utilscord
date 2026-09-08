import os
from pathlib import Path
from dotenv import load_dotenv

from discord import Bot, Intents, InteractionContextType, IntegrationType


def main() -> None:
    i = Intents.default()
    i.message_content = True
    bot = Bot(
        intents=i,
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

    load_dotenv()
    token = os.getenv("TOKEN")
    if token:
        bot.run(token)


if __name__ == "__main__":
    main()
