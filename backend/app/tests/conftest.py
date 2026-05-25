import os


os.environ.setdefault("CHILD_AI_ALLOW_MOCK_RUNTIME", "true")
os.environ.setdefault("CHILD_AI_MODEL_PROVIDER", "mock")
os.environ.setdefault("CHILD_AI_VISION_PROVIDER", "mock")
os.environ.setdefault("CHILD_AI_TTS_PROVIDER", "mock")
os.environ.setdefault("CHILD_AI_ASR_PROVIDER", "mock")
os.environ.setdefault("CHILD_AI_ASR_FALLBACK_PROVIDER", "mimo")
