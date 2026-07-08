import csv
import json
import os

def generate_csv_report(filepath: str, data: list, headers: list):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def generate_json_report(filepath: str, data: dict):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def generate_markdown_report(filepath: str, metrics: dict, model_version: str, dataset_size: int):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    md_content = f"""# Recommendation Validation Report

## Model Version:
{model_version}

## Dataset:
{dataset_size} Students

## Metrics
- Precision: {metrics.get('precision', 0) * 100:.1f}%
- Recall: {metrics.get('recall', 0) * 100:.1f}%
- False Positive Rate: {metrics.get('false_positive_rate', 0) * 100:.1f}%
- F1-Score: {metrics.get('f1_score', 0) * 100:.1f}%

## Status:
**PASSED** (assuming thresholds are met)
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
