import uuid
from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from .managers import UserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

# Table: User
# ---------------------------------------------------------------------------------------------------
class User(AbstractBaseUser, PermissionsMixin):
    RELIGION_CHOICES = [
        ("Islamic", "Islamic"),
        ("Buddhism", "Buddhism"),
        ("Christianity", "Christianity"),
        ("Sikhism", "Sikhism"),
        ("Judaism", "Judaism"),
        ("Hindu", "Hindu"),
        ("Mothernature", "Mother Nature"),
        ("Unaffiliated", "Unaffiliated"),
    ]
    telegram_id = models.PositiveBigIntegerField(unique=True)
    username = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    reffer_id = models.PositiveBigIntegerField()
    reffered_by = models.PositiveBigIntegerField(null=True, blank=True)
    reffered_points = models.PositiveBigIntegerField(default=0)

    balance = models.PositiveBigIntegerField(default=0)
    level_number = models.PositiveIntegerField(default=1)
    level_name = models.CharField(max_length=100, default="Seeker of Truth")
    welcome_bonus = models.BooleanField(default=False)

    multitap_level = models.PositiveIntegerField(default=0)
    recharging_speed_level = models.PositiveIntegerField(default=0)
    autobot_status = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    user_religion = models.CharField(
        max_length=50, choices=RELIGION_CHOICES, null=True, blank=True
    )

    USERNAME_FIELD = "telegram_id"
    REQUIRED_FIELDS = ["username", "first_name"]

    objects = UserManager()

    def __str__(self) -> str:
        return f"{self.telegram_id} {self.username}"
    
    def update_user_level(self):
        """
        Update the user level based on the Rules
        """
        rule = Rules.objects.filter(
            lower_points__lte=self.balance,
            higher_points__gte=self.balance
        ).first()
        if rule and (rule.level_number > self.level_number):
            self.level_name = rule.level_name
            self.level_number = rule.level_number
            # Update only the level fields to prevent infinite recursion
            self.save(update_fields=['level_name', 'level_number'])
            return True
        return False
    
# Table: Rules
# ---------------------------------------------------------------------------------------------------
class Rules(models.Model):
    level_number = models.PositiveIntegerField(default=1)
    level_name = models.CharField(max_length=100)
    lower_points = models.PositiveBigIntegerField()
    higher_points = models.PositiveBigIntegerField()
    per_tap = models.PositiveIntegerField()
    point_refill = models.PositiveIntegerField()
    number_of_tap = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.level_number} {self.level_name}"
    
# Table: RefferReward
# ---------------------------------------------------------------------------------------------------
class RefferReward(models.Model):
    level_number = models.PositiveIntegerField()
    reward_amount = models.PositiveBigIntegerField()

    def __str__(self) -> str:
        return f"{self.level_number} {self.reward_amount}"

# Table: Earning
# ---------------------------------------------------------------------------------------------------
class Earnings(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ("CREDIT", "credit"),
        ("DEBIT", "debit")
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_earnings")
    amount = models.PositiveBigIntegerField()
    transaction_type = models. CharField(max_length=6, choices=TRANSACTION_TYPE_CHOICES)
    reason = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.telegram_id} - {self.transaction_type} - {self.amount} on {self.timestamp}"

# Table: Tasks
# ----------------------------------------------------------------------------------------------------
class Tasks(models.Model):
    TASKS_TYPES_CHOICE = [
        ("daily", "Daily"),
        ("social", "Social"),
        ("partner", "Partner")
    ]
    ACTION_CHOICES = [
        ("join", "Join"),
        ("visit", "Visit")
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=10, choices=TASKS_TYPES_CHOICE)
    points = models.PositiveIntegerField()
    image = models.ImageField(upload_to="tasks")
    url = models.URLField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default="visit")
    is_telegram = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
    
# Table: UserTaskClaim
# -----------------------------------------------------------------------------------------------------
class UserTaskClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_tasks")
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    claimed = models.BooleanField(default=False)
    date_claimed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "task", "date_claimed")

    def __str__(self) -> str:
        return f"{self.user.telegram_id} - {self.task.name} - {self.claimed}"

# Table: Cards
# -----------------------------------------------------------------------------------------------------
class Cards(models.Model):
    CARDS_TYPE_CHOICES = [
        ("eternals", "Eternals"),
        ("divine", "Divine"),
        ("specials", "specials")
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    number = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="cards", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    card_type = models.CharField(max_length=20, choices=CARDS_TYPE_CHOICES)

    def __str__(self) -> str:
        return f"{self.number} - {self.name}"
    
# Table: CardsDetails
# -----------------------------------------------------------------------------------------------------
class CardsDetails(models.Model):
    card = models.ForeignKey(Cards, on_delete=models.CASCADE, related_name="cards_details")
    level_number = models.PositiveIntegerField(default=0)
    burning_points = models.PositiveIntegerField()
    automine_points = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.card.name} - {self.level_number} - {self.burning_points} - {self.automine_points}"
    
# Table: UserCardClaim
# -----------------------------------------------------------------------------------------------------
class UserCardClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_cards")
    card = models.ForeignKey(Cards, on_delete=models.CASCADE)
    card_level = models.PositiveIntegerField(default=0)
    claimed = models.BooleanField(default=False)
    date_claimed = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "card")

    def __str__(self) -> str:
        return f"{self.user.telegram_id} - {self.card.name} - {self.claimed}"
    
class BoosterClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    claim_type = models.CharField(max_length=50)  # 'energy' or 'power'
    claim_at = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'claim_at')

class DailyReward(models.Model):
    day = models.PositiveIntegerField()
    points = models.PositiveIntegerField()

    def __str__(self):
        return f"Day: {self.day}: {self.points} Points"
    
class UserDailyReward(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_daily_reward')
    current_day = models.PositiveIntegerField(default=1)
    last_claimed_at = models.DateTimeField(null=True, blank=True)

    def reset_reward(self):
        """
        Reset the user's reward progress to Day 1.
        """
        self.current_day = 1
        self.last_claimed_at = None
        self.save()

    def can_claim(self):
        """
        Check if the user can claim today's reward.
        """
        if not self.last_claimed_at:
            return True
        next_claim_time = self.last_claimed_at + timedelta(days=1)

        # Reset if the claim window is missed
        if now() > next_claim_time + timedelta(days=1):  # More than a day skipped
            self.reset_reward()
            return True

        return now() >= next_claim_time

    def next_claim_time(self):
        """
        Return the next claimable time for the user.
        """
        return self.last_claimed_at + timedelta(days=1) if self.last_claimed_at else None

    def update_reward(self):
        """
        Update the user's reward progress. Resets to Day 1 if the claim window was missed.
        """
        if not self.can_claim():
            return False

        # Update day and last claimed timestamp
        self.current_day = self.current_day + 1 if self.current_day < 7 else 1
        self.last_claimed_at = now()
        self.save()
        return True