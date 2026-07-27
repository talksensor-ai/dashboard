import subprocess
import re

try:
    cmd = ["ssh", "ai@100.123.93.21", "cat /Users/ai/talk/pipeline/run_21.log"]
    log_content = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
    lines = log_content.split("\n")
    
    # We want to find all [TOKENS] lines
    # Example format: [TOKENS] prompt=10497 (cached=5888) completion=5693
    total_prompt = 0
    total_cached = 0
    total_completion = 0
    
    for line in lines:
        if "[TOKENS]" in line:
            # Parse prompt, cached, completion
            m = re.search(r"prompt=(\d+)\s+\(cached=(\d+)\)\s+completion=(\d+)", line)
            if m:
                total_prompt += int(m.group(1))
                total_cached += int(m.group(2))
                total_completion += int(m.group(3))
                
    print(f"Token counts from run_21.log:")
    print(f"  Total prompt tokens (including cached): {total_prompt}")
    print(f"  Total cached prompt tokens: {total_cached}")
    print(f"  Total non-cached prompt tokens: {total_prompt - total_cached}")
    print(f"  Total completion tokens: {total_completion}")
    
    # DeepSeek API pricing (for deepseek-chat/deepseek-reasoner or deepseek-v4-flash, let's look at deepseek-v3/r1 pricing)
    # Wait, the model is "deepseek-v4-flash". What is the pricing?
    # Wait, is deepseek-v4-flash a custom endpoint or Deepseek's official API?
    # DeepSeek's official API models are deepseek-chat ($0.14/1M prompt cached, $0.55/1M prompt uncached, $2.19/1M completion)
    # and deepseek-reasoner ($0.55/1M prompt cached, $2.19/1M prompt uncached, $2.19/1M completion).
    # If they are using a local proxy or deepseek api, let's calculate based on standard DeepSeek Chat/Coder (v3) API pricing:
    # Prompt Cache Hit: $0.14 / million tokens
    # Prompt Cache Miss: $0.55 / million tokens
    # Completion (output): $2.19 / million tokens
    # If they use DeepSeek R1 (deepseek-reasoner) pricing:
    # Prompt Cache Hit: $0.55 / million tokens
    # Prompt Cache Miss: $2.19 / million tokens
    # Completion: $2.19 / million tokens
    # Let's show both prices so they know exactly.
    
    # standard chat (v3) pricing
    cost_cached_v3 = (total_cached / 1_000_000) * 0.14
    cost_uncached_v3 = ((total_prompt - total_cached) / 1_000_000) * 0.55
    cost_comp_v3 = (total_completion / 1_000_000) * 2.19
    total_cost_v3 = cost_cached_v3 + cost_uncached_v3 + cost_comp_v3
    
    # reasoner (r1) pricing
    cost_cached_r1 = (total_cached / 1_000_000) * 0.55
    cost_uncached_r1 = ((total_prompt - total_cached) / 1_000_000) * 2.19
    cost_comp_r1 = (total_completion / 1_000_000) * 2.19
    total_cost_r1 = cost_cached_r1 + cost_uncached_r1 + cost_comp_r1
    
    print("\n--- Cost Estimation (USD) ---")
    print(f"DeepSeek V3 (Chat) Pricing:")
    print(f"  Prompt Cache Hit cost: ${cost_cached_v3:.4f}")
    print(f"  Prompt Cache Miss cost: ${cost_uncached_v3:.4f}")
    print(f"  Completion cost: ${cost_comp_v3:.4f}")
    print(f"  Total: ${total_cost_v3:.4f} USD (~{total_cost_v3 * 80:.2f} rub)")
    
    print(f"\nDeepSeek R1 (Reasoner) Pricing:")
    print(f"  Prompt Cache Hit cost: ${cost_cached_r1:.4f}")
    print(f"  Prompt Cache Miss cost: ${cost_uncached_r1:.4f}")
    print(f"  Completion cost: ${cost_comp_r1:.4f}")
    print(f"  Total: ${total_cost_r1:.4f} USD (~{total_cost_r1 * 80:.2f} rub)")
    
except Exception as e:
    print("Error:", e)
