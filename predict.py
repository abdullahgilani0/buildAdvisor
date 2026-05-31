"""
BuildAdvisor – Prediction Module
Loads saved models and exposes predict_cost(), predict_materials(), and predict_feasibility_score()
for integration into any backend.
"""

import json
from pathlib import Path
from typing import Union

import joblib
import numpy as np
import pandas as pd

_BASE_DIR = Path(__file__).parent

_model = None
_scaler = None
_materials_model = None
_feasibility_model = None
_feature_columns: list[str] = []
_uses_scaling = False


def _load_artifacts():
    global _model, _scaler, _feature_columns, _uses_scaling, _materials_model, _feasibility_model

    model_path = _BASE_DIR / "model.pkl"
    mats_path = _BASE_DIR / "materials_model.pkl"
    feas_path = _BASE_DIR / "feasibility_model.pkl"
    scaler_path = _BASE_DIR / "scaler.pkl"
    cols_path = _BASE_DIR / "feature_columns.json"

    if not model_path.exists():
        raise FileNotFoundError(
            "model.pkl not found. Run train_model.py first."
        )
    if not cols_path.exists():
        raise FileNotFoundError(
            "feature_columns.json not found. Run train_model.py first."
        )

    _model = joblib.load(model_path)
    _feature_columns = json.loads(cols_path.read_text())

    if scaler_path.exists():
        _scaler = joblib.load(scaler_path)
        from sklearn.linear_model import LinearRegression
        _uses_scaling = isinstance(_model, LinearRegression)

    if mats_path.exists():
        _materials_model = joblib.load(mats_path)
    if feas_path.exists():
        _feasibility_model = joblib.load(feas_path)


def _prepare_input(input_data: dict) -> pd.DataFrame:
    global _model
    if _model is None:
        _load_artifacts()

    # Normalise alternate key names
    data = dict(input_data)
    if "rooms" in data and "number_of_rooms" not in data:
        data["number_of_rooms"] = data.pop("rooms")
    if "bathrooms" in data and "number_of_bathrooms" not in data:
        data["number_of_bathrooms"] = data.pop("bathrooms")

    _validate(data)

    row = pd.DataFrame([data])

    # One-hot encode categoricals
    cat_cols = ["construction_type", "quality_level", "structure_type", "soil_type"]
    row = pd.get_dummies(row, columns=cat_cols)

    # Align to training feature set (fills missing dummies with 0)
    row = row.reindex(columns=_feature_columns, fill_value=0)
    return row


def predict_cost(input_data: dict) -> dict:
    """
    Predict total construction cost in PKR.
    """
    global _model
    if _model is None:
        _load_artifacts()

    row = _prepare_input(input_data)

    if _uses_scaling and _scaler is not None:
        X = _scaler.transform(row.values.astype(float))
    else:
        X = row

    predicted = int(_model.predict(X)[0])

    return {
        "predicted_cost_pkr": predicted,
        "formatted": f"PKR {predicted:,.0f}",
    }


def predict_materials(input_data: dict) -> dict:
    """
    Predict structural materials using the trained multi-output RF model.
    """
    global _materials_model
    if _materials_model is None:
        _load_artifacts()
    if _materials_model is None:
        raise FileNotFoundError("materials_model.pkl not found. Run train_model.py first.")

    row = _prepare_input(input_data)
    predicted = _materials_model.predict(row)[0]
    
    # Target order: ["cement_bags", "sand_cft", "aggregate_cft", "bricks", "steel_bars_kg"]
    return {
        "cement_bags": int(round(predicted[0])),
        "sand_cft": int(round(predicted[1])),
        "aggregate_cft": int(round(predicted[2])),
        "bricks": int(round(predicted[3])),
        "steel_bars_kg": int(round(predicted[4])),
    }


def predict_feasibility_score(input_data: dict) -> float:
    """
    Predict base feasibility score using the trained RF model.
    """
    global _feasibility_model
    if _feasibility_model is None:
        _load_artifacts()
    if _feasibility_model is None:
        raise FileNotFoundError("feasibility_model.pkl not found. Run train_model.py first.")

    row = _prepare_input(input_data)
    predicted = _feasibility_model.predict(row)[0]
    return float(predicted)


def _validate(data: dict):
    required = {
        "total_area_sqft", "number_of_floors", "number_of_rooms",
        "number_of_bathrooms", "location_factor",
        "construction_type", "quality_level", "structure_type",
        "soil_type", "avg_temp_summer", "avg_temp_winter",
    }
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    valid_construction = {"residential", "commercial"}
    valid_quality = {"basic", "standard", "premium"}
    valid_structure = {"brick", "concrete", "steel"}
    valid_soil = {"clay", "silt", "sand", "gravel", "rock"}

    if data["construction_type"] not in valid_construction:
        raise ValueError(f"construction_type must be one of {valid_construction}")
    if data["quality_level"] not in valid_quality:
        raise ValueError(f"quality_level must be one of {valid_quality}")
    if data["structure_type"] not in valid_structure:
        raise ValueError(f"structure_type must be one of {valid_structure}")
    if data["soil_type"] not in valid_soil:
        raise ValueError(f"soil_type must be one of {valid_soil}")
    if not (1.0 <= float(data["location_factor"]) <= 1.3):
        raise ValueError("location_factor must be between 1.0 and 1.3")
    if not (20.0 <= float(data["avg_temp_summer"]) <= 55.0):
        raise ValueError("avg_temp_summer must be between 20 and 55")
    if not (-15.0 <= float(data["avg_temp_winter"]) <= 30.0):
        raise ValueError("avg_temp_winter must be between -15 and 30")


# ── Demo / test ───────────────────────────────────────────────────────────────

SAMPLE_INPUTS = [
    {
        "label": "Mid-range residential (standard brick)",
        "input": {
            "total_area_sqft": 1200,
            "number_of_floors": 2,
            "number_of_rooms": 3,
            "number_of_bathrooms": 2,
            "location_factor": 1.1,
            "construction_type": "residential",
            "quality_level": "standard",
            "structure_type": "brick",
            "soil_type": "gravel",
            "avg_temp_summer": 35.0,
            "avg_temp_winter": 10.0,
        },
    }
]


def run_demo():
    print("=" * 55)
    print("  BuildAdvisor – Prediction Demo")
    print("=" * 55)

    for case in SAMPLE_INPUTS:
        print(f"\n  Scenario : {case['label']}")
        for k, v in case["input"].items():
            print(f"    {k:<25} {v}")
        
        try:
            result_cost = predict_cost(case["input"])
            print(f"\n  ► Predicted Cost        : {result_cost['formatted']}")
            
            result_mats = predict_materials(case["input"])
            print(f"  ► Predicted Materials   : {result_mats}")
            
            result_feas = predict_feasibility_score(case["input"])
            print(f"  ► Predicted Feasibility : {result_feas:.2f}/100")
        except Exception as e:
            print(f"\n  Error during prediction: {e}")
        print("  " + "─" * 45)


if __name__ == "__main__":
    run_demo()
