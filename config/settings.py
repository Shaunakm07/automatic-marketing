import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY        = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_MODEL          = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Optional — only required by the LinkedIn posting pipeline
LINKEDIN_ACCESS_TOKEN    = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN      = os.getenv("LINKEDIN_PERSON_URN", "")
LINKEDIN_API_BASE        = "https://api.linkedin.com/v2"

# Optional — only required by the video pipeline
HIGGSFIELD_API_KEY       = os.getenv("HIGGSFIELD_API_KEY", "")
HIGGSFIELD_API_URL       = os.getenv("HIGGSFIELD_API_URL", "https://api.higgsfield.ai/v1")

SUPABASE_URL             = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

GITHUB_TOKEN             = os.environ["GITHUB_TOKEN"]
BRAIN_LLM_REPO           = os.getenv("BRAIN_LLM_REPO", "Shaunakm07/Brain-LLM-Fine-Tuning")

DRY_RUN                  = os.getenv("DRY_RUN", "false").lower() == "true"
LOG_LEVEL                = os.getenv("LOG_LEVEL", "INFO")
