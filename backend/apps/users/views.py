from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    JobTrackTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(CreateAPIView):
    """
    POST /api/auth/register/

    AllowAny is required here: by definition the caller has no account yet.
    This is one of only three unauthenticated endpoints in the whole API
    (register, login, refresh), which is worth being able to point at --
    "everything else requires a token" is a much easier security story to
    defend than a scattered mix of permissions.

    Returns tokens immediately so the user is logged in after registering,
    rather than forcing a second login round trip.
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    # Scoped to the "auth" rate (10/min per IP, see REST_FRAMEWORK settings)
    # -- registration abuse (mass account creation) is the risk here.
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["email"] = user.email

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/

    Thin wrapper over SimpleJWT's view, swapped to our serializer so the
    response includes the user object and the tokens carry role/email claims.
    """

    serializer_class = JobTrackTokenObtainPairSerializer
    permission_classes = [AllowAny]
    # Scoped to the "auth" rate -- this is the actual credential-stuffing
    # surface, the reason this throttle exists at all.
    throttle_scope = "auth"


class LogoutView(APIView):
    """
    POST /api/auth/logout/  body: {"refresh": "<token>"}

    What logout can and cannot do with JWTs, stated honestly:

    - The REFRESH token is blacklisted here, so it can never be exchanged
      for a new access token again. This is real, server-side revocation.
    - The ACCESS token is NOT revoked. It stays valid until it expires
      (15 minutes, per SIMPLE_JWT settings). This is inherent to stateless
      JWTs -- verifying an access token deliberately involves no database
      lookup, which is the entire performance argument for using them.

    The mitigation is the short access-token lifetime. If instant revocation
    ever became a hard requirement (e.g. compromised-account response), the
    options are: shorten the lifetime further, or add a denylist check to
    authentication -- which trades away the statelessness we chose JWTs for.

    Returns 205 Reset Content: the standard "your request succeeded, now
    clear your view state" response, which is precisely what the client
    should do with its stored tokens.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer("LogoutRequest", {"refresh": serializers.CharField()}),
        responses={205: None, 400: None},
        description="Blacklists the given refresh token. The access token remains valid "
        "until it naturally expires (see the class docstring for why).",
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            # Covers malformed, expired, and already-blacklisted tokens.
            # We deliberately do not distinguish between these cases in the
            # response -- telling an attacker *why* a token was rejected is
            # free information.
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """
    GET /api/auth/me/

    Returns the authenticated user. The frontend calls this on app load to
    restore session state from a stored token.

    Note there is no profile data here yet -- JobSeekerProfile and
    EmployerProfile do not exist until Phases 3 and 5. This endpoint will be
    extended to nest the profile once those models land, which is why the
    response is shaped as a nested object rather than flat user fields.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer("MeResponse", {"user": UserSerializer()}),
        description="Returns the authenticated user. Called on app load to restore session state.",
    )
    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})
