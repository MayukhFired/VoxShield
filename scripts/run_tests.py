"""
VoiceShield -- Interactive Test Runner
=======================================
Runs the EnsembleDetector on labelled audio files from data/real and data/synthetic,
and prints a formatted results table with per-check breakdowns and accuracy summary.

Usage:
    python scripts/run_tests.py                    # all files
    python scripts/run_tests.py --limit 5          # first N from each category
    python scripts/run_tests.py --file path.wav    # single file (no label)
    python scripts/run_tests.py --demo             # only the 3 files in data/demo
"""

import os
import sys
import argparse
import time

# Force UTF-8 output so colour codes work without crashing on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path so we can import ml.*
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ml.ensemble import EnsembleDetector

# ---- ANSI colour helpers (safe on modern Windows terminals) -------------------
def _c(code, text):
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: _c("92", t)
RED    = lambda t: _c("91", t)
YELLOW = lambda t: _c("93", t)
CYAN   = lambda t: _c("96", t)
BOLD   = lambda t: _c("1",  t)
DIM    = lambda t: _c("2",  t)


def verdict_colour(verdict, expected=None):
    if expected is None:
        return YELLOW(verdict.upper()) if verdict == "fake" else GREEN(verdict.upper())
    correct = (verdict == expected)
    return GREEN(verdict.upper()) if correct else RED(verdict.upper())


def bar(score, width=20):
    """ASCII progress bar: ### for filled, --- for empty."""
    filled = round(score * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def safe(text, max_len=45):
    """Truncate and strip any non-ASCII to be safe."""
    text = text[:max_len] + "..." if len(text) > max_len else text
    return text.encode("ascii", errors="replace").decode("ascii")


def print_result(path, result, expected=None, index=1):
    verdict  = result.get("verdict", "error")
    conf     = result.get("confidence", 0.0)
    e_score  = result.get("ensemble_score", 0.0)
    duration = result.get("duration_seconds", 0.0)
    sig_sum  = result.get("signal_summary", {})
    checks   = result.get("signal_checks", [])

    filename = os.path.basename(path)
    correct  = None if expected is None else (verdict == expected)

    if correct is None:
        prefix = YELLOW("[?]")
    elif correct:
        prefix = GREEN("[OK]")
    else:
        prefix = RED("[NO]")

    print(f"\n{BOLD(f'[{index}] {filename}')}")
    print(f"  {prefix}  Verdict: {verdict_colour(verdict, expected)}   "
          f"Confidence: {BOLD(f'{conf*100:.1f}%')}   "
          f"Ensemble: {e_score:.4f}   "
          f"Duration: {duration:.2f}s")

    if expected is not None:
        status = GREEN("CORRECT") if correct else RED(f"WRONG (expected {expected.upper()})")
        print(f"       Expected: {BOLD(expected.upper())} -> {status}")

    if result.get("verdict") == "error":
        print(f"  {RED('ERROR:')} {result.get('error', 'unknown')}")
        return False

    # Signal checks table
    print(f"  {DIM('-' * 78)}")
    print(f"  {'Check':<22} {'Pass':<6} {'Score':<7} {'Bar':<24} Detail")
    print(f"  {DIM('-' * 78)}")
    for c in checks:
        name   = c["check_name"]
        passed_str = GREEN("yes") if c["passed"] else RED("no ")
        score  = c["score"]
        detail = safe(c["detail"])
        print(f"  {name:<22} {passed_str}    {score:<7.4f} {bar(score):<24} {DIM(detail)}")

    print(f"  {DIM('-' * 78)}")
    p  = sig_sum.get("checks_passed", 0)
    f_ = sig_sum.get("checks_failed", 0)
    cs = sig_sum.get("combined_score", 0.0)
    print(f"  Signal: {GREEN(str(p))} passed  /  {RED(str(f_))} failed   Combined score: {cs:.4f}")

    return correct if correct is not None else True


def run_batch(detector, files_with_labels, limit=None):
    if limit:
        files_with_labels = files_with_labels[:limit]

    total = len(files_with_labels)
    correct_count = 0
    labelled_count = 0
    errors = 0

    print(BOLD(CYAN(f"\n{'='*70}")))
    print(BOLD(CYAN(f"  VoiceShield Test Runner   ({total} files)")))
    print(BOLD(CYAN(f"{'='*70}")))

    for i, (path, expected) in enumerate(files_with_labels, 1):
        t0 = time.time()
        result = detector.analyze(path)
        elapsed = time.time() - t0

        outcome = print_result(path, result, expected, index=i)
        print(f"  {DIM(f'(analysed in {elapsed:.2f}s)')}")

        if result.get("verdict") == "error":
            errors += 1
        elif expected is not None:
            labelled_count += 1
            if outcome:
                correct_count += 1

    # Summary
    print(BOLD(CYAN(f"\n{'='*70}")))
    print(BOLD("  SUMMARY"))
    print(f"  Files processed : {total}")
    print(f"  Errors          : {RED(str(errors)) if errors else GREEN('0')}")
    if labelled_count:
        acc = correct_count / labelled_count * 100
        col = GREEN if acc >= 70 else (YELLOW if acc >= 50 else RED)
        print(f"  Accuracy        : {col(f'{correct_count}/{labelled_count} ({acc:.1f}%)')}")
    print(BOLD(CYAN(f"{'='*70}\n")))


def collect_files(data_dir):
    """Collect labelled (path, expected_label) pairs from data/real and data/synthetic."""
    pairs = []
    real_dir = os.path.join(data_dir, "real")
    fake_dir = os.path.join(data_dir, "synthetic")

    for d, label in [(real_dir, "real"), (fake_dir, "fake")]:
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if fname.lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a")):
                pairs.append((os.path.join(d, fname), label))
    return pairs


def main():
    parser = argparse.ArgumentParser(description="VoiceShield test runner")
    parser.add_argument("--file",  type=str, help="Path to a single audio file (no label expected)")
    parser.add_argument("--demo",  action="store_true", help="Run only the 3 demo files")
    parser.add_argument("--limit", type=int, default=None, help="Max files per category")
    args = parser.parse_args()

    detector = EnsembleDetector()

    if args.file:
        print(BOLD(f"\nAnalysing: {args.file}"))
        result = detector.analyze(args.file)
        print_result(args.file, result, expected=None, index=1)
        return

    data_dir = os.path.join(ROOT, "data")

    if args.demo:
        demo_dir = os.path.join(data_dir, "demo")
        files = [(os.path.join(demo_dir, f), None)
                 for f in sorted(os.listdir(demo_dir))
                 if f.lower().endswith((".wav", ".mp3", ".flac"))]
        run_batch(detector, files)
        return

    files = collect_files(data_dir)

    if not files:
        print(RED("\nNo audio files found in data/real or data/synthetic."))
        sys.exit(1)

    # If limit given, take N from each category
    if args.limit:
        real_files = [(p, l) for p, l in files if l == "real"][:args.limit]
        fake_files = [(p, l) for p, l in files if l == "fake"][:args.limit]
        files = real_files + fake_files

    run_batch(detector, files)


if __name__ == "__main__":
    main()