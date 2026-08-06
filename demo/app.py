"""
demo/app.py — Data Pipeline & Observability Demo Backend
========================================================
Run from project root:
    .venv\\Scripts\\python.exe demo/app.py
Then open: http://localhost:5050
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from threading import Lock

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT))

# ── Flask import (graceful error if not installed) ───────────────────────────
try:
    from flask import Flask, Response, jsonify, send_from_directory, request
    from flask import stream_with_context
except ImportError:
    print("\n[ERROR] Flask not installed.")
    print("  Run:  .venv\\Scripts\\pip install flask")
    sys.exit(1)

# ── Constants ────────────────────────────────────────────────────────────────
DATA_DIR    = ROOT / "data"
SCRIPT_DIR  = ROOT / "script"
VENV_PY     = ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON      = str(VENV_PY) if VENV_PY.exists() else sys.executable

PHASES = {
    "phase1":    {"script": "run_phase1.py",         "label": "Phase 1 — Baseline"},
    "corruption":{"script": "run_corruption_flow.py", "label": "Corruption & Repair"},
}

# ── In-memory run state ──────────────────────────────────────────────────────
_state_lock = Lock()
_run_state: dict = {"running": None, "last_run": {}, "logs": {}}


app = Flask(__name__, static_folder=str(Path(__file__).parent))
app.config["SECRET_KEY"] = "chickenguy-demo-2026"


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════

def _load_json(path: Path, fallback=None):
    """Load JSON file; return fallback dict/list on any error."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Cannot load {path}: {exc}")
    return fallback if fallback is not None else {}


def _sse(data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_script_generator(phase: str):
    """Run a pipeline script as subprocess and yield SSE lines."""
    cfg = PHASES.get(phase)
    if not cfg:
        yield _sse({"type": "error", "msg": f"Unknown phase: {phase}"})
        return

    script = SCRIPT_DIR / cfg["script"]
    if not script.exists():
        yield _sse({"type": "error", "msg": f"Script not found: {script}"})
        return

    # Mark running
    with _state_lock:
        _run_state["running"] = phase
        _run_state["logs"][phase] = []

    yield _sse({"type": "start", "phase": phase, "label": cfg["label"]})
    time.sleep(0.05)

    try:
        proc = subprocess.Popen(
            [PYTHON, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT),
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
        )

        for raw_line in proc.stdout:
            line = raw_line.rstrip()
            if not line:
                continue
            with _state_lock:
                _run_state["logs"].setdefault(phase, []).append(line)

            # Classify log line for frontend coloring
            ltype = "log"
            if any(k in line for k in ["ERROR", "Exception", "Traceback", "fatal"]):
                ltype = "error"
            elif any(k in line for k in ["Warning", "WARN", "warn"]):
                ltype = "warn"
            elif any(k in line for k in ["===", "Completed", "PASSED", "FRESH", "Done"]):
                ltype = "success"
            elif any(k in line for k in ["Fetched", "Cleaned", "Built", "Saved", "Generating",
                                          "Running", "Evaluating", "Using", "Corrupted", "Repaired"]):
                ltype = "info"

            yield _sse({"type": "log", "ltype": ltype, "line": line})
            time.sleep(0.01)

        proc.wait()
        rc = proc.returncode

    except Exception as exc:
        yield _sse({"type": "error", "msg": str(exc)})
        with _state_lock:
            _run_state["running"] = None
        return

    # Mark done
    with _state_lock:
        _run_state["running"] = None
        _run_state["last_run"][phase] = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "returncode": rc,
        }

    if rc == 0:
        yield _sse({"type": "done", "phase": phase, "success": True})
    else:
        yield _sse({"type": "done", "phase": phase, "success": False,
                    "msg": f"Process exited with code {rc}"})


# ════════════════════════════════════════════════════════════════════════════
# Routes — Static
# ════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory(str(Path(__file__).parent), "index.html")


# ════════════════════════════════════════════════════════════════════════════
# Routes — API
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/status")
def api_status():
    """Return current run state and last run metadata."""
    with _state_lock:
        state = dict(_run_state)
        state.pop("logs", None)  # don't send full logs in status
    return jsonify({"ok": True, "state": state})


@app.route("/api/run/<phase>")
def api_run(phase: str):
    """SSE endpoint: stream pipeline execution logs."""
    if phase not in PHASES:
        return jsonify({"ok": False, "error": f"Unknown phase '{phase}'"}), 400

    with _state_lock:
        if _run_state["running"] is not None:
            return jsonify({
                "ok": False,
                "error": f"Pipeline '{_run_state['running']}' already running"
            }), 409

    return Response(
        stream_with_context(_run_script_generator(phase)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/api/results")
def api_results():
    """Return all pipeline result JSON files (with fallback empty dicts)."""

    # ── Quality files ────────────────────────────────────────────────────
    q_dir = DATA_DIR / "quality"
    baseline_q   = _load_json(q_dir / "baseline_quality.json",   {"success": None})
    corrupted_q  = _load_json(q_dir / "corrupted_quality.json",  {"success": None})
    repaired_q   = _load_json(q_dir / "repaired_quality.json",   {"success": None})
    freshness    = _load_json(q_dir / "freshness_report.json",   {})
    freshness_c  = _load_json(q_dir / "freshness_report_corrupted.json", {})
    freshness_r  = _load_json(q_dir / "freshness_report_repaired.json",  {})

    # ── Metrics files ────────────────────────────────────────────────────
    r_dir = DATA_DIR / "results"
    baseline_m   = _load_json(r_dir / "baseline_metrics.json",   {})
    corrupted_m  = _load_json(r_dir / "corrupted_metrics.json",  {})
    repaired_m   = _load_json(r_dir / "repaired_metrics.json",   {})
    corruption_log = _load_json(r_dir / "corruption_log.json",   [])
    demo_answers = _load_json(r_dir / "agent_demo_answers.json", [])

    # ── Clean dataset summary ─────────────────────────────────────────────
    clean_json = DATA_DIR / "clean" / "papers_clean.json"
    papers = _load_json(clean_json, [])
    paper_count = len(papers) if isinstance(papers, list) else 0
    paper_titles = [p.get("title", "") for p in (papers[:5] if isinstance(papers, list) else [])]

    return jsonify({
        "ok": True,
        "quality": {
            "baseline":  baseline_q,
            "corrupted": corrupted_q,
            "repaired":  repaired_q,
        },
        "freshness": {
            "baseline":  freshness,
            "corrupted": freshness_c,
            "repaired":  freshness_r,
        },
        "metrics": {
            "baseline":  baseline_m,
            "corrupted": corrupted_m,
            "repaired":  repaired_m,
        },
        "corruption_log": corruption_log,
        "demo_answers": demo_answers,
        "dataset": {
            "paper_count": paper_count,
            "sample_titles": paper_titles,
        },
        "last_run": _run_state.get("last_run", {}),
    })


@app.route("/api/logs/<phase>")
def api_logs(phase: str):
    """Return buffered log lines for a phase."""
    with _state_lock:
        logs = list(_run_state["logs"].get(phase, []))
    return jsonify({"ok": True, "phase": phase, "logs": logs})


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Data Pipeline & Observability Demo")
    print("  Group ChickenGuy — Day 10 VinUni K3")
    print("=" * 60)
    print(f"  ROOT   : {ROOT}")
    print(f"  Python : {PYTHON}")
    print(f"  URL    : http://localhost:5050")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
