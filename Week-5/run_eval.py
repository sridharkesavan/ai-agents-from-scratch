import json
import sys
sys.path.append("../Week-5")  # so we can import from the Week-3 folder

from golden_dataset import golden_dataset
from eval_judge import judge_report
from langfuse import observe, propagate_attributes, get_client
#from agent_langgraphV1 import app  # the compiled LangGraph app, confirmed correct file
from agent_langgraphV1_Fuse import app  # the compiled LangGraph app, confirmed correct file

langfuse = get_client()

def get_report(topic: str, test_id: str) -> str:
    with propagate_attributes(trace_name=f"eval-{test_id}", tags=["week5-eval"]):
        result = app.invoke({
            "topic": topic,
            "report": "",
            "critique": "",
            "sources": [],
            "round": 0,
            "max_rounds": 2
        })
    return result["report"]

def run_evaluation():
    all_results = []

    for item in golden_dataset:
        print(f"\n{'='*60}")
        print(f"Running: {item['id']} — {item['topic']}")
        print('='*60)

        report = get_report(item["topic"], item["id"])

        judgment = judge_report(item["topic"], item["criteria"], report)

        passed = sum(1 for r in judgment["results"] if r["pass"])
        total = len(judgment["results"])

        print(f"Score: {passed}/{total}")
        for r in judgment["results"]:
            status = "✅" if r["pass"] else "❌"
            print(f"  {status} {r['criterion']}")
            if not r["pass"]:
                print(f"     → {r['reason']}")

        all_results.append({
            "id": item["id"],
            "topic": item["topic"],
            "passed": passed,
            "total": total,
            "details": judgment["results"]
        })

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    total_passed = sum(r["passed"] for r in all_results)
    total_criteria = sum(r["total"] for r in all_results)
    print(f"Overall: {total_passed}/{total_criteria} criteria passed across {len(all_results)} test cases\n")

    for r in all_results:
        bar = "█" * r["passed"] + "░" * (r["total"] - r["passed"])
        print(f"  {r['id']:20s} {bar}  {r['passed']}/{r['total']}")

    with open("eval_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nFull results saved to eval_results.json")

if __name__ == "__main__":
    run_evaluation()