"""The notebook's shared-function cells must be identical to src/analysis.py and src/figures.py."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The newest notebook in notebooks/ (for example 01_data_engineering_and_visualization_SIMPLIFIED_REVISED.ipynb).
NOTEBOOK = sorted((ROOT / "notebooks").glob("01_data_engineering_and_visualization*.ipynb"))[-1]


def code_cells():
    nb = json.loads(NOTEBOOK.read_text())
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def test_analysis_module_is_in_the_notebook():
    source = (ROOT / "src" / "analysis.py").read_text().strip("\n")
    assert source in code_cells()


def test_figures_module_is_in_the_notebook():
    lines = [l for l in (ROOT / "src" / "figures.py").read_text().strip("\n").splitlines() if not l.startswith("from src.analysis import")]
    cells = [c for c in code_cells() if "def fig_rq1(" in c]
    assert len(cells) == 1
    cell_lines = [l for l in cells[0].splitlines() if not l.startswith("# In the repository") and not l.startswith("# describe_strength")]
    assert cell_lines == lines
