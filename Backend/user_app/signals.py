from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import User, RefferReward, Earnings

@receiver(post_save, sender=User)
def handle_rewards(sender, instance, created, **kwargs):
    if created and instance.reffered_by:
        # Process referral reward if the user was referred by another user
        try:
            refferer = User.objects.get(telegram_id=instance.reffered_by)

            # Apply the reward based on the user level
            try:
                reward = RefferReward.objects.get(level_number=refferer.level_number).reward_amount
                refferer.reffered_points += reward
                refferer.balance += reward
                refferer.save()
            except RefferReward.DoesNotExist:
                pass  # Handle case where reward does not exist for that level

        except User.DoesNotExist:
            pass  # Handle case where refferer is not found

@receiver(post_save, sender=Earnings)
def update_user_balance(sender, instance, created, **kwargs):
    # Update the balance only when new instance is created
    if created:
        # get the user
        user = instance.user
        # check the transaction type
        match instance.transaction_type:
            case "CREDIT":
                user.balance += instance.amount
            case "DEBIT":
                if instance.reason == "Mutitap Increase" and user.multitap_level <= 12:
                    user.balance -= instance.amount
                    user.multitap_level += 1
                elif instance.reason == "Recharging Speed Increase" and user.recharging_speed_level <= 12:
                    user.balance -= instance.amount
                    user.recharging_speed_level += 1
                elif instance.reason == "Auto Pray" and not user.autobot_status:
                    user.balance -= instance.amount
                    user.autobot_status = True
        # Save the user details
        user.save()
        # Update the user level
        user.update_user_level()

@receiver(post_save, sender=User)
def update_user_level(sender, instance, **kwargs):
    """
    Signal handler to update user level after user save.
    """
    update_fields = kwargs.get('update_fields', None)

    # If update_fields is specified and includes 'level_number', skip the signal logic
    if update_fields and 'level_number' in update_fields:
        return
    
    if instance.update_user_level():
        instance.save(update_fields=['level_name', 'level_number'])