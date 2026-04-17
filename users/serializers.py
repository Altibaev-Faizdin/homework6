from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

CustomUser = get_user_model()


class OauthSerializer(serializers.Serializer):
    code = serializers.CharField()


class CustomJWTSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["last_login"] = str(user.last_login) if user.last_login else None
        token["is_staff"] = user.is_staff
        token["call_me"] = "+996777777777"
        token["birthdate"] = user.birthdate.isoformat() if user.birthdate else None
        return token


class UserBaseSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=150)
    password = serializers.CharField()


class AuthValidateSerializer(UserBaseSerializer):
    pass


class RegisterValidateSerializer(UserBaseSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def validate_email(self, email):
        try:
            CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return email
        raise ValidationError("CustomUser уже существует!")


class ConfirmationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        try:
            CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise ValidationError("CustomUser не существует!")
        return attrs
