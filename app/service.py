from __future__ import annotations

import hashlib
import json
import threading
import uuid
import weakref
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Payload, TransformationCache
from app.transformer import Transformer


class TransformationCacheService:
    """Coordinates transformation caching and payload deduplication.

    A lock is maintained per source value so that two concurrent requests inside
    the same service process cannot call the transformer twice for the same value.
    The database unique constraint remains the source of truth for persistence.
    """

    def __init__(self, transformer: Transformer) -> None:
        self._transformer = transformer
        self._locks_guard = threading.Lock()
        self._locks: weakref.WeakValueDictionary[str, threading.Lock] = weakref.WeakValueDictionary()

    def create_payload(self, session: Session, list_1: list[str], list_2: list[str]) -> Payload:
        fingerprint = self._fingerprint(list_1, list_2)
        existing = session.scalar(select(Payload).where(Payload.fingerprint == fingerprint))
        if existing is not None:
            return existing

        all_values = dict.fromkeys((*list_1, *list_2))
        transformed = self._get_or_transform_values(session, all_values.keys())
        output_values = [
            value
            for pair in zip(list_1, list_2, strict=True)
            for value in (transformed[pair[0]], transformed[pair[1]])
        ]

        payload = Payload(
            id=str(uuid.uuid4()),
            fingerprint=fingerprint,
            output=", ".join(output_values),
        )
        session.add(payload)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            existing = session.scalar(select(Payload).where(Payload.fingerprint == fingerprint))
            if existing is None:
                raise
            return existing

        session.refresh(payload)
        return payload

    def get_payload(self, session: Session, payload_id: str) -> Payload | None:
        return session.get(Payload, payload_id)

    def _get_or_transform_values(
        self, session: Session, values: Iterable[str]
    ) -> dict[str, str]:
        transformed: dict[str, str] = {}
        for value in values:
            cached = session.scalar(
                select(TransformationCache).where(TransformationCache.source_text == value)
            )
            if cached is not None:
                transformed[value] = cached.transformed_text
                continue

            with self._lock_for(value):
                # Another request may have filled the cache while this request waited.
                cached = session.scalar(
                    select(TransformationCache).where(TransformationCache.source_text == value)
                )
                if cached is None:
                    result = self._transformer.transform(value)
                    cached = TransformationCache(source_text=value, transformed_text=result)
                    session.add(cached)
                    try:
                        session.commit()
                    except IntegrityError:
                        session.rollback()
                        cached = session.scalar(
                            select(TransformationCache).where(
                                TransformationCache.source_text == value
                            )
                        )
                        if cached is None:
                            raise

                transformed[value] = cached.transformed_text
        return transformed

    def _lock_for(self, key: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(key, threading.Lock())

    @staticmethod
    def _fingerprint(list_1: list[str], list_2: list[str]) -> str:
        canonical = json.dumps(
            {"list_1": list_1, "list_2": list_2},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
