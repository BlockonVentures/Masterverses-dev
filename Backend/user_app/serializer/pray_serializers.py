from django.utils import timezone
from user_app.models import BoosterClaim, DailyReward, User, Earnings, Tasks, UserDailyReward, UserTaskClaim, Cards, UserCardClaim, CardsDetails
from rest_framework import serializers
from datetime import timedelta
from django.utils.timezone import now

# Serializer: UpdateBalance
# -----------------------------------------------------------------------------------------
class UpdateBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a user's balance.
    
    Fields:
        - level_number: Current level number of the user.
        - level_name: Name of the user's current level.
        - balance: Current balance of the user.
        - amount: Amount to add to the user's balance, validated to be greater than current balance.
    """
    amount = serializers.IntegerField(min_value=1, required=True, write_only=True)

    class Meta:
        model = User
        fields = ["level_number", "level_name", "balance", "amount"]
        read_only_fields = ["level_number", "level_name", "balance", ]

    def validate(self, attrs):
        """
        Ensure that the new balance (amount) is greater than the user's current balance.
        
        Raises:
            ValidationError: If the new balance is not greater than the current balance.
        """
        # Ensure that the updated amount is greater than the current balance
        if self.instance.balance >= attrs.get("amount"):
            raise serializers.ValidationError("Updated amount should be greater than the current balance.")
        
        return attrs

    def update(self, instance, validated_data):
        """
        Update the user's balance.
        
        Args:
            instance: The user instance being updated.
            validated_data: The validated data containing the new amount.

        Returns:
            Updated user instance with the new balance.
        """
        instance.balance = validated_data["amount"]
        instance.save()
        return instance    

# Serializer: UserEarning
# ----------------------------------------------------------------------------------------------
class UserEarningsSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user earnings. Supports both CREDIT and DEBIT transactions.
    """
    class Meta:
        model = Earnings
        fields = ["amount", "transaction_type", "reason"]

    def validate(self, attrs):
        """
        Ensure sufficient balance for DEBIT transactions.
        """
        # get the current user
        user = self.context["request"].user
        if attrs["transaction_type"] == "DEBIT" and user.balance < attrs["amount"]:
            raise serializers.ValidationError("Insufficient Funds")
        return attrs
    
# Serializer: UserRefferalLearderboard
# ----------------------------------------------------------------------------------------------
class UserRefferalLeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer to display user referral leaderboard data.
    """
    rank = serializers.IntegerField()

    class Meta:
        model = User
        fields = ["telegram_id", "username", "first_name", "balance", "rank"]

# Serializer: OverallLeaderboard
# ----------------------------------------------------------------------------------------------
class OverallLeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer to display overall leaderboard data.
    """
    rank = serializers.IntegerField()

    class Meta:
        model = User
        fields = ["telegram_id", "username", "first_name", "balance", "rank"]

# Serializer: RefferalLeaderboard
# ----------------------------------------------------------------------------------------------
class RefferalLeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer for referral leaderboard. Includes additional field to count referrals.
    """
    rank = serializers.IntegerField()
    refferal_counts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["telegram_id", "username", "first_name", "reffered_points", "rank", "refferal_counts"]

    def get_refferal_counts(self, obj):
        """
        Count the number of users referred by the current user.
        """
        return User.objects.filter(reffered_by=obj.telegram_id).count()

    
# Serializer: Tasks
# -----------------------------------------------------------------------------------------------
class TasksSerializer(serializers.ModelSerializer):
    """
    Serializer for listing task details with claim status and image URL.
    """
    claim = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Tasks
        fields = ["id", "name", "description", "task_type", "points", "claim", "image", "url", "action", "is_telegram"]

    def get_claim(self, obj):
        """
        Check if the user has already claimed this task.
        """
        user = self.context['request'].user
        current_time = now()
        start_time = current_time - timedelta(hours=24)

        if obj.task_type == 'daily':
            return UserTaskClaim.objects.filter(user=user, task=obj, date_claimed__gte=start_time).exists()
        elif obj.task_type in ["social", "partner"]:
            return UserTaskClaim.objects.filter(user=user, task=obj).exists()
        
        return False
    
    def get_image(self, obj):
        """
        Provide the task image URL, ensuring it's served over HTTPS.
        """
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url).replace("http://", "https://")
        return None
    
# Serializer: UserTaskClaim
# -----------------------------------------------------------------------------------------------
class UserTaskClaimSerializer(serializers.Serializer):
    """
    Serializer to handle claiming of tasks by users.
    """
    id = serializers.UUIDField()

    def validate_id(self, value):
        """
        Validate that the task ID exists.
        """
        try:
            task = Tasks.objects.get(id=value)
        except Tasks.DoesNotExist:
            raise serializers.ValidationError("Not a Valid Task ID")
        
        # Add the task in context
        self.context["task"] = task
        return value
    
    def validate(self, attrs):
        """
        Ensure the task can be claimed based on its type and user's claim history.
        """
        user = self.context["request"].user
        task = self.context["task"]
        today = timezone.now().date()

        if task.task_type == "daily":
            if UserTaskClaim.objects.filter(user=user, task=task, date_claimed__date=today).exists():
                raise serializers.ValidationError("Task already claimed today.")
        elif task.task_type in ["social", "partner"]:
            if UserTaskClaim.objects.filter(user=user, task=task).exists():
                raise serializers.ValidationError(f"Task already claimed for type: {task.task_type}.")

        return attrs
    
    def save(self, **kwargs):
        """
        Save the task claim and update user's balance.
        """
        user = self.context["request"].user
        task = self.context["task"]
        # create the UserTaskClaim
        claim = UserTaskClaim.objects.create(
            user=user,
            task=task,
            claimed=True
        )

        # update the user balance
        user.balance += task.points
        user.save()
        return claim
    
    def to_representation(self, obj):
        """
        Customize the response to include detailed task information.
        """
        representation = super().to_representation(obj)
        instance = Tasks.objects.get(id=obj.get("id"))
        representation["name"] = instance.name
        representation["description"] = instance.description
        representation["task_type"] = instance.task_type
        representation["points"] = instance.points
        representation["claim"] = True
        representation["image"] = self.context.get("request").build_absolute_uri('/')[:-1].replace("http://", "https://") + instance.image.url if instance.image else None
        representation["url"] = instance.url
        representation["action"] = instance.action
        representation["is_telegram"] = instance.is_telegram
        return representation
    
# Serializer: Cards
# -----------------------------------------------------------------------------------------------
class CardsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Cards model to represent card details, user-specific data,
    and calculated fields such as claim status, level, and points.
    """
    claim = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    burning_points = serializers.SerializerMethodField()
    automine_points = serializers.SerializerMethodField()

    class Meta:
        model = Cards
        fields = ["id", "name", "number", "image", "description", "card_type", "claim", "level", "status", "burning_points", "automine_points"]

    def __init__(self, *args, **kwargs):
        """
        Custom initialization to precompute and cache user-related data
        for efficient lookup during serialization.
        """
        super().__init__(*args, **kwargs)
        user = self.context["request"].user

        # Precompute and store user claims and card levels in context
        self.context["user_card_claims"] = {
            claim.card_id: claim for claim in UserCardClaim.objects.filter(user=user)
        }
        # Precompute claimed card names and levels for quick access in conditions
        self.context["claimed_card_names"] = {
            claim.card.name for claim in self.context["user_card_claims"].values()
        }
        self.context["claimed_card_levels"] = {
            claim.card.name: claim.card_level for claim in self.context["user_card_claims"].values()
        }

        # Fetch all necessary card details and store by (card, level) keys
        self.context["cards_details"] = {
            (detail.card_id, detail.level_number): detail
            for detail in CardsDetails.objects.all()
        }

    def get_image(self, obj):
        """
        Get the card's image URL and ensure it's served via HTTPS.

        Args:
            obj (Cards): Card object.

        Returns:
            str: HTTPS URL of the card image, or None if no image exists.
        """
        request = self.context.get('request')
        if obj.image:
            # Using build_absolute_uri to ensure it's https
            return request.build_absolute_uri(obj.image.url).replace("http://", "https://")
        return None

    def get_claim(self, obj):
        """
        Check if the user has claimed this card.

        Args:
            obj (Cards): Card object.

        Returns:
            bool: True if the card is claimed, False otherwise.
        """
        return obj.id in self.context["user_card_claims"]

    def get_level(self, obj):
        """
        Get the card's level if claimed by the user.

        Args:
            obj (Cards): Card object.

        Returns:
            int: Card level or 0 if unclaimed.
        """
        card_claim = self.context["user_card_claims"].get(obj.id)
        return card_claim.card_level if card_claim else 0

    def get_status(self, obj):
        """
        Determine the card's status (claimed, unlocked, locked) based on user progress.

        Args:
            obj (Cards): Card object.

        Returns:
            str: "claimed", "unlocked", or "locked".
        """
        if self.get_claim(obj):
            return "claimed"

        user_level_number = self.context["request"].user.level_number
        claimed_card_names = self.context["claimed_card_names"]
        claimed_card_levels = self.context["claimed_card_levels"]

        # Conditions for each card based on type and name
        conditions = {
            "eternals": {
                "Eternal Flame": user_level_number >= 2,
                "Infinity Stone": user_level_number >= 2,
                "Timeless Spirit": user_level_number >= 2,
                "Arcane Eternity": "Infinity Stone" in claimed_card_names and "Timeless Spirit" in claimed_card_names,
                "Celestial Bond": claimed_card_levels.get("Infinity Stone", 0) >= 5,
                "Boundless Horizon": user_level_number >= 3,
                "Endless Resolve": claimed_card_levels.get("Arcane Eternity", 0) >= 3,
                "Infinite Grace": "Celestial Bond" in claimed_card_names,
                "Eon's Blessing": user_level_number >= 3,
                "Perpetual Strength": "Eon's Blessing" in claimed_card_names,
            },
            "divine": {
                "Divine Radiance": user_level_number >= 2,
                "Heavenly Beacon": user_level_number >= 2,
                "Seraphim's Grace": user_level_number >= 4,
                "Ascendant Aura": user_level_number >= 4,
                "Sanctified Chalice": (
                    claimed_card_levels.get("Boundless Horizon", 0) >= 4 
                    and claimed_card_levels.get("Seraphim's Grace", 0) >= 2
                ),
                "Celestial Crown": (
                    claimed_card_levels.get("Celestial Bond", 0) >= 3 
                    and claimed_card_levels.get("Heavenly Beacon", 0) >= 2
                ),
                "Elysian Blessing": (
                    claimed_card_levels.get("Infinity Stone", 0) >= 5 
                    and claimed_card_levels.get("Celestial Crown", 0) >= 2
                ),
                "Divine Wrath": (
                    claimed_card_levels.get("Boundless Horizon", 0) >= 4 
                    and claimed_card_levels.get("Seraphim's Grace", 0) >= 2
                ),
                "Halo of Eternity": (
                    claimed_card_levels.get("Infinity Stone", 0) >= 5 
                    and claimed_card_levels.get("Celestial Crown", 0) >= 2
                ),
                "Transcendent Light": (
                    claimed_card_levels.get("Sanctified Chalice", 0) >= 3 
                    and claimed_card_levels.get("Halo of Eternity", 0) >= 2
                ),
            },
            "specials": {
                "Time Warp": user_level_number >= 5,
                "Shadow Step": (
                    claimed_card_levels.get("Sanctified Chalice", 0) >= 3 
                    and claimed_card_levels.get("Halo of Eternity", 0) >= 2
                ),
                "Elemental Burst": user_level_number >= 4,
                "Magic Shield": user_level_number >= 6,
                "Lucky Charm": user_level_number >= 7,
            }
        }
        return "unlocked" if conditions.get(obj.card_type, {}).get(obj.name, False) else "locked"

    def get_burning_points(self, obj):
        """
        Retrieve burning points based on the card's level.

        Args:
            obj (Cards): Card object.

        Returns:
            int or None: Burning points for the card's current level.
        """
        card_claim = self.context["user_card_claims"].get(obj.id)
        level = card_claim.card_level if card_claim else 0  # Use claimed level or default to level 0
        card_detail = self.context["cards_details"].get((obj.id, level))
        return card_detail.burning_points if card_detail else None

    def get_automine_points(self, obj):
        """
        Retrieve automine points based on the card's level.

        Args:
            obj (Cards): Card object.

        Returns:
            int or None: Automine points for the card's current level.
        """
        card_claim = self.context["user_card_claims"].get(obj.id)
        level = card_claim.card_level if card_claim else 0  # Use claimed level or default to level 0
        card_detail = self.context["cards_details"].get((obj.id, level))
        return card_detail.automine_points if card_detail else None
    
# Serializer: UserCardClaim
# ----------------------------------------------------------------------------------------------
class UserCardClaimSerializer(serializers.Serializer):
    """
    Serializer for creating a claim on a card by the user.
    It validates card ID, user's balance, and ensures the card is not already claimed.
    """
    id = serializers.UUIDField() # Card ID
    burning_points = serializers.IntegerField()

    def validate_id(self, value):
        """
        Validate that the card ID exists in the Cards model.

        Args:
            value (UUID): Card ID provided by the user.

        Raises:
            serializers.ValidationError: If the card ID does not exist.

        Returns:
            UUID: Validated card ID.
        """
        try:
            card = Cards.objects.get(id=value)
        except Cards.DoesNotExist:
            raise serializers.ValidationError("Not a valid Card ID.")
        self.context["card"] = card
        return value
    
    def validate(self, attrs):
        """
        Validate user-specific conditions:
        - Ensure the card is not already claimed by the user.
        - Verify the user has sufficient balance.

        Args:
            attrs (dict): Validated data from the request.

        Returns:
            dict: Validated attributes if checks pass.
        """
        user = self.context["request"].user
        card = self.context["card"]
        burning_points = attrs.get("burning_points")
        if UserCardClaim.objects.filter(user=user, card=card).exists():
            raise serializers.ValidationError("Already Claimed.")
        if user.balance < burning_points:
            raise serializers.ValidationError("Insufficients Funds.")
        return attrs
    
    def save(self, **kwargs):
        """
        Create a UserCardClaim instance and deduct burning points from the user's balance.

        Args:
            **kwargs: Additional arguments for the save method.

        Returns:
            UserCardClaim: Newly created claim instance.
        """
        user = self.context["request"].user
        card = self.context["card"]
        burning_points = self.validated_data["burning_points"]
        # create UserCardClaim instance
        claim = UserCardClaim.objects.create(
            user=user,
            card=card,
            claimed=True
        )
        # update the user balance
        user.balance -= burning_points
        user.save()
        self.context["claim"] = claim
        return claim
    
    def to_representation(self, instance):
        """
        Customize the serialized output to include additional card and claim details.

        Args:
            instance: Instance of UserCardClaim.

        Returns:
            dict: Serialized representation.
        """
        representation = super().to_representation(instance)
        claim = self.context["claim"]
        card = CardsDetails.objects.get(card=claim.card, level_number=claim.card_level)
        representation["name"] = claim.card.name
        representation["number"] = claim.card.number
        representation["card_type"] = claim.card.card_type
        representation["image"] = self.context.get("request").build_absolute_uri('/')[:-1].replace("http://", "https://") + claim.card.image.url if claim.card.image else None
        representation["description"] = claim.card.description
        representation["claim"] = True
        representation["level"] = claim.card_level
        representation["status"] = "claimed"
        representation["burning_points"] = card.burning_points
        representation["automine_points"] = card.automine_points
        return representation

# Serializer: UpdateUserCardLevel
# ----------------------------------------------------------------------------------------------
class UpdateUserCardLevelSerializer(serializers.Serializer):
    """
    Serializer for updating a claimed card's level for a user.
    Validates user balance and card eligibility before updating.
    """
    id = serializers.UUIDField()
    points = serializers.IntegerField()

    def get_card_details(self, value):
        """
        Retrieve the UserCardClaim instance for the provided card ID.

        Args:
            value (UUID): Card ID.

        Raises:
            serializers.ValidationError: If the card or its claim doesn't exist.

        Returns:
            UserCardClaim: User's claimed card details.
        """
        try:
            user = self.context["request"].user
            card = Cards.objects.get(id=value)
            card_details = UserCardClaim.objects.get(user=user, card=card)
        except Cards.DoesNotExist:
            raise serializers.ValidationError("Invalid Card ID.")
        except UserCardClaim.DoesNotExist:
            raise serializers.ValidationError("You haven't claimed this card yet.")
        return card_details

    def validate(self, attrs):
        """
        Validate user balance and ensure the card level can be incremented.

        Args:
            attrs (dict): Validated attributes.

        Returns:
            dict: Validated attributes.
        """
        user = self.context["request"].user
        card_details = self.get_card_details(attrs.get("id"))
        points = attrs.get("points")

        if user.balance < points:
            raise serializers.ValidationError("Insufficient funds to claim this card.")

        if card_details.card_level >= 11:
            raise serializers.ValidationError("Card level has already reached the maximum limit.")
        
        self.context["card_details"] = card_details
        return attrs

    def create(self, validated_data):
        """
        Increment the card's level and deduct points from user's balance.

        Args:
            validated_data (dict): Validated data for the update.

        Returns:
            dict: Updated data.
        """
        user = self.context["request"].user
        card_details = self.context["card_details"]
        points = validated_data.get("points")

        # Update the card level (increment by 1)
        card_details.card_level += 1
        card_details.save()

        # Subtract points from user's balance
        user.balance -= points
        user.save()
        return validated_data
    
    def to_representation(self, instance):
        """
        Customize the output to include detailed card information.

        Args:
            instance: Validated instance.

        Returns:
            dict: Serialized representation of updated card details.
        """
        representation = super().to_representation(instance)
        card = self.context["card_details"]
        card_details = CardsDetails.objects.get(card=card.card, level_number=card.card_level)
        representation["name"] = card.card.name
        representation["number"] = card.card.number
        representation["card_type"] = card.card.card_type
        representation["image"] = self.context.get("request").build_absolute_uri('/')[:-1].replace("http://", "https://") + card.card.image.url if card.card.image else None
        representation["description"] = card.card.description
        representation["claim"] = True
        representation["level"] = card.card_level
        representation["status"] = "claimed"
        representation["burning_points"] = card_details.burning_points
        representation["automine_points"] = card_details.automine_points
        return representation
    
# Serializer: CardDetails
# ----------------------------------------------------------------------------------------------
class CardDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for CardsDetails model. Provides detailed information about a specific card level.
    """
    id = serializers.UUIDField(source="card.id", read_only=True)
    name = serializers.CharField(source="card.name", read_only=True)
    number = serializers.IntegerField(source="card.number", read_only=True)
    card_type = serializers.CharField(source="card.card_type", read_only=True)
    image = serializers.URLField(source="card.image", read_only=True)
    description = serializers.CharField(source="card.description", read_only=True)
    level = serializers.IntegerField(source="level_number")
    
    class Meta:
        model = CardsDetails
        fields = ["id", "name", "number", "card_type", "image", "description", "level", "burning_points", "automine_points"]


class BoosterClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoosterClaim
        fields = ['id', 'user', 'claim_type', 'claim_at', 'end_time']

# Serializer: DailyReward
# -------------------------------------------------------------------------------------------
class DailyRewardSerializer(serializers.ModelSerializer):
    """
    Serializer for listing daily rewards and their status.

    This serializer includes the `status` field, which indicates whether a user can claim
    the reward for a particular day or if the reward has already been claimed.
    """
    status = serializers.SerializerMethodField()

    class Meta:
        model = DailyReward
        fields = ["day", "points", "status"]

    def get_status(self, obj):
        """
        Determines the claim status for a particular daily reward based on the user's progress.

        The status can be:
        - 'Claimed': If the reward has already been claimed for the day.
        - 'Can Claim': If the reward is available for claiming today.
        - A formatted time string if the user needs to wait before they can claim again.
        """
        user_reward = self.context.get("user_daily_reward")
        current_time = timezone.localtime(timezone.now())
        # Reset logic if the user missed a claim
        if user_reward.last_claimed_at:
            missed_days = (current_time.date() - user_reward.last_claimed_at.date()).days
            if missed_days > 1:  # If skipped more than one day
                user_reward.reset_reward()

        if obj.day < user_reward.current_day:
            return "Claimed"
        elif obj.day == user_reward.current_day:
            if user_reward.can_claim():
                return "Can Claim"
            else:
                # Calculate the wait time until the next claim
                wait_time = user_reward.next_claim_time()
                # Format the wait time in the server's local timezone
                return wait_time.astimezone(timezone.get_current_timezone()).strftime('%d %b %Y %I:%M %p')
        return "Cannot Claim"
    
    
# Serializer: ClaimReward
# -------------------------------------------------------------------------------------------
class ClaimRewardSerializer(serializers.ModelSerializer):
    """
    Serializer for claiming daily rewards and updating the user's progress.

    This serializer validates whether the user can claim a reward and handles updating 
    the user's reward progress and balance when the claim is successful.
    """
    reward_points = serializers.SerializerMethodField()

    class Meta:
        model = UserDailyReward
        fields = ["current_day", "last_claimed_at", "reward_points"]

    def get_reward_points(self, obj):
        """
        Fetches the points for the current reward day.

        If the current reward day exists, it returns the corresponding points; 
        otherwise, it returns None.
        """
        current_reward = DailyReward.objects.filter(day=obj.current_day).first()
        return current_reward.points if current_reward else None

    def validate(self, attrs):
        """
        Validates whether the user is allowed to claim their reward.

        Checks if the user is eligible to claim the reward for the current day. 
        If not, it raises a validation error with the appropriate message.
        """
        user_reward = self.instance
        if not user_reward.can_claim():
            raise serializers.ValidationError(
                f"You cannot claim your reward yet. Please wait until {user_reward.next_claim_time().strftime('%d %b %Y %I:%M %p')}"
            )
        return attrs

    def save(self, **kwargs):
        """
        Handles claiming the reward and updating the user's balance.

        This method fetches the current reward points, updates the user's reward progress,
        and adds the points to the user's balance.
        """
        user_reward = self.instance

        # Fetch the current reward points
        current_reward = DailyReward.objects.filter(day=user_reward.current_day).first()
        if not current_reward:
            raise serializers.ValidationError("Invalid reward configuration.")

        # Update the user's reward progress
        user_reward.update_reward()

        # Update user's balance or points (assuming a `balance` or similar field on User model)
        user = user_reward.user
        user.balance += current_reward.points
        user.save()

        return user_reward