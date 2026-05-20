import requests, os, json
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

key = os.environ["DEEPSEEK_API_KEY"]
r = requests.get(
    "https://api.deepseek.com/user/balance",
    headers={"Authorization": f"Bearer {key}", "Accept": "application/json"}
)
print(json.dumps(r.json(), indent=2))

# Also recalculate our actual spend with correct prices
with open("e:/talk/cache_stats_23_april.json", "r") as f:
    stats = json.load(f)

print("\n=== ACTUAL COSTS (correct prices) ===")
print(f"Prices: input_miss=$0.28/1M, input_hit=$0.028/1M, output=$0.42/1M\n")

total_cost = 0
for r_entry in stats["requests_log"]:
    hit_cost = r_entry["cache_hit"] * 0.028 / 1_000_000
    miss_cost = r_entry["cache_miss"] * 0.28 / 1_000_000
    out_cost = r_entry["completion_tokens"] * 0.42 / 1_000_000
    entry_cost = hit_cost + miss_cost + out_cost
    total_cost += entry_cost
    print(f"  {r_entry['step']:20s} | hit=${hit_cost:.6f} miss=${miss_cost:.6f} out=${out_cost:.6f} | TOTAL=${entry_cost:.6f}")

print(f"\n  TOTAL SPENT on 1 hour: ${total_cost:.4f}")
print(f"  In rubles (~78 rub/$):  {total_cost * 78:.2f} rub")
