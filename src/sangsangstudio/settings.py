import os

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
