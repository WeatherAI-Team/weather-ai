import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

app = create_app()
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
