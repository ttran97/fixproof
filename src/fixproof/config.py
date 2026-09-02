from __future__ import annotations

import os
import re
from pathlib import Path


ALLOWED_ENVIRONMENT_KEYS = frozenset(
    {
        "OPENAI_API_KEY",
        "FIXPROOF_MODEL",
    }
)

ENVIRONMENT_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EnvironmentFileError(ValueError):
    """Raised when a FixProof environment file is malformed."""


def _parse_value(raw_value: str, path: Path, line_number: int) -> str:
    value = raw_value.strip()
    if not value:
        return ""

    if value[0] in {"'", '"'}:
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise EnvironmentFileError(
                f"Unterminated quoted value in '{path}' on line {line_number}."
            )
        return value[1:-1]

    return value


def load_environment_file(
    path: Path,
    *,
    required: bool = False,
) -> tuple[str, ...]:
    """Load only FixProof's approved settings without overriding the shell."""

    path = path.resolve()
    if not path.is_file():
        if required:
            raise EnvironmentFileError(f"Environment file not found: '{path}'.")
        return ()

    loaded: list[str] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise EnvironmentFileError(
                f"Expected KEY=VALUE in '{path}' on line {line_number}."
            )

        raw_key, raw_value = line.split("=", 1)
        key = raw_key.strip()
        if not ENVIRONMENT_KEY_PATTERN.fullmatch(key):
            raise EnvironmentFileError(
                f"Invalid environment key in '{path}' on line {line_number}."
            )
        if key not in ALLOWED_ENVIRONMENT_KEYS:
            continue

        value = _parse_value(raw_value, path, line_number)
        if key not in os.environ and value:
            os.environ[key] = value
            loaded.append(key)

    return tuple(loaded)


def find_environment_file(start: Path) -> Path | None:
    """Find the nearest .env while walking from a file/directory to its root."""

    current = start.resolve()
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None
