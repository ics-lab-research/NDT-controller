from pathlib import Path
from loguru import logger

from src.core.utils import load_experiment_plans
from typing import List
from src.core.models import ExperimentPlan


def update_details(selected_filename: str, plans: List[ExperimentPlan]):
    # ) -> List[List[str]]:
    logger.info(
        f"Updating details for selected experiment: {selected_filename}"
    )
    if not selected_filename:
        return []
    plan = next((p for p in plans if p.filename == selected_filename), None)
    print(plan)
    if not plan:
        logger.warning(f"Plan not found for filename: {selected_filename}")
        return [["Error", "", ""]]
    data = []
    for tool in plan.experiment:
        if tool == "unknown":
            continue
        tool_name = tool.tool_name
        params = vars(tool)
        params.pop("tool_name", None)
        param_list = [f"{k}={v}" for k, v in params.items()]
        param1 = param_list[0] if len(param_list) > 0 else ""
        param2 = param_list[1] if len(param_list) > 1 else ""
        data.append([tool_name, param1, param2])
    logger.info(f"Details updated with {len(data)} tools")
    return data


def main():
    """Run the load_experiment_plans function and print the result."""
    filepath = Path("EXPERIMENTS/labview_experiment_plans.json")
    plans = load_experiment_plans(filepath)

    # for plan in plans:
    #     print("========================")
    #     print(plan.filename)

    #     for tool in plan.experiment:
    #         if tool == "unknown":
    #             continue
    #         params = vars(tool)
    #         params.pop("tool_name", None)
    #         param_list = [f"{k}={v}" for k, v in params.items()]
    #         param1 = param_list[0] if len(param_list) > 0 else ""
    #         param2 = param_list[1] if len(param_list) > 1 else ""
    #         print(param1)
    #         print(param2)

    test = update_details(
        selected_filename="gaussian_30x30_freq2000", plans=plans
    )

    print(test)


if __name__ == "__main__":
    main()
