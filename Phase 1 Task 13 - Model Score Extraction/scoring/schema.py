"""Input/output contracts using Pydantic for strict validation."""
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Any
from datetime import datetime


class CustomerInput(BaseModel):
    tenure: float = Field(..., ge=0, le=120, description="Months as customer (0-120)")
    monthly_charges: float = Field(..., ge=0, le=500, description="Monthly bill in ₹")
    total_charges: float = Field(..., ge=0, description="Total billed so far in ₹")
    num_products: int = Field(..., ge=1, le=10, description="Number of subscribed products")
    support_calls: int = Field(..., ge=0, le=50, description="Support calls in past year")
    contract_type: int = Field(..., ge=0, le=2, description="0=Month-to-Month, 1=One Year, 2=Two Year")
    payment_method: int = Field(..., ge=0, le=3, description="0-3 payment method codes")
    age_group: int = Field(..., ge=0, le=3, description="0=18-25, 1=26-40, 2=41-60, 3=60+")
    region: int = Field(..., ge=0, le=3, description="0=North, 1=South, 2=East, 3=West")
    internet_service: int = Field(..., ge=0, le=2, description="0=None, 1=DSL, 2=Fiber")
    online_backup: int = Field(..., ge=0, le=1, description="1=Yes, 0=No")
    tech_support: int = Field(..., ge=0, le=1, description="1=Yes, 0=No")

    @validator('total_charges')
    def total_ge_monthly(cls, v, values):
        if 'monthly_charges' in values and v < values['monthly_charges'] * 0.5:
            raise ValueError('total_charges seems too low relative to monthly_charges')
        return v

    class Config:
        extra = 'forbid'


class ScoreOutput(BaseModel):
    record_id: Optional[str] = None
    score: float = Field(..., description="Calibrated churn probability (0.0–1.0)")
    score_band: str = Field(..., description="Human-readable risk band")
    prediction: int = Field(..., description="Binary prediction (0=Stay, 1=Churn)")
    prediction_label: str
    threshold_used: float
    score_meaning: str = "Calibrated probability of customer churn in the next billing cycle"
    model_version: str
    model_hash: str
    scored_at: str


class BatchInput(BaseModel):
    records: List[CustomerInput] = Field(..., min_items=1, max_items=10000)
    batch_id: Optional[str] = None


class BatchOutput(BaseModel):
    batch_id: Optional[str] = None
    total_records: int
    scored_records: int
    failed_records: int
    model_version: str
    scores: List[Any]
    errors: List[Any]
    scored_at: str


def score_band(prob: float) -> str:
    if prob < 0.20: return "LOW"
    if prob < 0.40: return "MEDIUM-LOW"
    if prob < 0.60: return "MEDIUM-HIGH"
    return "HIGH"
