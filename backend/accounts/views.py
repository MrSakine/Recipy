from django.http import Http404
from rest_framework import status as st
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from accounts.models import User, UserProfile
from accounts.serializers import UserSerializer, UserProfileSerializer


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
            "email": user_instance.email
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
def update_password(request: Request, id: str):
    pass

@api_view(["PUT"])
def update_picture(request: Request, id: str):
    pass


@api_view(["DELETE"])
def delete_user(request: Request, id: str):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404("User does not exist")
    user.delete()
    return Response({"message": "ok"})
