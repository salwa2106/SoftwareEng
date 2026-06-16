import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

def safe_float(val) -> Optional[float]:
    """Convert value to float safely."""
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return None
        return round(v, 2)
    except (TypeError, ValueError):
        return None

def calculate_age(dob: str, reference_date: str) -> Optional[int]:
    """Calculate age from date of birth."""
    try:
        dob_dt = pd.to_datetime(dob)
        ref_dt = pd.to_datetime(reference_date)
        age = (ref_dt - dob_dt).days // 365
        if age > 150:
            return 91
        return max(0, age)
    except Exception:
        return None

def normalize_gender(gender: str) -> str:
    if isinstance(gender, str):
        return gender.strip().upper()
    return "Unknown"

def hours_between(start: str, end: str) -> Optional[float]:
    """Calculate hours between two datetime strings."""
    try:
        s = pd.to_datetime(start)
        e = pd.to_datetime(end)
        return round((e - s).total_seconds() / 3600, 1)
    except Exception:
        return None
