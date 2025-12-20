#!/usr/bin/env python3
from datetime import datetime, timedelta
from uuid import uuid4

from jose import jws

# Читаем приватный ключ
with open(".dev/secrets/jwt/signing_key", "r") as f:
    signing_key = f.read()

# Создаем claims для токена
claims = {
    "sub": str(uuid4()),  # user_id
    "sid": str(uuid4()),  # session_id
    "email": "viewer@example.com",
    "first_name": "Test",
    "last_name": "Viewer",
    "role": "viewer",
    "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
    "iat": int(datetime.utcnow().timestamp()),
}

# Генерируем токен
token = jws.sign(claims, signing_key, algorithm="ES256")

print("Generated JWT Token:")
print(token)
print("\nClaims:")
for key, value in claims.items():
    print(f"  {key}: {value}")
