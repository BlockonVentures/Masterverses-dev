from user_app.models import User, Tasks, Cards, CardsDetails
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

# Serializer: AdminLogin
# ---------------------------------------------------------------------------------------------
class AdminLoginSerializer(serializers.Serializer):
    """
    Serializer for admin login.

    Validates telegram_id and password, and ensures the user has admin privileges.
    """
    telegram_id = serializers.IntegerField()
    password = serializers.CharField()

    class Meta:
        fields = ["telegram_id", "password"]

    def validate(self, attrs):
        """
        Validates the provided credentials and checks if the user is an admin.

        Args:
            attrs (dict): Serialized input data containing telegram_id and password.

        Returns:
            User: Authenticated user object if validation passes.

        Raises:
            serializers.ValidationError: If credentials are invalid or the user is not an admin.
        """
        telegram_id = attrs.get("telegram_id")
        password = attrs.get("password")
        user = authenticate(telegram_id=telegram_id, password=password)
        if not user or not user.is_staff:
            raise serializers.ValidationError("Sorry, you are not an admin.")
        return user
    
# -----------------------------------------------------------------------------------
class AdminUpdatePointsSerializer(serializers.Serializer):
    """
    Serializer for updating user points by an admin.

    Allows updating points based on either telegram_id or username.
    """
    telegram_id = serializers.IntegerField(write_only=True, required=False)
    username = serializers.CharField(write_only=True, required=False)
    points = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        fields = ["telegram_id", "points"]

    def validate(self, attrs):
        """
        Ensures that either telegram_id or username is provided and validates their existence.

        Args:
            attrs (dict): Serialized input data.

        Returns:
            dict: Validated attributes.

        Raises:
            serializers.ValidationError: If neither telegram_id nor username is provided or user is not found.
        """
        telegram_id = attrs.get("telegram_id")
        username = attrs.get("username")

        if not telegram_id and not username:
            raise serializers.ValidationError("Either telegram_id or username must be provided.")
        
        # Check if the user exists based on provided identifier
        if telegram_id:
            user = get_object_or_404(User, telegram_id=telegram_id)
        else:
            user = get_object_or_404(User, username=username)
        
        return attrs
    
# Serializer: Task
# ---------------------------------------------------------------------------------------------
class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for managing tasks.
    
    Serializes all fields of the Tasks model.
    """
    class Meta:
        model = Tasks
        fields = "__all__"

# Serializer: Card
# ---------------------------------------------------------------------------------------------
class CardSerializer(serializers.ModelSerializer):
    """
    Serializer for managing cards.
    
    Serializes all fields of the Cards model.
    """
    class Meta:
        model = Cards
        fields = "__all__"

# Serializer: CardDetails
# ---------------------------------------------------------------------------------------------
class CardDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for managing card details.
    
    Serializes all fields of the CardsDetails model.
    """
    
    class Meta:
        model = CardsDetails
        fields = "__all__"