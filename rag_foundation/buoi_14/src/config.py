import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Valid Roles configuration for RBAC (Buổi 15)
ROLES = ["Admin", "HR_Manager", "Risk_Officer", "Employee", "Guest"]
VALID_ROLES = set(ROLES)

# Role hierarchy / permissions mapping
ROLE_PERMISSIONS = {
    "Admin": ["Admin", "HR_Manager", "Risk_Officer", "Employee", "Guest"],
    "HR_Manager": ["HR_Manager", "Employee", "Guest"],
    "Risk_Officer": ["Risk_Officer", "Employee", "Guest"],
    "Employee": ["Employee", "Guest"],
    "Guest": ["Guest"]
}

# Neo4j Database Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def get_neo4j_config():
    return {
        "uri": NEO4J_URI,
        "user": NEO4J_USER,
        "password": NEO4J_PASSWORD,
        "database": NEO4J_DATABASE
    }

if __name__ == "__main__":
    print(f"Loaded config from: {ENV_PATH}")
    print(f"Valid Roles: {ROLES}")
    print(f"Neo4j URI: {NEO4J_URI}")
