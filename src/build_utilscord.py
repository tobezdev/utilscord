from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    if not (root / "pyproject.toml").is_file() or not (root / "uv.lock").is_file():
        raise SystemExit("Run this command from the Utilscord checkout using uv run build-utilscord.")

    output = root / "build"
    if output.is_symlink():
        raise SystemExit("Refusing to replace build/: it is a symbolic link.")

    # Finish exporting and copying before replacing a previous successful build.
    with TemporaryDirectory(prefix="utilscord-build-") as temporary:
        staging = Path(temporary)
        subprocess.run(
            [
                "uv", "export", "--locked", "--no-default-groups",
                "--no-emit-project", "--format", "requirements.txt",
                "--output-file", str(staging / "requirements.txt"), "--quiet",
            ],
            cwd=root,
            check=True,
        )
        source = root / "src"
        for path in sorted(source.rglob("*.py")):
            relative = path.relative_to(source)
            if path == Path(__file__).resolve() or any(
                part.startswith(".") or part == "__pycache__" or part.endswith(".egg-info")
                for part in relative.parts
            ):
                continue
            destination = staging / "src" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staging, output)
    print(f"Built {output}")


if __name__ == "__main__":
    main()
