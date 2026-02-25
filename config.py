import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# RunPod
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")
BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/openai/v1"

# Model
MODEL_NAME = "deepseek-ai/deepseek-r1-distill-qwen-7b"

# Inference defaults
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.6"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "32768"))
N_SAMPLES = int(os.environ.get("N_SAMPLES", "1"))

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
ROLLOUTS_DIR = DATA_DIR / "rollouts"
ROLLOUTS_DIR.mkdir(parents=True, exist_ok=True)
