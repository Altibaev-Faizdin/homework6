import os
import logging

import requests
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.serializers import OauthSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class GoogleLoginAPIView(CreateAPIView):
    serializer_class = OauthSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]

        token_response = requests.post(
            url="https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI"),
                "grant_type": "authorization_code",
            },
        )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return Response({"error": "Invalid access_token!"})

        user_info = requests.get(
            url="https://www.googleapis.com/oauth2/v3/userinfo",
            params={"alt": "json"},
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()

        email = user_info.get("email")
        if not email:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Could not retrieve email from Google."},
            )

        given_name = user_info.get("given_name", "")
        family_name = user_info.get("family_name", "")

        user, created = User.objects.get_or_create(email=email)
        logger.info("Google OAuth login: user %s (created=%s)", email, created)

        user.is_active = True
        user.first_name = given_name
        user.last_name = family_name
        user.last_login = timezone.now()
        user.registration_source = "google"
        user.save(update_fields=["is_active", "first_name", "last_name", "last_login", "registration_source"])

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["birthdate"] = user.birthdate.isoformat() if user.birthdate else None

        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        })
