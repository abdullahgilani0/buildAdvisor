"""
BuildAdvisor – Feasibility Analyzer
Scores a construction project across structural, zoning, budget, and
environmental dimensions, and returns actionable recommendations.
"""

# ── Reference tables ───────────────────────────────────────────────────────────

MAX_FLOORS = {"brick": 3, "concrete": 10, "steel": 25}

FOUNDATION_DEPTH = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8}   # floors → depth in ft

ZONING = {
    "residential": {
        "max_height_ft":  45,
        "max_coverage":   60,    # % of plot
        "setback_ft":      5,
        "min_area_sqft":  400,
    },
    "commercial": {
        "max_height_ft": 120,
        "max_coverage":   75,
        "setback_ft":     10,
        "min_area_sqft": 1500,
    },
}

GREEN_BASE = {"basic": 28, "standard": 55, "premium": 82}

STRUCT_LABEL = {
    "brick":    "Reinforced Brick Masonry (RBM)",
    "concrete": "Reinforced Cement Concrete (RCC)",
    "steel":    "Structural Steel Frame",
}


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_feasibility(
    total_area_sqft:     float,
    number_of_floors:    int,
    number_of_rooms:     int,
    number_of_bathrooms: int,
    location_factor:     float,
    construction_type:   str,
    quality_level:       str,
    structure_type:      str,
    predicted_cost:      int,
    soil_type:           str,
    avg_temp_summer:     float,
    avg_temp_winter:     float,
) -> dict:
    """
    Returns a full feasibility report dict.
    """
    issues          = []
    warnings        = []
    recommendations = []

    # Predict baseline feasibility score using ML
    from predict import predict_feasibility_score
    try:
        ml_score = predict_feasibility_score({
            "total_area_sqft":     total_area_sqft,
            "number_of_floors":    number_of_floors,
            "number_of_rooms":     number_of_rooms,
            "number_of_bathrooms": number_of_bathrooms,
            "location_factor":     location_factor,
            "construction_type":   construction_type,
            "quality_level":       quality_level,
            "structure_type":      structure_type,
            "soil_type":           soil_type,
            "avg_temp_summer":     avg_temp_summer,
            "avg_temp_winter":     avg_temp_winter,
        })
        score = round(ml_score)
    except Exception:
        score = 100  # Fallback in case model is not trained yet

    # ── 1. Structural feasibility ─────────────────────────────────────────────
    max_fl   = MAX_FLOORS[structure_type]
    struct_ok = number_of_floors <= max_fl

    if not struct_ok:
        over = number_of_floors - max_fl
        issues.append(
            f"{STRUCT_LABEL[structure_type]} supports a maximum of {max_fl} floor(s). "
            f"Your design has {number_of_floors} floors ({over} over the limit). "
            f"Upgrade to {'Concrete' if structure_type=='brick' else 'Steel'} structure."
        )
        # Safety Override: Force score to be low if structural integrity is failed
        score = min(score, 45)
    elif number_of_floors == max_fl:
        warnings.append(
            f"You are at the ceiling for {structure_type} construction ({max_fl} floors). "
            "Engineering review by a licensed structural engineer is mandatory."
        )

    struct_score = max(10, 100 - max(0, (number_of_floors - max_fl)) * 20) if struct_ok else max(10, 100 - (number_of_floors - max_fl) * 25)

    # ── 2. Zoning compliance ──────────────────────────────────────────────────
    z            = ZONING[construction_type]
    height_ft    = number_of_floors * 10
    height_ok    = height_ft <= z["max_height_ft"]
    min_area_ok  = total_area_sqft >= z["min_area_sqft"]

    if not height_ok:
        warnings.append(
            f"Building height ({height_ft} ft) exceeds the typical {construction_type} "
            f"zoning limit ({z['max_height_ft']} ft). Obtain a height variance permit."
        )

    if not min_area_ok:
        warnings.append(
            f"Total area ({total_area_sqft:,.0f} sqft) is below the recommended minimum "
            f"for {construction_type} use ({z['min_area_sqft']:,} sqft)."
        )

    if construction_type == "commercial" and structure_type == "brick":
        warnings.append(
            "Brick masonry is rarely approved for commercial buildings in urban zones. "
            "RCC or steel frame is strongly preferred."
        )

    zoning_score = 100
    if not height_ok:   zoning_score -= 20
    if not min_area_ok: zoning_score -= 15
    if construction_type == "commercial" and structure_type == "brick": zoning_score -= 15
    zoning_score = max(10, zoning_score)

    # ── 3. Space & comfort ratios ─────────────────────────────────────────────
    sqft_per_room = total_area_sqft / max(number_of_rooms, 1)
    bath_ratio    = number_of_rooms / max(number_of_bathrooms, 1)

    if sqft_per_room < 100:
        warnings.append(
            f"Very cramped layout: {sqft_per_room:.0f} sqft per room on average. "
            "Consider reducing rooms or increasing total area."
        )
    elif sqft_per_room > 700:
        recommendations.append(
            "Large average room size detected. Open-plan design or commercial partitioning "
            "will maximise space efficiency."
        )

    if bath_ratio > 4:
        recommendations.append(
            f"1 bathroom per {bath_ratio:.0f} rooms is below comfort standards. "
            "Adding a bathroom improves livability and resale value significantly."
        )

    # ── 4. Budget range ───────────────────────────────────────────────────────
    low_est   = round(predicted_cost * 0.87)
    high_est  = round(predicted_cost * 1.16)
    # Simple annuity: 15% p.a., 10-year loan, monthly
    r         = 0.15 / 12
    n         = 120
    monthly   = round(predicted_cost * r * (1 + r)**n / ((1 + r)**n - 1))
    cost_psf  = round(predicted_cost / total_area_sqft)
    budget_score = 85   # assume feasible if budget is available

    # ── 5. Foundation & site ──────────────────────────────────────────────────
    found_depth = FOUNDATION_DEPTH.get(min(number_of_floors, 5), 9)
    if structure_type == "steel":
        found_depth += 2

    # Adjust foundation depth based on soil type
    if soil_type == "clay":
        found_depth += 2
    elif soil_type == "rock":
        found_depth = max(3, found_depth - 1)

    if location_factor >= 1.2:
        recommendations.append(
            "High-value location detected. Consider pile/raft foundation for long-term "
            "structural integrity and property value protection."
        )

    soil_test_required = number_of_floors >= 3 or structure_type in ("concrete", "steel") or soil_type in ("clay", "silt")
    if soil_test_required:
        recommendations.append(
            "Soil Bearing Capacity (SBC) test is mandatory for your configuration. "
            "Commission a geotechnical survey before breaking ground."
        )

    # Soil-specific alerts
    if soil_type == "clay":
        warnings.append(
            "Clay soil detected. Clay is highly prone to swelling and shrinkage. "
            "A raft (mat) foundation or deep piles are required to prevent structural settlement."
        )
        if number_of_floors >= 4:
            issues.append(
                "High-rise construction (4+ floors) on clay soil is highly restricted and requires "
                "structural pile foundations deep into solid strata. Geotechnical review is critical."
            )
    elif soil_type == "silt":
        warnings.append(
            "Silt soil detected. Silt has moderate bearing capacity and is highly susceptible to "
            "water erosion and frost heaving. Ensure robust site drainage."
        )
    elif soil_type == "rock":
        recommendations.append(
            "Rock subgrade detected. Excellent bearing capacity allows for minimal foundation depth "
            "(3-4 ft), though excavation will be more costly."
        )
    elif soil_type == "sand":
        warnings.append(
            "Sandy soil detected. Sand has good drainage but lacks cohesion. Excavations require "
            "shoring to prevent cave-ins, and foundation settlement must be monitored."
        )

    drainage_note = (
        "Ensure site drainage plan is prepared — commercial buildings require "
        "a formal stormwater management system."
        if construction_type == "commercial"
        else "Verify site drainage; low-lying plots require a 1–2 ft plinth raise."
    )
    recommendations.append(drainage_note)

    # ── 6. Environmental / green ──────────────────────────────────────────────
    green_score = GREEN_BASE[quality_level]

    if structure_type == "steel":
        green_score += 12
        recommendations.append(
            "Steel structures use recyclable material — a sound environmental choice. "
            "Consider cool-roof coatings to reduce heat gain."
        )
    if quality_level == "premium":
        recommendations.append(
            "Premium quality opens the door to double-glazed windows, spray foam insulation, "
            "and rooftop solar panels — all increasing property value."
        )
    if quality_level == "basic":
        recommendations.append(
            "Even on a basic budget, cavity-wall insulation saves 20–30 % on cooling costs. "
            "Plan electrical conduit for future solar addition."
        )
    if number_of_floors >= 3:
        recommendations.append(
            "Multi-storey buildings benefit greatly from a central HVAC system; "
            "plan the risers now to avoid costly retrofitting."
        )

    # Temperature-specific alerts
    if avg_temp_summer > 42.0:
        recommendations.append(
            f"Extreme summer heat detected ({avg_temp_summer}°C). High thermal resistance insulation "
            "(cavity walls, double-glazing, cool roof coatings) is essential to reduce HVAC loads."
        )
    if avg_temp_winter < 2.0:
        recommendations.append(
            f"Freezing winter temperatures detected ({avg_temp_winter}°C). Implement wall and floor insulation "
            "(e.g., polystyrene boards) and plan a robust space heating system."
        )

    green_score = min(100, green_score)

    # ── Overall risk ──────────────────────────────────────────────────────────
    score = max(0, min(100, score))
    if score >= 78:
        risk, risk_color, risk_emoji = "LOW",    "#3dd68c", "✅"
    elif score >= 55:
        risk, risk_color, risk_emoji = "MEDIUM", "#f5a623", "⚠️"
    else:
        risk, risk_color, risk_emoji = "HIGH",   "#f87171", "🔴"

    return {
        "overall_score":  score,
        "risk_level":     risk,
        "risk_color":     risk_color,
        "risk_emoji":     risk_emoji,
        "scores": {
            "Structural":    min(100, struct_score),
            "Zoning":        zoning_score,
            "Budget":        budget_score,
            "Environmental": green_score,
        },
        "issues":          issues,
        "warnings":        warnings,
        "recommendations": recommendations,
        "budget": {
            "low_estimate":        low_est,
            "predicted":           predicted_cost,
            "high_estimate":       high_est,
            "monthly_installment": monthly,
            "cost_per_sqft":       cost_psf,
        },
        "site": {
            "building_height_ft":  height_ft,
            "foundation_depth_ft": found_depth,
            "setback_required_ft": z["setback_ft"],
            "max_coverage_pct":    z["max_coverage"],
            "soil_test_required":  soil_test_required,
            "structure_system":    STRUCT_LABEL[structure_type],
        },
    }
