from ninja import Router
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from ninja.errors import HttpError

router = Router(tags=["health"])
auth = JWTAuthentication()

@router.get("/health")
def health(request):
    return {"status": "ok"}

@router.get("/health-protected")
def health_protected(request):
    user_auth = auth.authenticate(request)
    if not user_auth or isinstance(user_auth[0], AnonymousUser):
        raise HttpError(401, "Unauthorized")
    return {"status": "ok", "user": user_auth[0].username}