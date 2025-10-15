import os


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "claude-3-opus-20240229")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


