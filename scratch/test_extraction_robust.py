import os
import sys

# Add the plugins directory to sys.path
sys.path.append(os.getcwd())

from plugins.utils import extract_ep_label_robust

test_cases = [
    "Vashikaran 15 & 20",
    "Story 15 to 20",
    "Ep 15 & 20",
    "15-20",
    "15 & 20 Vashikaran",
    "15 Vashikaran 20",
]

print(f"{'Input':<30} | {'Label':<10} | {'Numbers':<15} | {'Is Range'}")
print("-" * 70)

for tc in test_cases:
    res = extract_ep_label_robust(tc)
    print(f"{tc:<30} | {res['label']:<10} | {str(res['numbers']):<15} | {res['is_range']}")
