"""
BuildAdvisor – Interactive Prediction CLI
Prompts the user for building details and returns a cost estimate.
"""

from predict import predict_cost


def get_float(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = float(input(prompt))
            if min_val is not None and val < min_val:
                print(f"  ✗ Value must be at least {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  ✗ Value must be at most {max_val}")
                continue
            return val
        except ValueError:
            print("  ✗ Please enter a valid number.")


def get_int(prompt, min_val=1, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if val < min_val:
                print(f"  ✗ Value must be at least {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  ✗ Value must be at most {max_val}")
                continue
            return val
        except ValueError:
            print("  ✗ Please enter a whole number.")


def get_choice(prompt, choices):
    choices_str = " / ".join(choices)
    while True:
        val = input(f"{prompt} [{choices_str}]: ").strip().lower()
        if val in choices:
            return val
        print(f"  ✗ Choose one of: {choices_str}")


def main():
    print()
    print("=" * 55)
    print("  BuildAdvisor – Interactive Cost Estimator")
    print("=" * 55)
    print("  Enter your building details below.")
    print("  Press Ctrl+C at any time to exit.\n")

    try:
        while True:
            area       = get_float("  Total area (sqft)          : ", min_val=100)
            floors     = get_int  ("  Number of floors            : ", min_val=1, max_val=20)
            rooms      = get_int  ("  Number of rooms             : ", min_val=1, max_val=50)
            bathrooms  = get_int  ("  Number of bathrooms         : ", min_val=1, max_val=20)
            loc_factor = get_float("  Location factor (1.0–1.3)   : ", min_val=1.0, max_val=1.3)
            constr     = get_choice("  Construction type          ", ["residential", "commercial"])
            quality    = get_choice("  Quality level              ", ["basic", "standard", "premium"])
            structure  = get_choice("  Structure type             ", ["brick", "concrete", "steel"])

            print()
            print("  " + "─" * 45)

            result = predict_cost({
                "total_area_sqft":     area,
                "number_of_floors":    floors,
                "number_of_rooms":     rooms,
                "number_of_bathrooms": bathrooms,
                "location_factor":     loc_factor,
                "construction_type":   constr,
                "quality_level":       quality,
                "structure_type":      structure,
            })

            print(f"  ► Predicted Cost : {result['formatted']}")
            print("  " + "─" * 45)

            again = input("\n  Run another estimate? (y/n): ").strip().lower()
            if again != "y":
                break
            print()

    except KeyboardInterrupt:
        pass

    print("\n  Goodbye!\n")


if __name__ == "__main__":
    main()
