import os

SECRET_KEY = os.getenv("SECRET_KEY", "hima-chababi-secret-change-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hima.db")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours
ALGORITHM = "HS256"
