"""The held-out set and the release gate (RAID v2 spec R13.1, R13.2, N1; AC38, AC39, AC41; task A8)."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from evals.heldout_rules import P1_CASES, check_key_order, missing_cases

HELDOUT = Path(__file__).resolve().parent.parent / "evals" / "heldout"


def test_the_28_p1_cases():
    assert len(P1_CASES) == 28 == len(set(P1_CASES))
    assert P1_CASES[:8] == ["A2", "A3", "A4", "A5", "A6", "A7", "A8", "A11"]


def test_ac38_each_committed_call_has_a_key_and_one_new_case():
    answers = sorted((HELDOUT / "answers").glob("*.json")) if (HELDOUT / "answers").exists() else []
    cases = []
    for answer_file in answers:
        answer = json.loads(answer_file.read_text(encoding="utf-8"))
        assert (HELDOUT / "calls" / answer["call"]).is_file(), answer_file.name
        assert answer["meeting_date"] and answer["writer"]
        cases.append(answer["case"])
    assert len(cases) == len(set(cases)) and set(cases) <= set(P1_CASES)


def test_missing_cases_lists_what_the_release_still_needs(tmp_path):
    (tmp_path / "answers").mkdir()
    (tmp_path / "answers" / "h01.json").write_text(json.dumps({"case": "A2"}), encoding="utf-8")
    assert missing_cases(tmp_path) == P1_CASES[1:]


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def _commit(repo, path, when):
    file = repo / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(path + when, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    env = {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", path],
                   check=True, env={**os.environ, **env})


def test_ac39_keys_committed_before_the_first_run_output(repo):
    _commit(repo, "evals/heldout/answers/h01.json", "2026-12-01T10:00:00")
    _commit(repo, "evals/heldout/outputs/run1/h01.json", "2026-12-02T10:00:00")
    assert check_key_order(repo) == []


def test_ac39_a_key_changed_after_a_run_is_reported(repo):
    _commit(repo, "evals/heldout/answers/h01.json", "2026-12-01T10:00:00")
    _commit(repo, "evals/heldout/outputs/run1/h01.json", "2026-12-02T10:00:00")
    _commit(repo, "evals/heldout/answers/h01.json", "2026-12-03T10:00:00")
    assert check_key_order(repo) == ["evals/heldout/answers/h01.json"]


def test_ac41_gate_exits_1_on_an_invented_date(tmp_path, monkeypatch):
    import evals.run_eval as run_eval

    (tmp_path / "answers").mkdir()
    (tmp_path / "calls").mkdir()
    (tmp_path / "outputs" / "run1").mkdir(parents=True)
    (tmp_path / "calls" / "c.txt").write_text("Ben Ortiz: I'll send the notes soon.", encoding="utf-8")
    key = {"call": "c.txt", "case": "C1", "meeting_date": "2026-12-01", "writer": "test", "items": [
        {"type": "Action", "summary": "Send notes", "owner": "Ben Ortiz", "owner_state": "Confirmed",
         "due_date": "Not stated", "evidence": "I'll send the notes soon."}]}
    (tmp_path / "answers" / "c.json").write_text(json.dumps(key), encoding="utf-8")
    output = {"sample": "c.txt", "model": "m", "run_date": "2026-12-01", "input_tokens": 1, "output_tokens": 1,
              "seconds": 1, "items": [{"type": "Action", "description": "Send the notes.", "owner": "Ben Ortiz",
                                       "owner_state": "Confirmed", "due_date": "2026-12-04",
                                       "source_quote": "I'll send the notes soon."}]}
    (tmp_path / "outputs" / "run1" / "c.json").write_text(json.dumps(output), encoding="utf-8")
    monkeypatch.setitem(run_eval.SETS, "heldout", (tmp_path / "answers", tmp_path / "calls", tmp_path / "outputs",
                                                   tmp_path / "report.md", "call"))
    monkeypatch.setattr(run_eval, "HELDOUT", tmp_path)
    monkeypatch.setattr(run_eval, "check_key_order", lambda root: [])
    assert run_eval.run(cached=True, model="m", set_name="heldout", runs=1, gate=True) == 1
    assert "| Invented dates (release gate: 0) | 1 |" in (tmp_path / "report.md").read_text(encoding="utf-8")
