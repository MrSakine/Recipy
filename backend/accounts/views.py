from django.http import Http404
from rest_framework import status as st
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.request import Request
from accounts.models import User, UserProfile
from accounts.serializers import (
    UserSerializer,
    UserProfileSerializer,
    LoginSerializer,
    RefreshTokenSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["GET"])
def status(request: Request):
    return Response(data={"status": "Working"})


@api_view(["POST"])
def signup(request: Request):
    user_serializer = UserSerializer(data=request.data)
    profile_serializer = UserProfileSerializer(data=request.data)

    valid_user_data = user_serializer.is_valid()
    valid_profile_data = profile_serializer.is_valid()

    if valid_user_data and valid_profile_data:
        user_instance = user_serializer.save()
        profile_serializer.save(user=user_instance)
        response_data = {
            "id": user_instance.id,
            "username": user_instance.username,
            "email": user_instance.email,
            "profile": profile_serializer.data
        }
        return Response(response_data, status=st.HTTP_201_CREATED)
    else:
        errors = {}
        if user_serializer.errors:
            errors.update(user_serializer.errors)
        if profile_serializer.errors:
            errors.update(profile_serializer.errors)
        return Response(errors, status=st.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@parser_classes([JSONParser])
def update_data(request, id: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404("User does not exist")

    data = {
        "first_name": request.data.get("first_name"),
        "last_name": request.data.get("last_name"),
        "username": request.data.get("username")
    }

    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)

    user.save()
    return Response({"message": "ok"})


@api_view(["PUT"])
@parser_classes([JSONParser])
def update_email(request: Request, id: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404("User does not exist")

    data = {
        "email": request.data.get("email")
    }

    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)

    user.save()
    return Response({"message": "ok"})


@api_view(["PUT"])
@parser_classes([JSONParser])
def update_password(request: Request, id: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404("User does not exist")

    data = {
        "password0": request.data.get("password0"),
        "password1": request.data.get("password1")
    }

    if not user.check_password(data.get("password0")):
        return Response({"error": "Old password is invalid"}, status=st.HTTP_400_BAD_REQUEST)
    elif not data.get("password1"):
        return Response({"error": "New password cannot be empty"}, status=st.HTTP_400_BAD_REQUEST)
    elif data.get("password0") == data.get("password1"):
        return Response({"error": "Password are the same"}, status=st.HTTP_400_BAD_REQUEST)
    else:
        setattr(user, "password", data.get("password1"))
    User.set_password(user, user.password)
    user.save()
    return Response({"message": "ok"})


@api_view(["PUT"])
@parser_classes([MultiPartParser])
def update_picture(request: Request, id: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404("User does not exist")

    profile_serializer = UserProfileSerializer(data=request.data)
    valid_profile_data = profile_serializer.is_valid()
    if valid_profile_data:
        user_profile = UserProfile.objects.filter(user=user).get()
        if user_profile.picture:
            user_profile.picture.delete()
        user_profile.picture = request.data.get("picture")
        user_profile.save()
        return Response({"message": "ok"})
    else:
        errors = {}
        if profile_serializer.errors:
            errors.update(profile_serializer.errors)
        return Response(errors, status=st.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_user(request: Request, id: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404("User does not exist")
    user.delete()
    return Response({"message": "ok"})


@api_view(["POST"])
@parser_classes([JSONParser])
def login(request: Request):
    """
    Login a user from email/username and password through jwt tokens
    Read more about jwt tokens here:
    https://django-rest-framework-simplejwt.readthedocs.io/en/latest/
    """
    login_serializer = LoginSerializer(data=request.data)
    valid = login_serializer.is_valid()
    user = None
    if valid:
        user = User.objects.filter(
            email=login_serializer.data.get("username")).first()
        if not user:
            user = User.objects.filter(
                username=login_serializer.data.get("username")).first()
        if user is not None and user.check_password(login_serializer.data.get("password")):
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "ok",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            )
        else:
            errors = {"detail": "Invalid credentials"}
            return Response(errors, status=st.HTTP_400_BAD_REQUEST)
    else:
        errors = {}
        if login_serializer.errors:
            errors.update(login_serializer.errors)
        return Response(errors, status=st.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def refresh_token(request: Request):
    refresh_token_serializer = RefreshTokenSerializer(data=request.data)
    valid = refresh_token_serializer.is_valid()
    if valid:
        try:
            refresh = refresh_token_serializer.validated_data.get("refresh")
            refresh_token = RefreshToken(refresh)
            RefreshToken.verify(refresh_token)
        except Exception as e:
            return Response({"error": str(e)}, status=st.HTTP_403_FORBIDDEN)
        return Response({"token": str(refresh_token.access_token)})
    else:
        errors = {}
        if refresh_token_serializer.errors:
            errors.update(refresh_token_serializer.errors)
        return Response(errors, status=st.HTTP_400_BAD_REQUEST)
