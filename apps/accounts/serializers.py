from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Company, UserProfile

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role_title', 'phone', 'company']
