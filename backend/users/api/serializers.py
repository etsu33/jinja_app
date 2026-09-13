from datetime import date
from typing import Optional

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers
from users.models import UserProfile

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # email は Signup の必須項目。
    # Django 標準 User.email は blank=True のため、ModelSerializer の自動生成に任せると
    # required=False / allow_blank=True になり、空文字や未送信を受け入れてしまう。
    # Backend を validation の正本とするため、ここで明示的に上書きする。
    email = serializers.EmailField(required=True, allow_blank=False, allow_null=False)

    class Meta:
        model = User
        fields = ("username", "password", "email")

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data["email"],
        )


class UserProfileSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(read_only=True)
    icon_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        # 必要なフィールドを一つに統合（必要に応じて created_at を残す/外す）
        fields = (
            "nickname", "is_public", "bio", "icon", "icon_url",
            "birthday", "birth_time", "birth_place", "created_at",
        )
        read_only_fields = ("icon", "icon_url", "created_at")

    @extend_schema_field(OpenApiTypes.URI)
    def get_icon_url(self, obj) -> Optional[str]:  # ← 引数の型注釈は外すのが安定
        request = self.context.get("request")
        try:
            if obj.icon and obj.icon.name:
                url = obj.icon.url
                return request.build_absolute_uri(url) if request else url
        except Exception:
            pass
        return None


class UserMeSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "profile")


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "nickname", "is_public", "bio", "icon",
            "birthday", "birth_time", "birth_place",
        )

    def validate_birthday(self, value):
        if value is not None and value > date.today():
            raise serializers.ValidationError("生年月日に未来の日付は指定できません。")
        return value
