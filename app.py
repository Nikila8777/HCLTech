from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Customer Payment Assistant Backend")

# Allow Streamlit frontend
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Backend is running successfully!"}

@app.get("/classify/{customer_id}")
def classify(customer_id: str):
    return {
        "customer_id": customer_id,
        "pred_label": "occasional_defaulter",
        "score": 0.78
    }

@app.get("/generate/{customer_id}")
def generate(customer_id: str):
    return {
        "customer_id": customer_id,
        "category": "occasional_defaulter",
        "email": {
            "subject": f"Payment Reminder for {customer_id}",
            "body": (
                f"Dear Customer,\n\n"
                f"This is a reminder regarding pending dues for account {customer_id}.\n"
                f"Please clear the outstanding balance within 7 days.\n\n"
                f"Thank You."
            )
        }
    }
