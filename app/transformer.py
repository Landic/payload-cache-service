class Transformer:
    """Small stand-in for an external transformation service used by the task."""

    def transform(self, value: str) -> str:
        return value.upper()
