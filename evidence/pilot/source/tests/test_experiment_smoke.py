import subprocess
import sys
from pathlib import Path


def test_rti_experiment_smoke_runs(tmp_path: Path):
    out = tmp_path / "rti"
    result = subprocess.run(
        [
            sys.executable,
            "experiment_rti_gaussian.py",
            "--smoke",
            "--iterations",
            "3",
            "--output",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (out / "rti_panel.png").exists()
    assert (out / "metrics.json").exists()
    assert (out / "report.md").exists()


def test_rgb_nir_experiment_smoke_runs(tmp_path: Path):
    out = tmp_path / "rgb_nir"
    result = subprocess.run(
        [
            sys.executable,
            "experiment_rgb_nir_gaussian.py",
            "--smoke",
            "--iterations",
            "3",
            "--output",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (out / "rgb_nir_panel.png").exists()
    assert (out / "metrics.json").exists()
    assert (out / "report.md").exists()
