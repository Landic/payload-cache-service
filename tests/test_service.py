from app.service import TransformationCacheService


def test_fingerprint_is_order_sensitive_for_each_list():
    first = TransformationCacheService._fingerprint(["a", "b"], ["c", "d"])
    second = TransformationCacheService._fingerprint(["b", "a"], ["c", "d"])
    third = TransformationCacheService._fingerprint(["a", "b"], ["d", "c"])

    assert first != second
    assert first != third
