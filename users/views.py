from accounts.tasks import send_otp_email
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView
from django.core.cache import cache

from .serializers import (
    RegisterValidateSerializer,
    AuthValidateSerializer,
    ConfirmationSerializer,
    CustomJWTSerializer,
)
import random
import string
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView


CustomUser = get_user_model()

_CODE_PREFIX = "confirmation_code:"
_CODE_TTL = 60 * 5


class CustomJWTView(TokenObtainPairView):
    serializer_class = CustomJWTSerializer


class AuthorizationAPIView(CreateAPIView):
    serializer_class = AuthValidateSerializer

    def post(self, request, *args, **kwargs):
        serializer = AuthValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(**serializer.validated_data)

        if user:
            if not user.is_active:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={"error": "CustomUser account is not activated yet!"},
                )

            token, _ = Token.objects.get_or_create(user=user)
            return Response(data={"key": token.key})

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={"error": "CustomUser credentials are wrong!"},
        )


class RegistrationAPIView(CreateAPIView):
    serializer_class = RegisterValidateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        phone_number = serializer.validated_data.get("phone_number", None)

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                is_active=False,
                phone_number=phone_number,
            )

            code = "".join(random.choices(string.digits, k=6))

            cache.set(f"{_CODE_PREFIX}{user.id}", code, timeout=_CODE_TTL)
            send_otp_email.delay(email=email, otp_code=code)

        return Response(
            status=status.HTTP_201_CREATED,
            data={"user_id": user.id, "confirmation_code": code},
        )


class ConfirmUserAPIView(CreateAPIView):
    serializer_class = ConfirmationSerializer

    def post(self, request, *args, **kwargs):
        serializer = ConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        code = serializer.validated_data["code"]

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "CustomUser не существует!"},
            )

        redis_key = f"{_CODE_PREFIX}{user_id}"
        stored_code = cache.get(redis_key)

        if stored_code is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Код подтверждения не найден или истёк!"},
            )

        if stored_code != code:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "Неверный код подтверждения!"},
            )

        with transaction.atomic():
            user.is_active = True
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

            cache.delete(redis_key)

        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "CustomUser аккаунт успешно активирован",
                "key": token.key,
            },
        )
