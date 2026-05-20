"""Tests for the local OASIS-2 training CLI configuration layer."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from src.training.oasis_research import CheckpointConfig, LossConfig, ResearchOASISTrainingConfig


def _load_train_oasis2_module():
    """Load the OASIS-2 training script as an importable module."""

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "train_oasis2.py"
    spec = importlib.util.spec_from_file_location("train_oasis2", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_oasis2_cli_preserves_temporal_lambda_and_pretrain_checkpoint() -> None:
    """CLI override merging should not silently erase model-improvement settings."""

    module = _load_train_oasis2_module()
    cfg = ResearchOASISTrainingConfig(
        loss=LossConfig(name="focal_loss", class_weights=(1.0, 1.0), focal_gamma=1.5, temporal_lambda=0.5),
        checkpoint=CheckpointConfig(init_from_checkpoint=Path("oasis1_best.pt")),
    )
    args = module.build_parser().parse_args([])

    resolved = module.apply_cli_overrides(cfg, args)

    assert resolved.loss.temporal_lambda == 0.5
    assert resolved.loss.class_weights == (1.0, 1.0)
    assert resolved.loss.focal_gamma == 1.5
    assert resolved.checkpoint.init_from_checkpoint == Path("oasis1_best.pt")


def test_oasis2_cli_accepts_explicit_temporal_and_pretrain_overrides() -> None:
    """The local runner should expose controlled stability/pretraining experiments."""

    module = _load_train_oasis2_module()
    cfg = ResearchOASISTrainingConfig()
    args = module.build_parser().parse_args(
        [
            "--temporal-lambda",
            "0.1",
            "--init-from-checkpoint",
            "candidate.pt",
        ]
    )

    resolved = module.apply_cli_overrides(cfg, args)

    assert resolved.loss.temporal_lambda == 0.1
    assert resolved.checkpoint.init_from_checkpoint == Path("candidate.pt")
