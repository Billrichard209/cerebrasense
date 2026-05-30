"""Tests for Colab workflow assets."""

from __future__ import annotations

import json
from pathlib import Path


def test_colab_notebook_exists_and_has_expected_cells() -> None:
    """The Colab notebook should exist and include the key training steps."""

    notebook_path = Path(__file__).resolve().parents[1] / "notebooks" / "oasis_colab_training.ipynb"
    assert notebook_path.exists()

    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    cell_sources = "\n".join("".join(cell.get("source", [])) for cell in payload["cells"])
    assert "drive.mount('/content/drive')" in cell_sources
    assert "train_oasis_colab.py" in cell_sources
    assert "calibrate_oasis_threshold.py" in cell_sources
    assert "promote_oasis_checkpoint.py" in cell_sources


def test_oasis2_v3_temporal_colab_notebook_is_run_ready() -> None:
    """The V3 reliability Colab notebook should point at the current candidate workflow."""

    notebook_path = Path(__file__).resolve().parents[2] / "oasis2_v3_temporal_reliability_colab.ipynb"
    assert notebook_path.exists()

    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    cell_sources = "\n".join("".join(cell.get("source", [])) for cell in payload["cells"])

    assert "https://github.com/Billrichard209/Cerebrasense-.git" in cell_sources
    assert "77eea77519a3743631917424e0a232cc1fa5b74f" in cell_sources
    assert "oasis2_multimodal_v3_temporal" in cell_sources
    assert "configs/oasis2_train_multimodal_v3_temporal.yaml" in cell_sources
    assert "train_oasis2_colab.py" in cell_sources
    assert "LOG_ROOT = RUNTIME_ROOT / 'logs' / RUN_NAME" in cell_sources
    assert "subprocess.Popen" in cell_sources
    assert "stderr=subprocess.STDOUT" in cell_sources
    assert "train-script-import-smoke" in cell_sources
    assert "PYTHON, '-u', 'scripts/train_oasis2_colab.py'" in cell_sources
    assert "evaluate_oasis2_candidate.py" in cell_sources
    assert "audit_temporal_paradoxes.py" in cell_sources
    assert "build_oasis2_leaderboard.py" in cell_sources
    assert "build_cerebrasense_control_tower.py" in cell_sources
    assert "make_archive" in cell_sources
    assert "export_onnx.py" not in cell_sources
    assert "Billrichard209/cerebrasense.git" not in cell_sources
