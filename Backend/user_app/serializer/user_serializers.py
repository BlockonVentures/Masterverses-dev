from user_app.models import User, UserCardClaim, CardsDetails
from rest_framework import serializers
from django.contrib.auth import authenticate

# Serializer: LoginSerializer
# ---------------------------------------------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login or creation.
    It validates and deserializes the user data for login and user creation.
    
    Attributes:
        telegram_id (int): The user's unique Telegram ID.
        username (str, optional): The user's username, not required during login.
        first_name (str, optional): The user's first name, not required during login.
        reffered_by (int, optional): The Telegram ID of the user who referred this user.
    """
    telegram_id = serializers.IntegerField() # Telegram ID (required field)
    username = serializers.CharField(max_length=100, required=False, allow_blank=True) # Optional username
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True) # Optional first name
    reffered_by = serializers.IntegerField(required=False, allow_null=True) # Optional field for the referring user's Telegram ID

    class Meta:
        fields = ["telegram_id", "username", "first_name", "reffered_by"] # Specifies the fields for serialization

    def validate_telegram_id(self, telegram_id):
        """
        Validate the provided Telegram ID. If a user already exists with that ID, 
        it is added to the context for later use.

        Args:
            telegram_id (int): The Telegram ID provided for the user.

        Returns:
            int: The valid Telegram ID.
        """
        try:
            user = User.objects.get(telegram_id=telegram_id) # Try to fetch an existing user by telegram_id
            self.context["user"] = user # If found, add the user to the context
        except User.DoesNotExist:
            pass # If user does not exist, do nothing
        return telegram_id
    
    def create(self, validated_data):
        """
        Create a new user instance using the validated data.
        
        Args:
            validated_data (dict): The data validated by the serializer.

        Returns:
            User: The newly created User instance.
        """
        reffered_by = validated_data.get("reffered_by") # Get the referring user's Telegram ID, if available
        username = validated_data.get("username", "") # Use empty string if username is not provided
        first_name = validated_data.get("first_name", "") # Use empty string if first name is not provided

        # Create a new user with the provided data
        user = User.objects.create(
            telegram_id=validated_data["telegram_id"],
            username=username,
            first_name=first_name,
            reffer_id=validated_data["telegram_id"], # The user’s own ID is used as reffered_by during creation
            reffered_by=reffered_by, # Assign the referring user’s ID, if available
        )
        self.context["user"] = user # Store the newly created user in the context
        return user
    
# Serializer: UserCardDetails
# -------------------------------------------------------------------------------------
class UserCardDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for user card details. It fetches information about the user’s cards 
    and the associated points.
    
    Attributes:
        name (str): The name of the card.
        automine_points (int): The automine points associated with the card.
    """
    name = serializers.CharField(source="card.name") # Get the card's name from the related Card model
    automine_points = serializers.SerializerMethodField() # Custom field to fetch automine points
    class Meta:
        model = UserCardClaim
        fields = ["name", "card_level", "date_claimed", "automine_points"]

    def get_automine_points(self, obj):
        """
        Get the automine points associated with the card and card level.

        Args:
            obj (UserCardClaim): The UserCardClaim instance being serialized.

        Returns:
            int: The automine points for the card at the given level.
        """
        # Try to get the CardsDetails entry for the card and level
        card_details = CardsDetails.objects.filter(card=obj.card, level_number=obj.card_level).first()
        
        # If no matching CardsDetails found, return None
        if card_details is None:
            return None
        
        return card_details.automine_points
    
# Serializer: UserDetails
# ---------------------------------------------------------------------------------------------
class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for user details, including the user's balance, level, bonus status,
    and card details.
    
    Attributes:
        user_cards (list): A list of user card details.
    """
    user_cards = UserCardDetailsSerializer(many=True) # Nested serializer for user cards
    class Meta:
        model = User
        fields = ["balance", "level_number", "level_name", "welcome_bonus", "multitap_level", "recharging_speed_level", "autobot_status", "user_cards", "user_religion"]

# Serializer: WelcomeBonus
# -----------------------------------------------------------------------------------
class WelcomeBonusSerializer(serializers.ModelSerializer):
    """
    Serializer to handle the user's welcome bonus status and balance update.
    
    Attributes:
        balance (int): The user's current balance.
        welcome_bonus (bool): The status of the user's welcome bonus.
    """
    class Meta:
        model = User
        fields = ["balance", "welcome_bonus"]
    
    def validate(self, attrs):
        """
        Validate if the user has already claimed the welcome bonus. If claimed, 
        raise a validation error.

        Args:
            attrs (dict): The validated data.

        Returns:
            dict: The validated data, if no errors.
        
        Raises:
            serializers.ValidationError: If the welcome bonus has already been claimed.
        """
        user = self.context["request"].user # Get the authenticated user from the request context
        if user.welcome_bonus:
            raise serializers.ValidationError("Welcome Bonus already claimed.") # Raise error if bonus is already claimed
        return attrs
    
class UpdateReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_religion"]
