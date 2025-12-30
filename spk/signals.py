from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    """Create or update UserProfile when User is saved"""
    if created:
        try:
            # Coba buat dengan default values
            UserProfile.objects.create(
                user=instance,
                role='viewer',  # Default role
                phone='',       # Default empty string
                department='',  # Default empty string
                alamat=''       # Default empty string
            )
        except Exception as e:
            # Log error tapi jangan crash
            print(f"Error creating UserProfile for {instance.username}: {e}")
