"""
BuildAdvisor – Synthetic Dataset Generator
Generates realistic construction cost, material quantities, and feasibility data for model training.
Includes weather and soil conditions.
"""

import numpy as np
import pandas as pd

QUALITY_BASE_RATES = {
    "basic": 2500,
    "standard": 3500,
    "premium": 5000,
}

STRUCTURE_FACTORS = {
    "brick": 1.0,
    "concrete": 1.15,
    "steel": 1.30,
}

CONSTRUCTION_TYPE_FACTORS = {
    "residential": 1.0,
    "commercial": 1.25,
}

# ── Material Estimation Tables ────────────────────────────────────────────────
CEMENT_RATES = {
    "brick":    {"foundation": 0.38, "superstructure": 0.28, "plaster": 0.18},
    "concrete": {"foundation": 0.50, "superstructure": 0.45, "plaster": 0.12},
    "steel":    {"foundation": 0.45, "superstructure": 0.08, "plaster": 0.08},
}
STEEL_KG_PER_SQFT = {"brick": 2.8, "concrete": 5.8, "steel": 9.5}
BRICK_PER_SQFT_WALL = 9
SAND_RATIO = 3.2
AGGREGATE_FACTOR = {"brick": 0.35, "concrete": 1.0, "steel": 0.55}
AGGREGATE_RATIO = 4.5


def _floor_factor(floors: int) -> float:
    """Cost per sqft rises with floors due to structural load and logistics."""
    if floors == 1:
        return 1.0
    elif floors == 2:
        return 1.08
    elif floors == 3:
        return 1.16
    else:
        return 1.16 + (floors - 3) * 0.06


def _wall_area_vect(total_area: np.ndarray, floors: np.ndarray) -> np.ndarray:
    area_per_floor = total_area / floors
    perim = 4 * np.sqrt(area_per_floor) * 1.15
    gross = perim * 10 * floors
    return gross * 0.82  # Deduct 18% for openings


def generate_dataset(n_samples: int = 3000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    construction_types = rng.choice(["residential", "commercial"], size=n_samples, p=[0.65, 0.35])
    quality_levels = rng.choice(["basic", "standard", "premium"], size=n_samples, p=[0.30, 0.45, 0.25])
    structure_types = rng.choice(["brick", "concrete", "steel"], size=n_samples, p=[0.50, 0.35, 0.15])

    # Soil & Weather Conditions
    soil_types = rng.choice(["clay", "silt", "sand", "gravel", "rock"], size=n_samples, p=[0.22, 0.15, 0.23, 0.25, 0.15])
    avg_temp_summer = rng.uniform(25.0, 50.0, n_samples).round(1)
    avg_temp_winter = rng.uniform(-10.0, 25.0, n_samples).round(1)

    # Area: residential 600–5000, commercial 1500–15000 sqft
    total_area_sqft = np.where(
        construction_types == "residential",
        rng.uniform(600, 5000, n_samples),
        rng.uniform(1500, 15000, n_samples),
    ).round(1)

    number_of_floors = rng.integers(1, 8, size=n_samples)

    # Rooms/bathrooms scale loosely with area and floors
    number_of_rooms = np.clip(
        (total_area_sqft / 300).astype(int) + rng.integers(-1, 2, size=n_samples),
        2, 30
    )
    number_of_bathrooms = np.clip(
        (number_of_rooms / 3).astype(int) + rng.integers(0, 2, size=n_samples),
        1, 12
    )

    location_factor = rng.uniform(1.0, 1.3, n_samples).round(2)

    # ── 1. Cost calculation ───────────────────────────────────────────────────
    base_rates = np.array([QUALITY_BASE_RATES[q] for q in quality_levels])
    struct_factors = np.array([STRUCTURE_FACTORS[s] for s in structure_types])
    constr_factors = np.array([CONSTRUCTION_TYPE_FACTORS[c] for c in construction_types])
    floor_factors = np.array([_floor_factor(f) for f in number_of_floors])

    # Soil Factors
    SOIL_FACTORS = {
        "clay": 1.08,
        "silt": 1.03,
        "sand": 1.01,
        "gravel": 1.00,
        "rock": 1.12,
    }
    soil_factors = np.array([SOIL_FACTORS[s] for s in soil_types])

    # Temperature Cost factors
    summer_excess = np.maximum(0.0, avg_temp_summer - 40.0)
    summer_temp_factor = 1.0 + (summer_excess * 0.01)

    winter_excess = np.maximum(0.0, 5.0 - avg_temp_winter)
    winter_temp_factor = 1.0 + (winter_excess * 0.015)

    cost_before_noise = (
        total_area_sqft
        * base_rates
        * floor_factors
        * struct_factors
        * constr_factors
        * location_factor
        * soil_factors
        * summer_temp_factor
        * winter_temp_factor
    )

    # Gaussian noise ±8%
    noise_pct = rng.normal(0, 0.08, n_samples)
    total_cost = (cost_before_noise * (1 + noise_pct)).round(0)

    # ── 2. Material Calculations ──────────────────────────────────────────────
    cem_found_rates = np.array([CEMENT_RATES[s]["foundation"] for s in structure_types])
    cem_super_rates = np.array([CEMENT_RATES[s]["superstructure"] for s in structure_types])
    cem_plaster_rates = np.array([CEMENT_RATES[s]["plaster"] for s in structure_types])
    
    w_area = _wall_area_vect(total_area_sqft, number_of_floors)
    
    # Soil adjustments for materials (Clay / Silt need raft foundation, rock/gravel need less foundation)
    MAT_SOIL_ADJ = {
        "clay": 1.10,
        "silt": 1.03,
        "sand": 1.00,
        "gravel": 0.95,
        "rock": 0.95,
    }
    mat_soil_adj = np.array([MAT_SOIL_ADJ[s] for s in soil_types])

    cement_found = total_area_sqft * cem_found_rates
    cement_super = total_area_sqft * cem_super_rates
    cement_plstr = (w_area * 2) * cem_plaster_rates / 10
    cement_total = (cement_found + cement_super + cement_plstr) * mat_soil_adj
    
    # Add noise to cement total: ±6%
    cement_bags = (cement_total * (1 + rng.normal(0, 0.06, n_samples))).round(0).astype(int)
    
    # Sand: cement * 3.2 + noise
    sand_cft = (cement_bags * SAND_RATIO * (1 + rng.normal(0, 0.05, n_samples))).round(0).astype(int)
    
    # Aggregate: cement * 4.5 * factor + noise
    agg_factors = np.array([AGGREGATE_FACTOR[s] for s in structure_types])
    aggregate_cft = (cement_bags * AGGREGATE_RATIO * agg_factors * (1 + rng.normal(0, 0.05, n_samples))).round(0).astype(int)
    
    # Bricks: depending on structure type
    brick_factors = np.where(structure_types == "brick", 1.0, np.where(structure_types == "concrete", 0.25, 0.15))
    bricks_base = w_area * BRICK_PER_SQFT_WALL * brick_factors
    bricks = (bricks_base * (1 + rng.normal(0, 0.07, n_samples))).round(0).astype(int)
    
    # Steel:
    steel_rates = np.array([STEEL_KG_PER_SQFT[s] for s in structure_types])
    steel_base = total_area_sqft * steel_rates * mat_soil_adj
    steel_bars_kg = (steel_base * (1 + rng.normal(0, 0.06, n_samples))).round(0).astype(int)

    # ── 3. Feasibility Score Calculation ──────────────────────────────────────
    feas_scores = np.ones(n_samples) * 100.0
    
    # Structural limits
    max_fl = np.where(structure_types == "brick", 3, np.where(structure_types == "concrete", 10, 25))
    over_fl = number_of_floors - max_fl
    penalty_struct = np.where(over_fl > 0, np.minimum(35.0, over_fl * 15.0), 0.0)
    penalty_struct = np.where(over_fl == 0, 5.0, penalty_struct)
    feas_scores -= penalty_struct
    
    # Zoning limits
    max_height = np.where(construction_types == "residential", 45, 120)
    heights = number_of_floors * 10
    penalty_height = np.where(heights > max_height, 12.0, 0.0)
    feas_scores -= penalty_height
    
    min_area = np.where(construction_types == "residential", 400.0, 1500.0)
    penalty_area = np.where(total_area_sqft < min_area, 6.0, 0.0)
    feas_scores -= penalty_area
    
    penalty_comm_brick = np.where((construction_types == "commercial") & (structure_types == "brick"), 8.0, 0.0)
    feas_scores -= penalty_comm_brick
    
    # Layout comfort
    sqft_per_room = total_area_sqft / number_of_rooms
    penalty_comfort = np.where(sqft_per_room < 100.0, 8.0, 0.0)
    feas_scores -= penalty_comfort
    
    # Soil penalties
    penalty_soil = np.where(soil_types == "clay", 8.0, np.where(soil_types == "silt", 4.0, 0.0))
    feas_scores -= penalty_soil
    
    # Clay + Floors >= 4 (deep structural hazards)
    penalty_clay_highrise = np.where((soil_types == "clay") & (number_of_floors >= 4), 25.0, 0.0)
    feas_scores -= penalty_clay_highrise
    
    # Temperature penalties
    penalty_temp_summer = np.where(avg_temp_summer > 42.0, 3.0, 0.0)
    penalty_temp_winter = np.where(avg_temp_winter < 0.0, 3.0, 0.0)
    feas_scores -= (penalty_temp_summer + penalty_temp_winter)

    # Add random inspection variance (std = 4.0)
    feasibility_noise = rng.normal(0.0, 4.0, n_samples)
    feasibility_score = np.clip(feas_scores + feasibility_noise, 10.0, 100.0).round(0).astype(int)

    df = pd.DataFrame({
        "total_area_sqft": total_area_sqft,
        "number_of_floors": number_of_floors,
        "number_of_rooms": number_of_rooms,
        "number_of_bathrooms": number_of_bathrooms,
        "location_factor": location_factor,
        "construction_type": construction_types,
        "quality_level": quality_levels,
        "structure_type": structure_types,
        "soil_type": soil_types,
        "avg_temp_summer": avg_temp_summer,
        "avg_temp_winter": avg_temp_winter,
        "total_cost": total_cost.astype(int),
        "cement_bags": cement_bags,
        "sand_cft": sand_cft,
        "aggregate_cft": aggregate_cft,
        "bricks": bricks,
        "steel_bars_kg": steel_bars_kg,
        "feasibility_score": feasibility_score,
    })

    return df


if __name__ == "__main__":
    df = generate_dataset(n_samples=3000)
    print(f"Dataset shape: {df.shape}")
    print(df.head())
    print("\nBasic stats:")
    print(df[["total_cost", "soil_type", "avg_temp_summer", "feasibility_score"]].describe())
