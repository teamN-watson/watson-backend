from django.shortcuts import render
from rest_framework.decorators import api_view

from .serializers import AccountSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response


# Create your views here.
@api_view(["POST"])
def signup(request):
    serializer = AccountSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response(
            {"message": "회원가입 되었습니다.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )
