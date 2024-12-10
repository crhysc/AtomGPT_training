import json
import transformers
import torch
import os
import zipfile
from jarvis.io.vasp.inputs import Poscar
from pydantic_settings import BaseSettings
from typing import Optional

class TrainingPropConfig(BaseSettings):
    """Training config defaults and validation."""

    id_prop_path: Optional[str] = "robo_desc.json.zip"
    prefix: str = "atomgpt_run"
    model_name: str = "gpt2"
    batch_size: int = 16
    max_length: int = 512
    num_epochs: int = 500
    latent_dim: int = 1024
    learning_rate: float = 1e-3
    test_each_run: bool = True
    include_struct: bool = False
    pretrained_path: str = ""
    seed_val: int = 42
    n_train: Optional[int] = None
    n_val: Optional[int] = None
    n_test: Optional[int] = None
    output_dir: str = "out_temp"
    train_ratio: Optional[float] = None
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    keep_data_order: bool = True
    desc_type: str = "desc_2"  # Added this line
    convert: bool = False

# Load the configuration file
config_file_path = "config.json"
with open(config_file_path, "r") as f:
    config_data = json.load(f)

config = TrainingPropConfig(**config_data)
print(config)

# Let's load the model first
model_name = config.model_name
output_dir = config.output_dir
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if "t5" in model_name:
    model = transformers.T5ForConditionalGeneration.from_pretrained(
        model_name
    )
else:
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_name,
        low_cpu_mem_usage=True,
    )

tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({"pad_token": "[PAD]"})
    model.resize_token_embeddings(len(tokenizer))
model.lm_head = torch.nn.Sequential(
    torch.nn.Linear(model.config.hidden_size, config.latent_dim),
    torch.nn.Linear(config.latent_dim, 1),
)
# Handle the DataParallel prefix in the state_dict
state_dict = torch.load(os.path.join(output_dir, "best_model.pt"), map_location=device)
# Remove 'module.' prefix from the keys
new_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

model.load_state_dict(new_state_dict)

# Get description
pos = """Mo2S4
1.0
1.5957990235943282 -2.764004284915705 0.0
1.5957990235946695 2.7640042849149173 0.0
0.0 0.0 12.47890117404454
Mo S
2 4
Cartesian
1.5958 -0.9213351759999822 3.119725
1.5958 0.9213351759999822 9.359175
1.5958 0.9213351759999822 1.553025569564048
1.5958 -0.9213351759999822 7.792475569561349
1.5958 0.9213351759999822 4.686424430434634
1.5958 -0.9213351759999822 10.92587443043865
"""

atoms = Poscar.from_string(pos).atoms
print("Inputted POSCAR:")
print(atoms)
desc = atoms.describe()[config.desc_type]
desc = atoms.describe()['desc_2']

#print(desc)

# Predict property
max_length=512
input_ids = tokenizer(
    [pos],
    return_tensors="pt",
    max_length=max_length,
    padding="max_length",
    truncation=True,
)['input_ids']


input_ids=input_ids.to(device)
model=model.to(device)

if "t5" in model_name:
    predictions = (
        model(
            input_ids,
            decoder_input_ids=input_ids,
        )
        .logits.squeeze()
        .mean(dim=-1)
    )
else:
    predictions = (
        model(
            input_ids.to(device),
        )
        .logits.squeeze()
        .mean(dim=-1)
    )

predictions = predictions.cpu().detach().numpy().tolist()
print("Predicted bandgap energy:")
print(predictions)
