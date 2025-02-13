from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _

# Manager: User
# -----------------------------------------------------------------------------------------
class UserManager(BaseUserManager):
    def create_user(self, telegram_id, username, first_name, password=None, **extra_fields):
        """
        Create and save a User with given telegram_id, username, first_name
        """
        if not telegram_id:
            raise ValueError(_("user must have an telegram_id"))
        
        user = self.model(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            reffer_id=telegram_id,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, telegram_id, username, first_name, password, **extra_fields):
        """
        Create and save a Superuser with given email and password
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("superuser must have is_superuser=True"))
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("superuser must have is_staff=True"))
        return self.create_user(telegram_id, username, first_name, password, **extra_fields)