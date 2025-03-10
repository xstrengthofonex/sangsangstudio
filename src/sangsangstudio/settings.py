import os

from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
DOT_ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=DOT_ENV_PATH)
