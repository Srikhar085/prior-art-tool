"""Configuration loaded from environment variables (see .env.example)."""
import os

from dotenv import load_dotenv

load_dotenv()

PATENTSVIEW_API_KEY = os.getenv("PATENTSVIEW_API_KEY", "").strip()
EPO_OPS_KEY = os.getenv("EPO_OPS_KEY", "").strip()
EPO_OPS_SECRET = os.getenv("EPO_OPS_SECRET", "").strip()
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()

# How many results to request from each source.
RESULTS_PER_SOURCE = 15
