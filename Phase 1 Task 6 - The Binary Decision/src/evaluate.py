"""Full binary classification evaluation."""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score,
    roc_curve, precision_recall_curve, classification_report,
    ConfusionMatrixDisplay
)


def full_eval(y_true, y_pred, y_prob, name="model", split="val"):
    m = {
        "model": name, "split": split,
        "accuracy":  round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1":        round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_true, y_prob), 4),
        "pr_auc":    round(average_precision_score(y_true, y_prob), 4),
    }
    print(f"\n  [{split.upper()}] {name}")
    for k,v in m.items():
        if k not in ("model","split"): print(f"    {k:12s}: {v}")
    print(classification_report(y_true, y_pred, target_names=["Not Fraud","Fraud"], zero_division=0))
    return m


def plot_confusion_matrix(y_true, y_pred, name, path):
    fig, ax = plt.subplots(figsize=(5,4))
    ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred, display_labels=["Not Fraud","Fraud"],
        ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(f"Confusion Matrix — {name}")
    plt.tight_layout()
    plt.savefig(path, dpi=120, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


def plot_roc_pr(y_true, models_data, out_dir="outputs"):
    fig, axes = plt.subplots(1,2,figsize=(13,5))
    for name, y_prob in models_data:
        fpr,tpr,_ = roc_curve(y_true,y_prob)
        auc = roc_auc_score(y_true,y_prob)
        axes[0].plot(fpr,tpr,lw=2,label=f"{name} (AUC={auc:.3f})")
        prec,rec,_ = precision_recall_curve(y_true,y_prob)
        ap = average_precision_score(y_true,y_prob)
        axes[1].plot(rec,prec,lw=2,label=f"{name} (AP={ap:.3f})")
    axes[0].plot([0,1],[0,1],"k--",lw=1,label="Random")
    axes[0].set_xlabel("FPR"); axes[0].set_ylabel("TPR")
    axes[0].set_title("ROC Curve"); axes[0].legend(); axes[0].grid(alpha=0.3)
    bp = y_true.mean()
    axes[1].axhline(bp,color="k",linestyle="--",lw=1,label=f"Random (AP={bp:.2f})")
    axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-Recall Curve"); axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(out_dir,"roc_pr_curves.png")
    plt.savefig(path, dpi=120, bbox_inches="tight"); plt.close()
    print(f"  Saved: {path}")


def threshold_analysis(y_true, y_prob, out_dir="outputs"):
    os.makedirs(out_dir, exist_ok=True)
    thresholds = np.arange(0.10,0.91,0.05).round(2)
    rows=[]
    for t in thresholds:
        yp=(y_prob>=t).astype(int)
        cm=confusion_matrix(y_true,yp)
        tn,fp,fn,tp=cm.ravel() if cm.shape==(2,2) else (cm[0,0],0,0,cm[1,1] if cm.shape==(1,1) else 0)
        rows.append({"threshold":round(t,2),"TP":int(tp),"TN":int(tn),"FP":int(fp),"FN":int(fn),
                     "precision":round(precision_score(y_true,yp,zero_division=0),4),
                     "recall":round(recall_score(y_true,yp,zero_division=0),4),
                     "f1":round(f1_score(y_true,yp,zero_division=0),4),
                     "accuracy":round(accuracy_score(y_true,yp),4)})
    df=pd.DataFrame(rows)
    path=os.path.join(out_dir,"threshold_analysis.csv")
    df.to_csv(path,index=False)
    print(f"\n  Threshold Analysis:\n{df[['threshold','precision','recall','f1','FN','FP']].to_string(index=False)}")
    fig,ax=plt.subplots(figsize=(10,5))
    ax.plot(df["threshold"],df["precision"],"b-o",ms=4,label="Precision")
    ax.plot(df["threshold"],df["recall"],"r-o",ms=4,label="Recall")
    ax.plot(df["threshold"],df["f1"],"g-o",ms=4,label="F1")
    ax.axvline(0.35,color="orange",linestyle="--",lw=2,label="Selected threshold=0.35")
    ax.set_xlabel("Threshold"); ax.set_ylabel("Score")
    ax.set_title("Precision / Recall / F1 vs Threshold")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir,"threshold_curve.png"),dpi=120,bbox_inches="tight"); plt.close()
    return df
