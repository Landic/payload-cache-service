def payload():
    return {
        "list_1": ["first string", "second string", "third string"],
        "list_2": ["other string", "another string", "last string"],
    }


def test_create_and_read_payload(client):
    response = client.post("/payload", json=payload())
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Payload created"
    assert body["id"]

    read_response = client.get(f"/payload/{body['id']}")
    assert read_response.status_code == 200
    assert read_response.json() == {
        "output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
    }


def test_reuses_transformed_values_and_payload_id(client, spy_transformer):
    data = payload()
    first = client.post("/payload", json=data)
    second = client.post("/payload", json=data)

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert sorted(spy_transformer.calls) == sorted(
        ["first string", "second string", "third string", "other string", "another string", "last string"]
    )
    assert len(spy_transformer.calls) == 6


def test_reuses_cache_across_different_payloads(client, spy_transformer):
    first = client.post(
        "/payload",
        json={"list_1": ["one", "two"], "list_2": ["three", "four"]},
    )
    second = client.post(
        "/payload",
        json={"list_1": ["one", "two"], "list_2": ["five", "six"]},
    )

    assert first.status_code == second.status_code == 201
    assert len(spy_transformer.calls) == 6
    assert "one" not in spy_transformer.calls[4:]
    assert "two" not in spy_transformer.calls[4:]


def test_rejects_different_lengths(client):
    response = client.post(
        "/payload",
        json={"list_1": ["one"], "list_2": ["two", "three"]},
    )
    assert response.status_code == 422
    assert "same length" in response.json()["detail"]


def test_missing_payload_returns_404(client):
    response = client.get("/payload/does-not-exist")
    assert response.status_code == 404
