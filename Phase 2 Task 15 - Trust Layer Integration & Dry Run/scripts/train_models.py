"""
Train and save models:
1. Job Matching Model - skill overlap + weighted similarity
2. Proctoring Model - Random Forest classifier
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import json

DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

def train_proctoring_model():
    """Train Random Forest for proctoring classification"""
    print("\n" + "="*60)
    print("TRAINING PROCTORING MODEL")
    print("="*60)
    
    # Load proctoring data
    proctoring_df = pd.read_csv(DATA_DIR / "eval" / "proctoring_sessions.csv")
    
    # Split by designated splits
    train_data = proctoring_df[proctoring_df['split'] == 'train'].copy()
    val_data = proctoring_df[proctoring_df['split'] == 'val'].copy()
    test_data = proctoring_df[proctoring_df['split'] == 'test'].copy()
    
    print(f"Train: {len(train_data)} | Val: {len(val_data)} | Test: {len(test_data)}")
    
    # Features
    feature_cols = [
        'assessment_duration_min', 'tab_switches', 'face_detections',
        'external_audio_detected', 'copy_paste_events',
        'keystroke_velocity_variance', 'mouse_speed_anomaly'
    ]
    
    X_train = train_data[feature_cols].values
    y_train = train_data['predicted_label'].values
    
    X_val = val_data[feature_cols].values
    y_val = val_data['predicted_label'].values
    
    X_test = test_data[feature_cols].values
    y_test = test_data['predicted_label'].values
    
    # Train Random Forest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    test_acc = model.score(X_test, y_test)
    
    print(f"\nProctoring Model Performance:")
    print(f"  Train Accuracy: {train_acc:.4f}")
    print(f"  Val Accuracy:   {val_acc:.4f}")
    print(f"  Test Accuracy:  {test_acc:.4f}")
    
    # Feature importance
    importances = model.feature_importances_
    for feat, imp in sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {imp:.4f}")
    
    # Save model
    joblib.dump(model, MODELS_DIR / "proctoring_model.pkl")
    print(f"\n✓ Saved proctoring model to {MODELS_DIR / 'proctoring_model.pkl'}")
    
    return model, feature_cols

def train_matching_model():
    """Matching model - lightweight skill overlap scorer"""
    print("\n" + "="*60)
    print("TRAINING MATCHING MODEL")
    print("="*60)
    
    # Load ontology for skill normalization
    ontology_df = pd.read_csv(DATA_DIR / "ontology.csv")
    
    # Create a simple model object that encodes the ontology
    matching_model = {
        'type': 'skill_overlap_scorer',
        'ontology': ontology_df.to_dict('records'),
        'version': '1.0'
    }
    
    joblib.dump(matching_model, MODELS_DIR / "matching_model.pkl")
    print(f"✓ Saved matching model to {MODELS_DIR / 'matching_model.pkl'}")
    print(f"  Model type: Skill overlap + weighted similarity scorer")
    print(f"  Ontology entries: {len(ontology_df)}")
    
    return matching_model

def main():
    print("\n" + "="*60)
    print("TASK 15 - MODEL TRAINING")
    print("="*60)
    
    # Train both models
    proctoring_model, feature_cols = train_proctoring_model()
    matching_model = train_matching_model()
    
    print("\n" + "="*60)
    print("✓ MODEL TRAINING COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
