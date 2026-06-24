"""
run_pipeline.py
---------------
Master runner — executes the full pipeline in order:

  1. Generate synthetic data
  2. Build features
  3. Evaluate heuristic baseline
  4. Train & evaluate Random Forest ranker
  5. Compare ranker vs baseline
  6. Run the demo walkthrough

Think of this as the 'press one button and show the founder' script.

Usage: python run_pipeline.py
       python run_pipeline.py --demo   (includes end-to-end demo at the end)
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def step(label: str):
    print(f"\n{'─' * 60}")
    print(f"  STEP: {label}")
    print(f"{'─' * 60}")


def main(run_demo: bool = False):
    t0 = time.time()
    print("PlaceMux · Task 06 · Quality Baseline Pipeline")
    print("=" * 60)

    # 1 ── generate data
    step("Generate synthetic student + job data")
    from src.utils.data_generator import main as gen_data
    gen_data()

    # 2 ── feature engineering
    step("Feature engineering")
    from src.features.feature_engineering import main as build_features
    build_features()

    # 3 ── baseline
    step("Heuristic baseline evaluation")
    from src.models.baseline import main as run_baseline
    baseline_metrics = run_baseline()

    # 4 ── ranker
    step("Train Random Forest ranker")
    from src.models.ranker import main as run_ranker
    _, ranker_metrics = run_ranker(run_demo_flag=run_demo)

    # 5 ── summary
    total_time = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete in {total_time:.1f}s")
    print(f"{'=' * 60}")
    print("\n  Key metrics (test set):")
    print(f"  {'Metric':<28} {'Baseline':>10} {'RF Ranker':>10}")
    print(f"  {'-' * 52}")
    for key in ["precision", "recall", "f1", "roc_auc", "false_positive_rate", "ndcg@10"]:
        bv = baseline_metrics.get(key, 0.0)
        rv = ranker_metrics.get(key, 0.0)
        print(f"  {key:<28} {bv:>10.4f} {rv:>10.4f}")
    print(f"\n  Reports saved to: reports/")
    print(f"  Model saved to:   experiments/models/ranker_rf.joblib")
    print(f"\n  To start the inference API:")
    print(f"    uvicorn src.api.app:app --reload --port 8000")
    print(f"\n  To run tests:")
    print(f"    pytest tests/ -v")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Include end-to-end demo walkthrough")
    args = parser.parse_args()
    main(run_demo=args.demo)
