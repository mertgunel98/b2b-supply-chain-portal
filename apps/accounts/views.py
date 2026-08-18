from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Company, UserProfile
from .serializers import CompanySerializer, UserProfileSerializer
from apps.scoring.models import ScoringConfiguration

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['get'])
    def suppliers(self, request):
        suppliers = Company.objects.filter(company_type='SUPPLIER')
        serializer = self.get_serializer(suppliers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def smes(self, request):
        smes = Company.objects.filter(company_type='SME')
        serializer = self.get_serializer(smes, many=True)
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Registers a new User and their Company (Buyer SME or Supplier).
    """
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role_type = data.get('role_type', 'SME') # 'SME' or 'SUPPLIER'
    company_name = data.get('company_name')
    contact_person = data.get('contact_person', username)
    phone = data.get('phone', '')
    tax_id = data.get('tax_id', '')

    if not username or not password or not company_name:
        return Response({'error': 'Username, password, and company name are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Create User
    user = User.objects.create_user(username=username, email=email, password=password)

    # 2. Create Company
    company = Company.objects.create(
        name=company_name,
        company_type=role_type,
        contact_person=contact_person,
        email=email,
        phone=phone,
        tax_id=tax_id
    )

    # 3. If SME, create default scoring config
    if role_type == 'SME':
        ScoringConfiguration.objects.get_or_create(
            sme_company=company,
            defaults={'w1_timeliness': 0.40, 'w2_completeness': 0.35, 'w3_price_consistency': 0.25}
        )

    # 4. Create UserProfile
    profile = UserProfile.objects.create(
        user=user,
        company=company,
        role_title="Procurement Officer" if role_type == 'SME' else "Sales & Operations Manager",
        phone=phone
    )

    login(request, user)

    return Response({
        'message': 'Registration successful.',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'company': CompanySerializer(company).data,
            'role_title': profile.role_title
        }
    }, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Authenticates user and returns company profile & role.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

    login(request, user)

    # Fetch profile
    profile = getattr(user, 'profile', None)
    company_data = CompanySerializer(profile.company).data if profile else None

    return Response({
        'message': 'Login successful.',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'company': company_data,
            'role_title': profile.role_title if profile else 'Administrator'
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_current_user(request):
    """
    Returns current authenticated user session data.
    """
    if not request.user.is_authenticated:
        return Response({'authenticated': False})

    profile = getattr(request.user, 'profile', None)
    company_data = CompanySerializer(profile.company).data if profile else None

    return Response({
        'authenticated': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'company': company_data,
            'role_title': profile.role_title if profile else 'Administrator'
        }
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_user(request):
    logout(request)
    return Response({'message': 'Logged out successfully.'})
