"""Opaque, signed bearer-token authentication backed by revocable sessions."""

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.services import authenticate_access_token


class SignedBearerAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid bearer authorization header.")
        try:
            token = parts[1].decode("ascii")
        except UnicodeDecodeError as exc:
            raise AuthenticationFailed("Invalid bearer token.") from exc

        result = authenticate_access_token(token)
        if result is None:
            raise AuthenticationFailed("Access token is invalid, expired, or revoked.")
        user, claims = result
        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
