import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app
from backend.config import Config
from backend.seed import seed_database

app = create_app()


@app.cli.command("seed-admin")
def seed_admin_command():
    seed_database()
    print("Seed completed: admin@example.com / Admin@12345")


if __name__ == "__main__":
    print(f"GEMS AI Assistant running on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
