from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a user, used for /auth/me/ and in auth
    responses. Note what is NOT here: password (obviously), but also
    is_staff/is_superuser, which are internal and should never be exposed
    to a client that has no business acting on them.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "created_at",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles account creation.

    Two deliberate choices:

    1. `password` is write_only. Serializers are used for output as well as
       input, so forgetting this is a classic way to leak a password hash
       into an API response.

    2. `role` is accepted here and ONLY here. It is in UserSerializer's
       read_only_fields, so no profile-update endpoint can ever change it.
       Role is set once at registration; a seeker cannot promote themselves
       to employer by PATCHing their own record. This is the difference
       between "we have roles" and "our roles are actually enforceable".

    No custom `validate_role` here (an earlier version had one, rejecting
    anything outside seeker/employer): ModelSerializer auto-builds `role`
    as a ChoiceField because User.role has `choices=` at the model level,
    and ChoiceField already rejects an invalid value before any custom
    field validator would run. A hand-written check duplicating that is
    dead code, confirmed by testing it directly against the serializer --
    worth stating explicitly so nobody re-adds it assuming it's needed.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
        ]

    def validate_email(self, value):
        # Lowercase before the uniqueness check so "Alice@x.com" cannot
        # slip past a DB unique constraint that already holds "alice@x.com".
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Runs Django's AUTH_PASSWORD_VALIDATORS (length, common passwords,
        # numeric-only, similarity to user attributes). Reusing these rather
        # than inventing our own password rules means one source of truth.
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        # Goes through the manager so the password is hashed, never stored raw.
        return User.objects.create_user(**validated_data)


class JobTrackTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends SimpleJWT's login serializer in two ways.

    1. Embeds `role` and `email` as claims in the access token, so the React
       app can render role-appropriate navigation immediately on login
       without an extra round trip.

       IMPORTANT: these claims are a UX convenience only. The backend never
       authorizes based on the token's role claim -- permissions re-read
       request.user.role from the database. A JWT payload is signed, so it
       cannot be tampered with, but it CAN go stale (e.g. account
       deactivated seconds after the token was issued). Authorization must
       reflect current state, not state at login time.

    2. Returns the serialized user alongside the tokens, so the frontend
       does not have to immediately call /auth/me/ after logging in.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
