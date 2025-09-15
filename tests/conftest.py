import os
import sys

# Garantir ambiente de testes previsível
os.environ.setdefault("APP_ENV", "test")
# Evita chamadas externas à Meta durante testes
os.environ.setdefault("WA_PROVIDER", "noop")

# Ensure the project root (which contains the 'app' package) is on sys.path
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
