from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx
from pydantic import AnyHttpUrl, Field, PositiveInt, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CliSettings(BaseSettings):
    """Validated CLI configuration.

    The assignment lists ``-h`` for both host and help. That is ambiguous, so
    the executable uses ``-H/--host`` and keeps ``-h/--help`` for conventional CLI help.
    """

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_prog_name="cache-cli",
        cli_kebab_case=True,
        cli_shortcuts={
            "repeat": ["r"],
            "input": ["i"],
            "json": ["j"],
            "output": ["o"],
        },
        env_prefix="",
    )

    host: AnyHttpUrl = "http://localhost:8000"
    repeat: PositiveInt = 1
    input_source: str = Field("-", alias="input")
    json_data: str | None = Field(None, alias="json")
    output: str = "-"

    @model_validator(mode="after")
    def validate_sources(self) -> "CliSettings":
        if self.json_data is not None and self.input_source != "-":
            raise ValueError("use either --input or --json, not both")
        return self


def parse_settings(args: list[str] | None = None) -> CliSettings:
    """Parse CLI arguments while resolving the assignment's ``-h`` collision.

    ``-h`` remains normal help when used alone. When a value follows it, the
    argument is treated as the short form of ``--host``. Pydantic Settings still
    performs all actual parsing and validation.
    """
    raw_args = list(sys.argv[1:] if args is None else args)
    normalized: list[str] = []
    index = 0
    while index < len(raw_args):
        current = raw_args[index]
        if current == "-h" and index + 1 < len(raw_args) and not raw_args[index + 1].startswith("-"):
            normalized.extend(["--host", raw_args[index + 1]])
            index += 2
            continue
        normalized.append(current)
        index += 1
    return CliSettings(_cli_parse_args=normalized)


def _read_request(settings: CliSettings) -> dict[str, Any]:
    if settings.json_data is not None:
        raw = settings.json_data
    elif settings.input_source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(settings.input_source).read_text(encoding="utf-8")

    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON input: {exc}") from exc

    if not isinstance(value, dict) or "list_1" not in value or "list_2" not in value:
        raise ValueError("input JSON must contain list_1 and list_2")
    if not isinstance(value["list_1"], list) or not isinstance(value["list_2"], list):
        raise ValueError("list_1 and list_2 must be arrays")
    if len(value["list_1"]) != len(value["list_2"]):
        raise ValueError("list_1 and list_2 must have the same length")
    if not all(isinstance(item, str) for item in value["list_1"] + value["list_2"]):
        raise ValueError("list_1 and list_2 must contain strings")
    return value


def run(settings: CliSettings) -> None:
    request_data = _read_request(settings)
    base_url = str(settings.host).rstrip("/")

    results: list[dict[str, str]] = []
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        for _ in range(settings.repeat):
            create_response = client.post("/payload", json=request_data)
            create_response.raise_for_status()
            payload_id = create_response.json()["id"]

            read_response = client.get(f"/payload/{payload_id}")
            read_response.raise_for_status()
            results.append({"id": payload_id, "output": read_response.json()["output"]})

    rendered = json.dumps(results[0] if len(results) == 1 else results, ensure_ascii=False, indent=2)
    if settings.output == "-":
        sys.stdout.write(rendered + "\n")
    else:
        Path(settings.output).write_text(rendered + "\n", encoding="utf-8")


def main() -> None:
    try:
        settings = parse_settings()
        run(settings)
    except (OSError, ValueError, httpx.HTTPError) as exc:
        print(f"cache-cli: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
