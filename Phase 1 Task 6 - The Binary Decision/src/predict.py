"""Live prediction with input validation and edge case handling."""
import joblib, numpy as np, pandas as pd

FEATURE_COLS=["age","income","credit_limit","transaction_amount","num_transactions_30d",
              "account_age_months","num_prev_disputes","merchant_category","country_match",
              "time_of_day_hour","is_weekend","card_present","distance_from_home_km"]
VALID_CATS={"retail","travel","food","electronics","online"}
BOUNDS={"age":(0,120),"income":(0,1e6),"credit_limit":(0,2e6),"transaction_amount":(0,1e5),
        "num_transactions_30d":(0,500),"account_age_months":(0,600),"num_prev_disputes":(0,100),
        "country_match":(0,1),"time_of_day_hour":(0,23),"is_weekend":(0,1),
        "card_present":(0,1),"distance_from_home_km":(0,50000)}

def validate_input(record):
    cleaned={}
    for col in FEATURE_COLS:
        if col not in record: cleaned[col]=np.nan; continue
        val=record[col]
        if col=="merchant_category":
            if val not in VALID_CATS and val is not None:
                print(f"  [Warning] Unknown category '{val}' — zero-encoded by OHE.")
            cleaned[col]=val; continue
        if val is None or (isinstance(val,float) and np.isnan(val)): cleaned[col]=np.nan; continue
        try: val=float(val)
        except: raise ValueError(f"'{col}' must be numeric, got '{record[col]}'")
        lo,hi=BOUNDS[col]
        if not(lo<=val<=hi): raise ValueError(f"'{col}'={val} out of range [{lo},{hi}]")
        cleaned[col]=val
    return cleaned

def predict_single(record,model_path="models/best_model.pkl",pp_path="models/preprocessor.pkl",threshold=0.35):
    try: cleaned=validate_input(record)
    except ValueError as e: return {"error":str(e),"prediction":None,"probability_fraud":None}
    pp=joblib.load(pp_path)
    row=pd.DataFrame([cleaned],columns=FEATURE_COLS)
    X=pp.transform(row)
    model=joblib.load(model_path)
    prob=float(model.predict_proba(X)[0][1])
    pred=int(prob>=threshold)
    return {"probability_fraud":round(prob,4),"threshold_used":threshold,
            "prediction":"FRAUD ⚠️" if pred else "NOT FRAUD ✅","prediction_int":pred,
            "reasoning":f"P(fraud)={prob:.4f} {'≥' if pred else '<'} {threshold} → {'FLAG' if pred else 'Allow'}"}

if __name__=="__main__":
    print("\n"+"="*55+"\n  Task 6 — Live Prediction Demo\n"+"="*55)
    cases=[
        ("High-risk transaction",{"age":34,"income":45000,"credit_limit":8000,"transaction_amount":4200,
          "num_transactions_30d":3,"account_age_months":6,"num_prev_disputes":3,
          "merchant_category":"electronics","country_match":0,"time_of_day_hour":2,
          "is_weekend":1,"card_present":0,"distance_from_home_km":350}),
        ("Normal transaction",{"age":45,"income":95000,"credit_limit":30000,"transaction_amount":120,
          "num_transactions_30d":25,"account_age_months":96,"num_prev_disputes":0,
          "merchant_category":"food","country_match":1,"time_of_day_hour":14,
          "is_weekend":0,"card_present":1,"distance_from_home_km":5}),
        ("Missing age (handled)",{"age":None,"income":60000,"credit_limit":15000,"transaction_amount":800,
          "num_transactions_30d":12,"account_age_months":48,"num_prev_disputes":1,
          "merchant_category":"retail","country_match":1,"time_of_day_hour":10,
          "is_weekend":0,"card_present":1,"distance_from_home_km":20}),
        ("Unseen category",{"age":29,"income":55000,"credit_limit":12000,"transaction_amount":200,
          "num_transactions_30d":8,"account_age_months":24,"num_prev_disputes":0,
          "merchant_category":"supermarket","country_match":1,"time_of_day_hour":11,
          "is_weekend":1,"card_present":1,"distance_from_home_km":8}),
        ("❌ Invalid age",{"age":"hello","income":50000,"credit_limit":10000,"transaction_amount":300,
          "num_transactions_30d":10,"account_age_months":36,"num_prev_disputes":0,
          "merchant_category":"online","country_match":1,"time_of_day_hour":9,
          "is_weekend":0,"card_present":1,"distance_from_home_km":15}),
        ("❌ Out-of-range amount",{"age":40,"income":70000,"credit_limit":20000,"transaction_amount":999999,
          "num_transactions_30d":5,"account_age_months":60,"num_prev_disputes":0,
          "merchant_category":"travel","country_match":1,"time_of_day_hour":15,
          "is_weekend":0,"card_present":1,"distance_from_home_km":30}),
    ]
    for label,data in cases:
        print(f"\n  Case: {label}")
        r=predict_single(data)
        if r.get("error"): print(f"  ❌ Error: {r['error']}")
        else:
            print(f"  P(fraud)={r['probability_fraud']}  Threshold={r['threshold_used']}")
            print(f"  Prediction: {r['prediction']}")
            print(f"  {r['reasoning']}")
