import os, sys, time
import torch
import librosa
from transformers import AutoProcessor, AutoModelForMultimodalLM

print("Loading Gemma 4 E2B model...")
MODEL_ID = "google/gemma-4-E2B-it"

t0 = time.time()
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForMultimodalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
print(f"Loaded in {time.time()-t0:.1f}s")

# Take the first 30 seconds of the test audio
TEST_OGG = "/root/talk/test_compare/19-00-27-04-2026.ogg"
print(f"Loading first 30 seconds of {TEST_OGG}...")
audio_chunk, sr = librosa.load(TEST_OGG, sr=16000, mono=True, duration=30.0)

prompt_text = "Transcribe the following speech segment in Russian into Russian text."

messages = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": audio_chunk},
            {"type": "text", "text": prompt_text},
        ],
    }
]

print("Applying chat template...")
inputs = processor.apply_chat_template(
    messages, tokenize=True, return_dict=True,
    return_tensors="pt", add_generation_prompt=True,
).to(model.device)

input_len = inputs["input_ids"].shape[-1]
print(f"Input tokens: {input_len}")

print("Generating (this is where it hung last time)...")
t_gen = time.time()
with torch.no_grad():
    # Adding parameters to prevent infinite generation loops
    outputs = model.generate(
        **inputs, 
        max_new_tokens=200,      # limit output tokens
        repetition_penalty=1.2,  # prevent repeating loops
        do_sample=False          # greedy decoding for stability
    )

print(f"Generation took {time.time()-t_gen:.1f}s")
print(f"Output tokens: {outputs.shape[-1] - input_len}")

response = processor.decode(outputs[0][input_len:], skip_special_tokens=True)
print("\n=== GEMMA 4 OUTPUT ===")
print(response)
print("======================\n")
