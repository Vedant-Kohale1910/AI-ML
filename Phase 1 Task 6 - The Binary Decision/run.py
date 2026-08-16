"""Task 6 Binary Decision harness. Usage: python run.py | python run.py --predict"""
import argparse,random,os
import numpy as np; import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score,f1_score
from src.preprocessing import load_and_split,build_preprocessor
from src.evaluate import full_eval,plot_confusion_matrix,plot_roc_pr,threshold_analysis

SEED=42; DATA="data/raw/credit_fraud_dataset.csv"; THRESHOLD=0.35

def run():
    random.seed(SEED); np.random.seed(SEED)
    os.makedirs("models",exist_ok=True); os.makedirs("outputs",exist_ok=True)
    print(f"\n{'='*60}\n  Task 6 — The Binary Decision\n{'='*60}\n")

    print("[1/7] Loading & splitting...")
    X_tr,X_val,X_test,y_tr,y_val,y_test,X_all,y_all=load_and_split(DATA,seed=SEED)
    total=len(y_all); fraud=y_all.sum()
    print(f"\n  IMBALANCE: Not Fraud {total-fraud} ({(total-fraud)/total*100:.1f}%) | Fraud {fraud} ({fraud/total*100:.1f}%)")
    print(f"  Ratio {(total-fraud)/fraud:.1f}:1 → accuracy alone misleading; using F1+PR-AUC")

    print("\n[2/7] Preprocessing (fit on X_train only)...")
    pp=build_preprocessor(X_tr)
    X_tr_p=pp.fit_transform(X_tr); X_val_p=pp.transform(X_val); X_test_p=pp.transform(X_test)

    print("\n[3/7] Baseline (majority class)...")
    dummy=DummyClassifier(strategy="most_frequent",random_state=SEED)
    dummy.fit(X_tr_p,y_tr)
    base_pred=dummy.predict(X_val_p)
    print(f"  Baseline acc={accuracy_score(y_val,base_pred):.4f} F1={f1_score(y_val,base_pred,zero_division=0):.4f} — catches 0 frauds")

    print("\n[4/7] Logistic Regression (class_weight=balanced)...")
    lr=LogisticRegression(random_state=SEED,max_iter=1000,class_weight="balanced")
    lr.fit(X_tr_p,y_tr)
    lr_prob=lr.predict_proba(X_val_p)[:,1]
    lr_pred=(lr_prob>=THRESHOLD).astype(int)
    lr_m=full_eval(y_val,lr_pred,lr_prob,"LogisticRegression","val")
    plot_confusion_matrix(y_val,lr_pred,"Logistic Regression (t=0.35)","outputs/cm_logistic.png")

    print("\n[5/7] Random Forest (class_weight=balanced)...")
    rf=RandomForestClassifier(n_estimators=100,random_state=SEED,class_weight="balanced")
    rf.fit(X_tr_p,y_tr)
    rf_prob=rf.predict_proba(X_val_p)[:,1]
    rf_pred=(rf_prob>=THRESHOLD).astype(int)
    rf_m=full_eval(y_val,rf_pred,rf_prob,"RandomForest","val")
    plot_confusion_matrix(y_val,rf_pred,"Random Forest (t=0.35)","outputs/cm_randomforest.png")

    plot_roc_pr(y_val,[("Logistic Regression",lr_prob),("Random Forest",rf_prob)],out_dir="outputs")

    print("\n[6/7] Threshold analysis on validation...")
    best_prob=rf_prob if rf_m["roc_auc"]>=lr_m["roc_auc"] else lr_prob
    best_name="RandomForest" if rf_m["roc_auc"]>=lr_m["roc_auc"] else "LogisticRegression"
    best_model=rf if best_name=="RandomForest" else lr
    threshold_analysis(y_val,best_prob,out_dir="outputs")
    print(f"\n  COST ANALYSIS: FN=missed fraud [HIGH COST] > FP=false alarm [LOW COST]")
    print(f"  → Lower threshold to 0.35 maximises recall. JUSTIFIED THRESHOLD=0.35")

    print("\n[7/7] Final test evaluation (ONCE)...")
    test_prob=best_model.predict_proba(X_test_p)[:,1]
    test_pred=(test_prob>=THRESHOLD).astype(int)
    test_m=full_eval(y_test,test_pred,test_prob,best_name,"test")
    plot_confusion_matrix(y_test,test_pred,f"{best_name} FINAL TEST","outputs/cm_final_test.png")

    joblib.dump(pp,"models/preprocessor.pkl"); joblib.dump(best_model,"models/best_model.pkl")
    print(f"\n  Models saved. Best: {best_name} | Threshold: {THRESHOLD}")
    print(f"  FINAL TEST — F1:{test_m['f1']} ROC-AUC:{test_m['roc_auc']} Recall:{test_m['recall']} Precision:{test_m['precision']}")
    print(f"{'='*60}\n")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--predict",action="store_true")
    args=parser.parse_args()
    if args.predict:
        import subprocess,sys; subprocess.run([sys.executable,"src/predict.py"])
    else:
        run()
