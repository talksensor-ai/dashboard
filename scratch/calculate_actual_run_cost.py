import re
import sys

def main():
    log_path = 'run_21_mac.log'
    try:
        with open(log_path, 'r', encoding='utf-16') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading UTF-16: {e}")
        return

    # Find token statistics
    # Format: [TOKENS] prompt=10382 (cached=10368) completion=4131
    pattern = re.compile(r'\[TOKENS\] prompt=(\d+)\s+\(cached=(\d+)\)\s+completion=(\d+)')
    matches = pattern.findall(text)
    
    total_prompt = 0
    total_cached = 0
    total_completion = 0
    
    for m in matches:
        total_prompt += int(m[0])
        total_cached += int(m[1])
        total_completion += int(m[2])
        
    print(f"Number of API requests logged: {len(matches)}")
    print(f"Total prompt tokens: {total_prompt}")
    print(f"Total cached prompt tokens: {total_cached}")
    print(f"Total uncached prompt tokens: {total_prompt - total_cached}")
    print(f"Total completion tokens: {total_completion}")
    
    # Let's inspect the models used
    # Models are sent in payloads, e.g. "model": "deepseek-v4-flash"
    models_found = set(re.findall(r'"model":\s*"([^"]+)"', text))
    print(f"Models found in logs: {models_found}")
    
    # Calculate costs.
    # Prices (DeepSeek API):
    # deepseek-v4-flash / deepseek-chat (V3 / Flash is the same pricing or similar):
    # Input (uncached): $0.075 / 1M tokens
    # Input (cached): $0.015 / 1M tokens
    # Output: $0.30 / 1M tokens
    
    uncached = total_prompt - total_cached
    cost_cached = total_cached * 0.015 / 1e6
    cost_uncached = uncached * 0.075 / 1e6
    cost_completion = total_completion * 0.30 / 1e6
    total_cost = cost_cached + cost_uncached + cost_completion
    
    print("\n--- Cost calculation (DeepSeek V4 Flash) ---")
    print(f"Cached Input Cost:   ${cost_cached:.6f} USD")
    print(f"Uncached Input Cost: ${cost_uncached:.6f} USD")
    print(f"Completion Cost:     ${cost_completion:.6f} USD")
    print(f"Total Cost:          ${total_cost:.4f} USD")
    
    # Let's also calculate if billed as R1 (Reasoner):
    # Prices:
    # - Input (cached): $0.14 / 1M
    # - Input (uncached): $0.55 / 1M
    # - Output: $2.19 / 1M
    cost_r1_cached = total_cached * 0.14 / 1e6
    cost_r1_uncached = uncached * 0.55 / 1e6
    cost_r1_completion = total_completion * 2.19 / 1e6
    total_r1_cost = cost_r1_cached + cost_r1_uncached + cost_r1_completion
    
    print("\n--- Cost calculation (If DeepSeek R1/Reasoner was used) ---")
    print(f"Cached Input Cost:   ${cost_r1_cached:.6f} USD")
    print(f"Uncached Input Cost: ${cost_r1_uncached:.6f} USD")
    print(f"Completion Cost:     ${cost_r1_completion:.6f} USD")
    print(f"Total Cost:          ${total_r1_cost:.4f} USD")

if __name__ == '__main__':
    main()
