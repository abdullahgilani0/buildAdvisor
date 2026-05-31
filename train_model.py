"""
BuildAdvisor – Model Training Pipeline
Trains cost estimation models (Linear Regression, Random Forest, Gradient Boosting),
trains material estimator (Multi-Output Random Forest), and feasibility scoring (Random Forest),
compares cost performance, and saves all models to disk.
"""

import json
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputRegressor

from data_generator import generate_dataset

warnings.filterwarnings("ignore")

CATEGORICAL_COLS = ["construction_type", "quality_level", "structure_type", "soil_type"]
RANDOM_STATE = 42


# ── Data preparation ──────────────────────────────────────────────────────────

def load_and_prepare(n_samples: int = 3000):
    df = generate_dataset(n_samples=n_samples, random_state=RANDOM_STATE)
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    # Define targets
    target_cols = ["total_cost", "cement_bags", "sand_cft", "aggregate_cft", "bricks", "steel_bars_kg", "feasibility_score"]
    
    # Input features
    X = pd.get_dummies(df.drop(columns=target_cols), columns=CATEGORICAL_COLS)
    
    y_cost = df["total_cost"]
    y_mats = df[["cement_bags", "sand_cft", "aggregate_cft", "bricks", "steel_bars_kg"]]
    y_feas = df["feasibility_score"]

    feature_columns = list(X.columns)
    with open("feature_columns.json", "w") as f:
        json.dump(feature_columns, f, indent=2)
    print(f"Saved {len(feature_columns)} feature columns to feature_columns.json")

    # Train/test split for all targets
    (
        X_train, X_test,
        y_cost_train, y_cost_test,
        y_mats_train, y_mats_test,
        y_feas_train, y_feas_test
    ) = train_test_split(
        X, y_cost, y_mats, y_feas, test_size=0.20, random_state=RANDOM_STATE
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    joblib.dump(scaler, "scaler.pkl")
    print("Saved scaler to scaler.pkl")

    return {
        "X_train": X_train,
        "X_test": X_test,
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "y_cost_train": y_cost_train,
        "y_cost_test": y_cost_test,
        "y_mats_train": y_mats_train,
        "y_mats_test": y_mats_test,
        "y_feas_train": y_feas_train,
        "y_feas_test": y_feas_test,
        "feature_cols": feature_columns
    }


# ── Model training & evaluation ───────────────────────────────────────────────

def evaluate(name: str, model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"\n{'─'*45}")
    print(f"  {name}")
    print(f"{'─'*45}")
    print(f"  MAE : PKR {mae:>14,.0f}")
    print(f"  MSE : PKR {mse:>14,.0f}")
    print(f"  RMSE: PKR {np.sqrt(mse):>14,.0f}")
    print(f"  R²  :     {r2:>14.4f}")
    return {"name": name, "model": model, "mae": mae, "mse": mse, "r2": r2}


def train_cost_models(X_train, X_test, X_train_scaled, X_test_scaled, y_train, y_test):
    results = []

    # 1. Linear Regression (uses scaled features)
    lr = LinearRegression()
    lr.fit(X_train_scaled, y_train)
    results.append(evaluate("Linear Regression (baseline)", lr, X_test_scaled, y_test))

    # 2. Random Forest
    rf = RandomForestRegressor(n_estimators=200, max_depth=None, random_state=RANDOM_STATE, n_jobs=-1)
    rf.fit(X_train, y_train)
    results.append(evaluate("Random Forest Regressor", rf, X_test, y_test))

    # 3. Gradient Boosting
    gb = GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=5, random_state=RANDOM_STATE)
    gb.fit(X_train, y_train)
    results.append(evaluate("Gradient Boosting Regressor", gb, X_test, y_test))

    return results


# ── Feature importance ────────────────────────────────────────────────────────

def plot_feature_importance(model, feature_columns: list, top_n: int = 10):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    print(f"\n{'═'*45}")
    print("  Top 5 Most Influential Features (Cost Model)")
    print(f"{'═'*45}")
    for rank, i in enumerate(indices[:5], 1):
        print(f"  {rank}. {feature_columns[i]:<35} {importances[i]:.4f}")

    # Bar chart
    top_idx = indices[:top_n]
    top_names = [feature_columns[i] for i in top_idx]
    top_vals = importances[top_idx]

    plt.figure(figsize=(10, 6))
    colors = sns.color_palette("Blues_r", top_n)
    plt.barh(range(top_n), top_vals[::-1], color=colors[::-1])
    plt.yticks(range(top_n), top_names[::-1])
    plt.xlabel("Importance Score")
    plt.title("Feature Importance – Random Forest Cost Model")
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=150)
    plt.close()
    print("\n  Chart saved to feature_importance.png")


# ── Model comparison summary ──────────────────────────────────────────────────

def print_comparison(results: list):
    print(f"\n{'═'*55}")
    print("  Cost Prediction Model Comparison Summary")
    print(f"{'═'*55}")
    print(f"  {'Model':<38} {'R²':>8}")
    print(f"  {'─'*38} {'─'*8}")
    for r in sorted(results, key=lambda x: x["r2"], reverse=True):
        marker = " ✓ BEST" if r == max(results, key=lambda x: x["r2"]) else ""
        print(f"  {r['name']:<38} {r['r2']:>8.4f}{marker}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  BuildAdvisor – ML Training Pipeline")
    print("=" * 55)

    data = load_and_prepare()

    # 1. Train & evaluate cost models
    results = train_cost_models(
        data["X_train"], data["X_test"],
        data["X_train_scaled"], data["X_test_scaled"],
        data["y_cost_train"], data["y_cost_test"]
    )
    print_comparison(results)

    # Pick best cost model
    tree_results = [r for r in results if r["name"] != "Linear Regression (baseline)"]
    best_cost = max(tree_results, key=lambda x: x["r2"])
    print(f"\n  Saving best cost model: {best_cost['name']}")
    joblib.dump(best_cost["model"], "model.pkl")
    print("  Saved to model.pkl")

    if hasattr(best_cost["model"], "feature_importances_"):
        plot_feature_importance(best_cost["model"], data["feature_cols"])

    # 2. Train Materials Multi-Output Regressor
    print(f"\n{'═'*55}")
    print("  Training Materials Estimator Model")
    print(f"{'═'*55}")
    rf_mats = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1)
    )
    rf_mats.fit(data["X_train"], data["y_mats_train"])
    
    # Evaluate Materials Model
    y_mats_pred = rf_mats.predict(data["X_test"])
    print("  Material Prediction R² Scores:")
    for idx, col in enumerate(data["y_mats_train"].columns):
        col_r2 = r2_score(data["y_mats_test"].iloc[:, idx], y_mats_pred[:, idx])
        print(f"    - {col:<20} : {col_r2:.4f}")
        
    joblib.dump(rf_mats, "materials_model.pkl")
    print("  Saved Materials model to materials_model.pkl")

    # 3. Train Feasibility Regressor
    print(f"\n{'═'*55}")
    print("  Training Feasibility Scoring Model")
    print(f"{'═'*55}")
    rf_feas = RandomForestRegressor(n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1)
    rf_feas.fit(data["X_train"], data["y_feas_train"])
    
    # Evaluate Feasibility Model
    y_feas_pred = rf_feas.predict(data["X_test"])
    feas_r2 = r2_score(data["y_feas_test"], y_feas_pred)
    print(f"  Feasibility Score R² : {feas_r2:.4f}")
    
    joblib.dump(rf_feas, "feasibility_model.pkl")
    print("  Saved Feasibility model to feasibility_model.pkl")


if __name__ == "__main__":
    main()
