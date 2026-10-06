from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class SpyTransformer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def transform(self, value: str) -> str:
        self.calls.append(value)
        return value.upper()


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def spy_transformer() -> SpyTransformer:
    return SpyTransformer()


@pytest.fixture
def client(db_url: str, spy_transformer: SpyTransformer):
    settings = Settings(database_url=db_url)
    app = create_app(settings=settings, transformer=spy_transformer)
    with TestClient(app) as test_client:
        yield test_client
