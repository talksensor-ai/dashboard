import re

def calculate():
    prompt_total = 0
    cached_total = 0
    completion_total = 0
    # On the Mac Mini, we'll read `/Users/ai/talk/pipeline/run_21.log`
    # Let's write a script that reads from stdin or from a specified path
    import sys
    log_path = sys.argv[1] if len(sys.argv) > 1 else 'run_21.log'
    
    pattern = re.compile(r'\[TOKENS\] prompt=(\d+)\s+\(cached=(\d+)\)\s+completion=(\d+)')
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                prompt_total += int(m.group(1))
                cached_total += int(m.group(2))
                completion_total += int(m.group(3))
                
    print(f"Total prompt tokens: {prompt_total}")
    print(f"Total cached prompt tokens: {cached_total}")
    print(f"Total completion tokens: {completion_total}")
    
    # Calculate costs for DeepSeek APIs
    # Prices (DeepSeek API):
    # DeepSeek V3 (Chat/Coder):
    # - Input (cached): $0.055 / 1M tokens
    # - Input (uncached): $0.14 / 1M tokens
    # - Output: $0.28 / 1M tokens
    # DeepSeek R1 (Reasoner):
    # - Input (cached): $0.14 / 1M tokens
    # - Input (uncached): $0.55 / 1M tokens
    # - Output: $2.19 / 1M tokens
    
    uncached_total = prompt_total - cached_total
    
    cost_v3 = (cached_total * 0.055 + uncached_total * 0.14 + completion_total * 0.28) / 1000000
    cost_r1 = (cached_total * 0.14 + uncached_total * 0.55 + completion_total * 2.19) / 1000000
    
    print(f"\n--- Cost estimation ---")
    print(f"If billed as DeepSeek-V3:")
    print(f"  Cached input cost:  ${cached_total * 0.055 / 1e6:.6f}")
    print(f"  Uncached input cost:${uncached_total * 0.14 / 1e6:.6f}")
    print(f"  Completion cost:    ${completion_total * 0.28 / 1e6:.6f}")
    print(f"  Total Cost:         ${cost_v3:.4f} USD")
    print(f"If billed as DeepSeek-R1 (Reasoner):")
    print(f"  Cached input cost:  ${cached_total * 0.14 / 1e6:.6f}")
    print(f"  Uncached input cost:${uncached_total * 0.55 / 1e6:.6f}")
    print(f"  Completion cost:    ${completion_total * 2.19 / 1e6:.6f}")
    print(f"  Total Cost:         ${cost_r1:.4f} USD")

if __name__ == "__main__":
    calculate()
