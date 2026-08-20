import os

# Required settings that have no default; tests never talk to real infra.
os.environ.setdefault("PUBLIC_BASE_URL", "http://localhost:5173")
