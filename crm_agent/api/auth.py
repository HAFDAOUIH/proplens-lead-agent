from ninja import Router, Schema
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

router = Router(tags=["auth"])

class LoginIn(Schema):
    username: str
    password: str

@router.post("/login")
def login(request, payload: LoginIn):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        return 401, {"detail": "Invalid credentials"}
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token)}