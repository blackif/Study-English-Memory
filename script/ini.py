from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESERVE_DIRS = {"templates", "script"}
PRESERVE_FILES = {"SKILL.md", ".gitignore"}
CONFIRMATION = "RESET"


def main() -> None:
    print(f"Repository root: {ROOT}")
    print("This utility deletes generated learning data under data/, curriculum/, history/, and tests/.")
    print(f"Type {CONFIRMATION} to continue:")
    if input().strip() != CONFIRMATION:
        print("Cancelled.")
        return

    for dirname in ("data", "curriculum", "history", "tests"):
        directory = ROOT / dirname
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass

    print("Reset complete. templates/, SKILL.md, and script/ were preserved.")


if __name__ == "__main__":
    main()
