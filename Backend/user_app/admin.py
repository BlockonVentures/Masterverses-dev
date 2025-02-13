from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Admin: User
# ---------------------------------------------------------------------------------------
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("telegram_id", "username", "reffered_points", "reffered_by", "balance", "level_number", "level_name", "is_staff", "is_active")
    list_filter = ("telegram_id", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("telegram_id", "balance", "reffered_by", "reffered_points", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "telegram_id", "username", "first_name", "reffered_by", "reffer_id", "password", "is_staff",
                    "is_active", "groups", "user_permissions"
                )
            }
        ),
    )
    search_fields = ("telegram_id",)
    ordering = ("telegram_id",)

# Admin: Rules
# ----------------------------------------------------------------------------------------
class RulesAdmin(admin.ModelAdmin):
    list_display = ["level_number", "level_name"]

# Admin: RefferReward
# ----------------------------------------------------------------------------------------
class RefferRewardAdmin(admin.ModelAdmin):
    list_display = ["level_number", "reward_amount"]

# Admin: Earnings
# ----------------------------------------------------------------------------------------
class EarningsAdmin(admin.ModelAdmin):
    list_display = ["user", "transaction_type", "amount", "reason"]

# Admin: Tasks
# -----------------------------------------------------------------------------------------
class TasksAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "task_type", "points"]

# Admin: UserTaskClaim
# ------------------------------------------------------------------------------------------
class UserTaskClaimAdmin(admin.ModelAdmin):
    list_display = ["user", "task", "claimed", "date_claimed"]

# Admin: DailyReward
# ---------------------------------------------------------------------------------------
class DailyRewardAdmin(admin.ModelAdmin):
    list_display = ["day", "points"]

# Admin: UserDailyReward
# ---------------------------------------------------------------------------------------
class UserDailyRewardAdmin(admin.ModelAdmin):
    list_display = ["user", "current_day", "last_claimed_at"]

# Admin: Cards
# ------------------------------------------------------------------------------------------
class CardsAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "card_type"]

# Admin: CardsDetails
# ------------------------------------------------------------------------------------------
class CardsDetailsAdmin(admin.ModelAdmin):
    list_display = ["card", "level_number", "burning_points", "automine_points"]

# Admin: UserCardClaim
# ------------------------------------------------------------------------------------------
class UserCardClaimAdmin(admin.ModelAdmin):
    list_display = ["user", "card"]

def _register(model, admin_class):
    admin.site.register(model, admin_class)

_register(User, CustomUserAdmin)
_register(Rules, RulesAdmin)
_register(RefferReward, RefferRewardAdmin)
_register(Earnings, EarningsAdmin)
_register(Tasks, TasksAdmin)
_register(UserTaskClaim, UserTaskClaimAdmin)
_register(Cards, CardsAdmin)
_register(CardsDetails, CardsDetailsAdmin)
_register(UserCardClaim, UserCardClaimAdmin)
_register(DailyReward, DailyRewardAdmin)
_register(UserDailyReward, UserDailyRewardAdmin)