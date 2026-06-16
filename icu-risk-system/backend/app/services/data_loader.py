import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class DataLoader:
    """Loads and caches CSV data from the /data directory."""

    def __init__(self):
        self.data_dir = Path(settings.DATA_DIR)
        self.sample_dir = Path(settings.SAMPLE_DATA_DIR)
        self._cache: Dict[str, pd.DataFrame] = {}
        self.loaded = False

    def _resolve_path(self, filename: str) -> Optional[Path]:
        real = self.data_dir / filename
        if real.exists():
            return real
        sample = self.sample_dir / filename
        if sample.exists():
            logger.info(f"Using sample data for {filename}")
            return sample
        logger.warning(f"File not found: {filename}")
        return None

    def _load_csv(self, filename: str) -> Optional[pd.DataFrame]:
        if filename in self._cache:
            return self._cache[filename]
        path = self._resolve_path(filename)
        if path is None:
            return None
        try:
            df = pd.read_csv(path, low_memory=False)
            df.columns = [c.lower().strip() for c in df.columns]
            self._cache[filename] = df
            logger.info(f"Loaded {filename}: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return None

    def get_patients(self) -> Optional[pd.DataFrame]:
        return self._load_csv("patients.csv")

    def get_admissions(self) -> Optional[pd.DataFrame]:
        return self._load_csv("admissions.csv")

    def get_icustays(self) -> Optional[pd.DataFrame]:
        return self._load_csv("icustays.csv")

    def get_chartevents(self) -> Optional[pd.DataFrame]:
        return self._load_csv("chartevents.csv")

    def get_labevents(self) -> Optional[pd.DataFrame]:
        return self._load_csv("labevents.csv")

    def get_prescriptions(self) -> Optional[pd.DataFrame]:
        df = self._load_csv("prescriptions.csv")
        if df is None:
            df = self._load_csv("medications.csv")
        return df

    def get_procedures(self) -> Optional[pd.DataFrame]:
        return self._load_csv("procedures.csv")

    def get_d_labitems(self) -> Optional[pd.DataFrame]:
        return self._load_csv("d_labitems.csv")

    def get_d_items(self) -> Optional[pd.DataFrame]:
        return self._load_csv("d_items.csv")

    def get_patient_ids(self):
        patients = self.get_patients()
        if patients is None:
            return []
        col = settings.PATIENTS_ID_COL.lower()
        if col in patients.columns:
            return patients[col].unique().tolist()
        return []

# Singleton instance
data_loader = DataLoader()
