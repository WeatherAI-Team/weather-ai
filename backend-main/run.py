from app import create_app
from app.api.kakao_auth_api import kakao_auth_bp

app = create_app()

app.register_blueprint(kakao_auth_bp)
app.secret_key = "your-secret-key"

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)