"""
Task 14 — Live Demo: predict.py
Loads prepared params, scores new customers, assigns to prep clusters.
"""
import sys, os, json, warnings
sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings('ignore')
import pandas as pd, numpy as np, joblib
from sklearn.cluster import KMeans

MODELS_DIR = 'models'
RESULTS_DIR = 'results'

scaler = joblib.load(f'{MODELS_DIR}/scaler.joblib')
pca = joblib.load(f'{MODELS_DIR}/pca.joblib')
with open(f'{RESULTS_DIR}/cluster_parameters.json') as f:
    params = json.load(f)

selected = params['selected_features']
k = params['justified_k']

# Refit KMeans on prepared data for assignment
X_pca = pd.read_csv(f'{RESULTS_DIR}/prepared_dataset_pca.csv')
km = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=42)
km.fit(X_pca)

def prepare_and_assign(data: dict):
    try:
        missing = [f for f in selected if f not in data]
        if missing:
            return {'error': f'Missing features: {missing}'}
        row = pd.DataFrame([[float(data[f]) for f in selected]], columns=selected)
        scaled = scaler.transform(row)
        pca_rep = pca.transform(scaled)
        cluster = int(km.predict(pca_rep)[0])
        return {
            'cluster': cluster,
            'pca_coords': [round(float(x), 4) for x in pca_rep[0]],
            'k_used': k,
            'silhouette_at_k': params['silhouette_at_justified_k'],
            'justification': f'k={k} selected via silhouette+elbow analysis'
        }
    except Exception as e:
        return {'error': str(e)}

CUSTOMERS = [
    ('Young Low-Income High-Spender', {'age':23,'annual_income':26000,'spending_score':82,'num_purchases':4,'account_balance':420}),
    ('Mid-Age High-Income Low-Spender', {'age':41,'annual_income':78000,'spending_score':28,'num_purchases':13,'account_balance':16000}),
    ('Senior Mid-Income Mid-Spender', {'age':56,'annual_income':54000,'spending_score':58,'num_purchases':9,'account_balance':8500}),
    ('Mid-Age Mid-Income High-Spender', {'age':34,'annual_income':44000,'spending_score':83,'num_purchases':21,'account_balance':3200}),
]

EDGE_CASES = [
    ('Missing feature', {'age':30,'annual_income':50000,'spending_score':60}),
    ('Invalid type', {'age':'young','annual_income':50000,'spending_score':60,'num_purchases':5,'account_balance':2000}),
    ('Out-of-range spending_score=-5', {'age':30,'annual_income':50000,'spending_score':-5,'num_purchases':5,'account_balance':2000}),
]

print("\n" + "="*65)
print(f"  TASK 14 — LIVE DEMO: Cluster Parameter Prep")
print(f"  Prepared k={k} | Features={selected}")
print(f"  Silhouette={params['silhouette_at_justified_k']} | Distance ratio={params['inter_intra_distance_ratio']}")
print("="*65)

print("\n── Customer Cluster Assignment (using prepared params) ──")
for name, data in CUSTOMERS:
    res = prepare_and_assign(data)
    if 'error' in res:
        print(f"\n  {name}: ERROR — {res['error']}")
    else:
        print(f"\n  {name}")
        print(f"  Input    : age={data['age']}, income=₹{data['annual_income']}, spending={data['spending_score']}")
        print(f"  → Cluster: {res['cluster']} of {res['k_used']}")
        print(f"  → PCA coords: {res['pca_coords']}")

print("\n── Edge Case Handling ──")
for name, data in EDGE_CASES:
    try:
        res = prepare_and_assign(data)
        if 'error' in res:
            print(f"  {name}: ✓ Caught → {res['error'][:80]}")
        else:
            print(f"  {name}: Cluster {res['cluster']}")
    except Exception as e:
        print(f"  {name}: ✓ Error → {str(e)[:80]}")

print("\n── Prepared Dataset Summary ──")
print(f"  Scaled CSV   : results/prepared_dataset_scaled.csv")
print(f"  PCA CSV      : results/prepared_dataset_pca.csv")
print(f"  Parameters   : results/cluster_parameters.json")
print(f"  Selected k   : {k} (justified by silhouette={params['silhouette_at_justified_k']})")
print(f"  Justification: {params['justification'][:120]}...")

print("\n" + "="*65)
print("  Demo complete. Dataset locked and parameters ready for clustering.")
print("="*65 + "\n")
