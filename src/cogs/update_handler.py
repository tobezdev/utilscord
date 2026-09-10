import asyncio
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from discord import (
    ApplicationContext,
    Bot,
    ChannelType,
    DMChannel,
    IntegrationType,
    InteractionContextType,
)
from discord.commands import slash_command
from discord.ext.commands import Cog, is_owner


REPOSITORY = "https://github.com/tobezdev/Utilscord.git"
BRANCH = "main"
COMMIT_HASH = re.compile(r"^[0-9a-fA-F]{7,40}$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class UpdateError(RuntimeError):
    pass


def _run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise UpdateError(detail[-1] if detail else "The update command failed.")
    return result.stdout.strip()


def _is_ancestor(commit: str, branch_tip: str, cwd: Path) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, branch_tip],
        cwd=cwd,
        check=False,
    )
    return result.returncode == 0


def update_project(commit: str) -> str:
    """Fetch main, verify the requested commit belongs to it, and install its files."""
    if not COMMIT_HASH.fullmatch(commit):
        raise UpdateError("Commit must be a 7-40 character hexadecimal hash.")

    with tempfile.TemporaryDirectory(prefix="utilscord-update-") as directory:
        checkout = Path(directory) / "checkout"
        _run(["git", "clone", "--filter=blob:none", "--no-checkout", REPOSITORY, str(checkout)])
        _run(["git", "fetch", "origin", BRANCH], cwd=checkout)

        resolved = _run(["git", "rev-parse", f"{commit}^{{commit}}"], cwd=checkout)
        main_tip = _run(["git", "rev-parse", f"origin/{BRANCH}"], cwd=checkout)
        if not _is_ancestor(resolved, main_tip, checkout):
            raise UpdateError(f"{commit} is not an ancestor of origin/{BRANCH}.")

        _run(["git", "checkout", "--detach", resolved], cwd=checkout)

        # Keep runtime state and secrets in the Pterodactyl volume intact.
        for name in ("pyproject.toml", "uv.lock"):
            source = checkout / name
            if source.exists():
                shutil.copy2(source, PROJECT_ROOT / name)

        source_directory = checkout / "src"
        target_directory = PROJECT_ROOT / "src"
        if not source_directory.is_dir():
            raise UpdateError("The selected commit does not contain a src directory.")
        shutil.copytree(source_directory, target_directory, dirs_exist_ok=True)

    return resolved


class UpdateHandler(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command(
        name="update",
        description="Update the bot to a specific commit hash.",
        integration_types={IntegrationType.user_install},
        contexts={InteractionContextType.bot_dm},
    )
    @is_owner()
    async def update(self, ctx: ApplicationContext, commit: str):
        if ctx.guild is not None or not isinstance(ctx.channel, DMChannel) or ctx.channel.type is not ChannelType.private:
            return await ctx.respond("This command can only be used in a direct DM with me.", ephemeral=True)

        await ctx.defer(ephemeral=True)
        try:
            resolved = await asyncio.to_thread(update_project, commit.strip())
        except (OSError, subprocess.SubprocessError, UpdateError) as error:
            return await ctx.followup.send(f"Update failed: {error}", ephemeral=True)

        await ctx.followup.send(
            f"Updated to `{resolved[:12]}` from `origin/{BRANCH}`.",
            ephemeral=True,
        )


def setup(bot: Bot) -> None:
    bot.add_cog(UpdateHandler(bot))
