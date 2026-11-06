import threading
import time

from fastapi.testclient import TestClient

from app import main


def upload(client, name, data, content_type="text/plain"):
    return client.post("/api/sources", files={"file": (name, data, content_type)})


def wait_for_job(client, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/jobs/{job_id}").json()
        if body["status"] != "running":
            return body
        time.sleep(0.05)
    raise AssertionError("the job did not finish in time")


# ---------- the first 6 tests ----------
def test_status_has_expected_keys():
    with TestClient(main.app) as client:
        r = client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] == "ok"
    assert {"up", "model", "model_installed"} <= set(body["ollama"])
    assert isinstance(body["documents"], int)
    assert isinstance(body["runs"], int)


def test_empty_answer_is_rejected():
    with TestClient(main.app) as client:
        r = client.post("/api/verify/answer", json={"question": "x", "answer": ""})
    assert r.status_code == 422


def test_too_long_answer_is_rejected():
    with TestClient(main.app) as client:
        r = client.post("/api/verify/answer", json={"question": "x", "answer": "a" * 5001})
    assert r.status_code == 422


def test_verify_answer_returns_the_analysis(monkeypatch):
    fake = {"run_id": 7, "risk": {"level": "Safe", "score": 0}}
    monkeypatch.setattr(main, "verify_answer", lambda question, answer: fake)
    with TestClient(main.app) as client:
        r = client.post("/api/verify/answer", json={"question": "q", "answer": "a"})
    assert r.status_code == 200
    assert r.json() == fake


def test_unknown_run_is_404():
    with TestClient(main.app) as client:
        assert client.get("/api/runs/999999").status_code == 404


def test_runs_list_is_a_list():
    with TestClient(main.app) as client:
        r = client.get("/api/runs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------- documents ----------
def test_upload_txt_works(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        r = upload(client, "rules.txt", b"Para one.\n\nPara two.")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "rules.txt"
    assert body["chunks"] == 2
    assert body["status"] == "Indexed"
    assert (tmp_path / "rules.txt").exists()


def test_upload_rejects_other_file_types(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        r = upload(client, "evil.exe", b"MZ", "application/octet-stream")
    assert r.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_upload_rejects_big_files(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        r = upload(client, "big.txt", b"a" * (main.MAX_UPLOAD_BYTES + 1))
    assert r.status_code == 413


def test_upload_strips_folder_names(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        r = upload(client, "../../evil.txt", b"Some text.")
    assert r.status_code == 200
    assert r.json()["name"] == "evil.txt"
    assert (tmp_path / "evil.txt").exists()
    assert not (tmp_path.parent / "evil.txt").exists()


def test_upload_rejects_non_text_and_empty_files(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        assert upload(client, "bad.txt", b"\xff\xfe\xfa").status_code == 400
        assert upload(client, "empty.txt", b"   ").status_code == 400


def test_list_content_and_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        upload(client, "a.txt", b"Hello world.")
        assert [s["name"] for s in client.get("/api/sources").json()] == ["a.txt"]
        assert client.get("/api/sources/a.txt/content").json()["text"] == "Hello world."
        assert client.delete("/api/sources/a.txt").status_code == 200
        assert client.get("/api/sources").json() == []


def test_delete_unknown_source_is_404(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DOCS_DIR", tmp_path)
    with TestClient(main.app) as client:
        assert client.delete("/api/sources/nothing.txt").status_code == 404


# ---------- dashboard numbers ----------
def test_stats_has_the_dashboard_numbers():
    with TestClient(main.app) as client:
        r = client.get("/api/stats")
    body = r.json()
    assert r.status_code == 200
    assert set(body["by_level"]) == {"Safe", "Warning", "Critical"}
    assert set(body["claims"]) == {"Supported", "Contradicted", "Insufficient evidence"}
    assert isinstance(body["total_checked"], int)
    assert isinstance(body["recent"], list)


# ---------- background jobs ----------
def test_job_finishes_with_result_and_steps(monkeypatch):
    def fake(question, progress=None):
        progress("Working", [{"step": "task_started", "detail": question, "time": 0}])
        return {"run_id": 1}

    monkeypatch.setattr(main, "verify_question", fake)
    with TestClient(main.app) as client:
        job_id = client.post("/api/verify/question", json={"question": "q"}).json()["job_id"]
        body = wait_for_job(client, job_id)
    assert body["status"] == "done"
    assert body["result"] == {"run_id": 1}
    assert len(body["steps"]) == 1


def test_failed_job_does_not_leak_details(monkeypatch):
    def broken(question, progress=None):
        raise RuntimeError("secret detail")

    monkeypatch.setattr(main, "verify_question", broken)
    with TestClient(main.app) as client:
        job_id = client.post("/api/verify/question", json={"question": "q"}).json()["job_id"]
        body = wait_for_job(client, job_id)
    assert body["status"] == "error"
    assert "secret detail" not in body["error"]


def test_only_one_verification_runs_at_a_time(monkeypatch):
    release = threading.Event()

    def slow(question, progress=None):
        release.wait(timeout=5)
        return {"run_id": 1}

    monkeypatch.setattr(main, "verify_question", slow)
    with TestClient(main.app) as client:
        first = client.post("/api/verify/question", json={"question": "a"})
        second = client.post("/api/verify/question", json={"question": "b"})
        release.set()
        assert first.status_code == 200
        assert second.status_code == 409
        wait_for_job(client, first.json()["job_id"])