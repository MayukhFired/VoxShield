"""Evaluate VoxShield's heuristic baseline against a labeled CSV manifest.

This tool deliberately reports the baseline's observed performance rather than
claiming universal accuracy. It does not download data or send audio anywhere.

Example:
    python scripts/evaluate_baseline.py data/DATASET_MANIFEST.csv --output reports/baseline.json
"""

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.ensemble import EnsembleDetector


def truth_from_label(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"real", "bonafide", "human"}:
        return "real"
    if normalized in {"fake", "synthetic", "spoof"}:
        return "fake"
    raise ValueError("label must be one of real/bonafide/human or fake/synthetic/spoof")


def evaluate(manifest_path: Path) -> dict:
    detector = EnsembleDetector()
    records = []
    confusion = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "errors": 0}

    with manifest_path.open(newline="", encoding="utf-8") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            try:
                path = (PROJECT_ROOT / row["path"]).resolve()
                expected = truth_from_label(row["label"])
                if not path.is_file():
                    raise FileNotFoundError(path)
                result = detector.analyze(str(path))
                predicted = result.get("verdict")
                if predicted not in {"real", "fake"}:
                    raise RuntimeError(result.get("error", "detector returned no verdict"))
                if expected == "fake" and predicted == "fake":
                    confusion["tp"] += 1
                elif expected == "real" and predicted == "real":
                    confusion["tn"] += 1
                elif expected == "real":
                    confusion["fp"] += 1
                else:
                    confusion["fn"] += 1
                records.append({"path": row["path"], "expected": expected, "predicted": predicted, "score": result["ensemble_score"]})
            except Exception as error:
                confusion["errors"] += 1
                records.append({"row": row_number, "path": row.get("path"), "error": str(error)})

    evaluated = sum(confusion[key] for key in ("tp", "tn", "fp", "fn"))
    accuracy = (confusion["tp"] + confusion["tn"]) / evaluated if evaluated else None
    precision = confusion["tp"] / (confusion["tp"] + confusion["fp"]) if confusion["tp"] + confusion["fp"] else None
    recall = confusion["tp"] / (confusion["tp"] + confusion["fn"]) if confusion["tp"] + confusion["fn"] else None
    return {"evaluated": evaluated, "accuracy": accuracy, "fake_precision": precision, "fake_recall": recall, "confusion": confusion, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="CSV with path and label columns")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    result = evaluate(args.manifest)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
