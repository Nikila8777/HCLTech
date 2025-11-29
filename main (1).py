# main.py - Backend using final labeled CSV + XGBoost + email generator
# =====================================================================

import os
import uuid
import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from joblib import load
from email import generate_email    # <-- from your email.py


# ============================================================
# 1. LOAD FINAL LABELED CSV
# ============================================================

FINAL_CSV = "final.csv"  # <-- this is your segmented + cleaned dataset

try:
    customer_db = pd.read_csv(FINAL_CSV)
    customer_db.columns = customer_db.columns.str.strip()
    customer_db["Customer ID"] = customer_db["Customer ID"].astype(str)
    print(f"Loaded FINAL CSV with {len(customer_db)} records.")
except Exception as e:
    print("Error loading CSV:", e)
    customer_db = pd.DataFrame()


# ============================================================
# 2. LOAD MODELS
# ============================================================

print("Loading XGBoost model...")
segment_model = load("telco_xgb_model.pkl")

print("Loading label encoder...")
label_encoder = load("label_encoder.pkl")

# reverse mapping (0 → critical, 1 → habitual, etc.)
inv_label_map = {
    i: c for c, i in zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_))
}


# ============================================================
# 3. FASTAPI SETUP
# ============================================================

app = FastAPI(title="HCL Backend — Segmentation + Email AI")


class SegmentRequest(BaseModel):
    customer_id: str


class EmailRequest(BaseModel):
    customer_id: str
    amount_due: float
    due_date: str   # "2025-02-01"


# ============================================================
# Helper: Fetch a customer row from FINAL CSV
# ============================================================

def get_customer(customer_id: str):
    row = customer_db[customer_db["Customer ID"] == customer_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found.")

    return row.iloc[0].to_dict()


# ============================================================
# 4. HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "running",
        "source_csv": FINAL_CSV,
        "timestamp": datetime.datetime.now()
    }


# ============================================================
# 5. Predict Customer Segment
# ============================================================

@app.post("/predict/segment")
def predict_segment(req: SegmentRequest):
    cust = get_customer(req.customer_id)

    X = customer_db[customer_db["Customer ID"] == req.customer_id].drop(
        columns=["Customer ID", "segment", "segment_encoded"],
        errors="ignore"
    )

    pred_code = int(segment_model.predict(X)[0])
    pred_label = inv_label_map[pred_code]

    return {
        "customer_id": req.customer_id,
        "predicted_segment": pred_label,
        "segment_code": pred_code
    }


# ============================================================
# 6. Generate Email (using TinyLlama)
# ============================================================

@app.post("/generate/email")
def generate_email_api(req: EmailRequest):

    cust = get_customer(req.customer_id)

    # → Predict segment
    X = customer_db[customer_db["Customer ID"] == req.customer_id].drop(
        columns=["Customer ID", "segment", "segment_encoded"],
        errors="ignore"
    )
    pred_code = int(segment_model.predict(X)[0])
    segment_label = inv_label_map[pred_code]

    # → Extract personalization fields from FINAL CSV
    gender = cust.get("gender") or cust.get("Gender")
    tenure = cust.get("tenure") or cust.get("Tenure")
    internet_service = cust.get("Internet Service")
    payment_method = cust.get("Payment Method")
    monthly_charges = cust.get("Monthly Charges")

    # → Generate Email
    email_txt = generate_email(
        class_id=pred_code,
        name=req.customer_id,
        amount_due=req.amount_due,
        due_date=req.due_date,
        gender=gender,
        tenure=tenure,
        internet_service=internet_service,
        payment_method=payment_method,
        monthly_charges=monthly_charges
    )

    return {
        "customer_id": req.customer_id,
        "segment": segment_label,
        "email": email_txt,
        "generated_at": datetime.datetime.now().isoformat()
    }


# ============================================================
# 7. Run the server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
