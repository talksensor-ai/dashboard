import gigaam
import torch

device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Loading model...")
model = gigaam.load_model('v3_e2e_rnnt', device=device)
print("Type of model:", type(model))
print("Dir of model:", dir(model))
