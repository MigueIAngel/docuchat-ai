import json

from fastapi.testclient import TestClient


def parse_events(body: str) -> list[tuple[str, object]]:
    events = []
    for block in body.strip().split("\n\n"):
        event_line, data_line = block.split("\n", 1)
        events.append(
            (event_line.removeprefix("event: "), json.loads(data_line.removeprefix("data: ")))
        )
    return events


def upload(client: TestClient, content: bytes, name: str = "policy.pdf"):
    return client.post("/api/documents", files={"file": (name, content, "application/pdf")})


def test_health_reports_demo_provider(client: TestClient) -> None:
    assert client.get("/api/health").json()["provider"] == "demo"


def test_upload_list_and_delete(client: TestClient, sample_pdf: bytes) -> None:
    response = upload(client, sample_pdf)
    assert response.status_code == 201
    document = response.json()
    assert document["pages"] == 2 and document["chunks"] >= 2

    assert [d["id"] for d in client.get("/api/documents").json()] == [document["id"]]
    assert client.delete(f"/api/documents/{document['id']}").status_code == 204
    assert client.get("/api/documents").json() == []
    assert client.delete(f"/api/documents/{document['id']}").status_code == 404


def test_rejects_non_pdf_files(client: TestClient) -> None:
    assert upload(client, b"hello", "notes.txt").status_code == 415
    assert upload(client, b"hello", "fake.pdf").status_code == 422


def test_chat_streams_sources_and_answer(client: TestClient, sample_pdf: bytes) -> None:
    upload(client, sample_pdf)
    response = client.post(
        "/api/chat", json={"question": "How much is the coworking reimbursement?"}
    )
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_events(response.text)
    names = [name for name, _ in events]
    assert names[0] == "sources" and names[-1] == "done"
    sources = events[0][1]
    # The expenses section lives on page 2 of the sample policy.
    assert sources[0]["filename"] == "policy.pdf"  # type: ignore[index]
    assert sources[0]["page"] == 2  # type: ignore[index]
    answer = "".join(data for name, data in events if name == "token")  # type: ignore[misc]
    assert "[1]" in answer


def test_chat_can_be_limited_to_documents(client: TestClient, sample_pdf: bytes) -> None:
    upload(client, sample_pdf)
    events = parse_events(
        client.post("/api/chat", json={"question": "VPN", "document_ids": ["missing"]}).text
    )
    assert events[0] == ("sources", [])


def test_chat_validates_input(client: TestClient) -> None:
    assert client.post("/api/chat", json={"question": ""}).status_code == 422
