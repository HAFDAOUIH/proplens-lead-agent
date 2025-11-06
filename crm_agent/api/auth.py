from ninja import Router, Schema
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Dict

router = Router(tags=["auth"])

class LoginIn(Schema):
    username: str
    password: str

class TokenOut(Schema):
    access: str

class ErrorOut(Schema):
    detail: str

@router.post("/login", response={200: TokenOut, 401: ErrorOut})
def login(request, payload: LoginIn):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        return 401, {"detail": "Invalid credentials"}
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token)}