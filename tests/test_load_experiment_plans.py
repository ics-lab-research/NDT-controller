from pathlib import Path

from src.core.utils import load_experiment_plans


def main():
    """Run the load_experiment_plans function and print the result."""
    filepath = Path("EXPERIMENTS/labview_experiment_plans.json")
    plans = load_experiment_plans(filepath)
    print(plans)


if __name__ == "__main__":
    main()
