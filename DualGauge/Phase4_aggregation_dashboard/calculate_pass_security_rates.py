import os
import json
 
def aggregate_summary(base_dir="."):
    totals = {
        "Security": {"passed": 0, "total": 0},
        "Functional Correctness": {"passed": 0, "total": 0},
    }
 
    # Walk through directories recursively
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == "summary.json":
                path = os.path.join(root, file)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        categories = data.get("categories", {})
                        for key in totals.keys():
                            cat = categories.get(key)
                            if cat:
                                totals[key]["passed"] += cat.get("passed_test_cases", 0)
                                totals[key]["total"] += cat.get("total_test_cases", 0)
                except Exception as e:
                    print(f"Error reading {path}: {e}")
 
    # Compute and print summary
    print("\n=== Aggregate Summary ===")
    for key, values in totals.items():
        passed = values["passed"]
        total = values["total"]
        percent = (passed / total * 100) if total > 0 else 0
        print(f"{key}: {passed}/{total} passed ({percent:.2f}%)")
 
if __name__ == "__main__":
    aggregate_summary(".")