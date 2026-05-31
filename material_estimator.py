"""
BuildAdvisor – Material Estimator
Calculates required construction material quantities based on building specs.
Uses Pakistan construction engineering standards.
"""

import math

# ── Material rates ─────────────────────────────────────────────────────────────

CEMENT_RATES = {
    # bags per sqft of floor area
    "brick":    {"foundation": 0.38, "superstructure": 0.28, "plaster": 0.18},
    "concrete": {"foundation": 0.50, "superstructure": 0.45, "plaster": 0.12},
    "steel":    {"foundation": 0.45, "superstructure": 0.08, "plaster": 0.08},
}

STEEL_KG_PER_SQFT   = {"brick": 2.8,  "concrete": 5.8,  "steel": 9.5}
BRICK_PER_SQFT_WALL = 9        # bricks per sqft of single-wythe wall
FLOOR_HEIGHT_FT     = 10       # standard floor height
SAND_RATIO          = 3.2      # cubic ft sand per cement bag
AGGREGATE_FACTOR    = {"brick": 0.35, "concrete": 1.0, "steel": 0.55}
AGGREGATE_RATIO     = 4.5      # cubic ft aggregate per cement bag (concrete only)

PAINT_COVERAGE      = 12       # sqft per litre per coat
TILE_BATHROOM_SQFT  = {"basic": 70, "standard": 90, "premium": 110}

QUALITY_TILE_FACTOR = {"basic": 1.0, "standard": 1.15, "premium": 1.40}

WIRE_PER_SQFT       = 2.8      # metres of electrical wire per sqft
PVC_PER_BATH        = 38       # metres PVC per bathroom
RISER_PER_FLOOR     = 14       # metres riser pipe per floor

WATER_TANK_BASE     = 1000     # gallons base
WATER_PER_ROOM      = 500      # gallons per room


# ── Internal helpers ───────────────────────────────────────────────────────────

def _perimeter(area_per_floor: float) -> float:
    """Estimate building perimeter from footprint area (non-square factor 1.15)."""
    return 4 * math.sqrt(area_per_floor) * 1.15


def _wall_area(total_area: float, floors: int) -> float:
    area_per_floor = total_area / floors
    perim = _perimeter(area_per_floor)
    gross = perim * FLOOR_HEIGHT_FT * floors
    return gross * 0.82          # 18 % deducted for openings (doors/windows)


# ── Public API ─────────────────────────────────────────────────────────────────

def estimate_materials(
    total_area_sqft:     float,
    number_of_floors:    int,
    number_of_rooms:     int,
    number_of_bathrooms: int,
    construction_type:   str,
    quality_level:       str,
    structure_type:      str,
    soil_type:           str,
    avg_temp_summer:     float,
    avg_temp_winter:     float,
) -> dict:
    """
    Returns a nested dict of material quantities grouped by category:
      structural / finishing / mep / meta
    """
    area   = total_area_sqft
    floors = number_of_floors
    rooms  = number_of_rooms
    baths  = number_of_bathrooms
    st     = structure_type
    ql     = quality_level

    w_area = _wall_area(area, floors)

    # ── Structural (Machine Learning Model Prediction) ────────────────────────
    from predict import predict_materials
    ml_mats = predict_materials({
        "total_area_sqft": area,
        "number_of_floors": floors,
        "number_of_rooms": rooms,
        "number_of_bathrooms": baths,
        "location_factor": 1.0,  # Materials are structurally constant regardless of cost factors
        "construction_type": construction_type,
        "quality_level": ql,
        "structure_type": st,
        "soil_type": soil_type,
        "avg_temp_summer": avg_temp_summer,
        "avg_temp_winter": avg_temp_winter,
    })
    cement_total = ml_mats["cement_bags"]
    sand_total = ml_mats["sand_cft"]
    agg_total = ml_mats["aggregate_cft"]
    bricks = ml_mats["bricks"]
    steel_kg = ml_mats["steel_bars_kg"]

    # ── Finishing ─────────────────────────────────────────────────────────────
    paintable   = w_area * 2 + area         # walls (both faces) + ceilings
    paint_ltr   = round(paintable / PAINT_COVERAGE * 2)   # 2 coats

    tf          = QUALITY_TILE_FACTOR[ql]
    tiles_floor = round(area * tf)
    tiles_bath  = round(baths * TILE_BATHROOM_SQFT[ql] * tf)
    tiles_total = tiles_floor + tiles_bath

    doors       = rooms + baths + 2         # +2 for main & back entrance
    windows     = rooms * 2 + (floors if construction_type == "commercial" else 0)
    glass_sqft  = windows * 15              # avg 15 sqft per window

    # ── MEP ───────────────────────────────────────────────────────────────────
    wiring_m    = round(area * WIRE_PER_SQFT)
    switches    = rooms * 2 + baths + 4    # per room avg + extras
    mcbs        = rooms + baths + 4         # MCB / breakers
    pvc_m       = round(baths * PVC_PER_BATH + floors * RISER_PER_FLOOR)
    sanitary    = baths * 3                 # WC + washbasin + shower/tap set
    tank_gal    = WATER_TANK_BASE + rooms * WATER_PER_ROOM

    return {
        "structural": {
            "Cement Bags (50 kg)": cement_total,
            "Sand (cubic ft)":     sand_total,
            "Aggregate (cubic ft)": agg_total,
            "Bricks":              bricks,
            "Steel Bars (kg)":     steel_kg,
        },
        "finishing": {
            "Paint (litres)":      paint_ltr,
            "Tiles (sqft)":        tiles_total,
            "Doors":               doors,
            "Windows":             windows,
            "Glass (sqft)":        glass_sqft,
        },
        "mep": {
            "Electrical Wire (m)":  wiring_m,
            "Switchboards":         switches,
            "MCB Breakers":         mcbs,
            "PVC Pipe (m)":         pvc_m,
            "Sanitary Units":       sanitary,
            "Water Tank (gallons)": tank_gal,
        },
        "meta": {
            "wall_area_sqft":   round(w_area),
            "floor_area_sqft":  round(area),
        },
    }
