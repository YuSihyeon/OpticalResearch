from pathlib import Path

import numpy as np

from gaussian_pilot.visualize import save_rgb_nir_panel, write_json, write_markdown_report


def test_visualization_and_reports_write_files(tmp_path: Path):
    image = np.zeros((12, 12, 3), dtype=np.float32)
    nir = np.zeros((12, 12), dtype=np.float32)
    heat = np.ones((12, 12), dtype=np.float32)
    panel = tmp_path / "panel.png"
    save_rgb_nir_panel(
        panel,
        {
            "rgb_target": image,
            "rgb_recon": image,
            "nir_target": nir,
            "nir_recon": nir,
            "rgb_error": nir,
            "shared_error": nir,
            "difference": heat,
        },
    )
    assert panel.exists()
    write_json(tmp_path / "metrics.json", {"mae": 0.1})
    assert (tmp_path / "metrics.json").exists()
    write_markdown_report(tmp_path / "report.md", "Title", {"Summary": "Body"})
    assert "Summary" in (tmp_path / "report.md").read_text(encoding="utf-8")
