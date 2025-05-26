from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Profile


@receiver(pre_save, sender=Profile)
def delete_old_avatar(sender, instance, **kwargs):
    if not instance.pk:  # yeni kayıt
        return
    old = Profile.objects.get(pk=instance.pk)
    # değişmiş & eski dosya default değilse
    if (
        old.avatar
        and old.avatar != instance.avatar
        and old.avatar.name != "avatars/default.png"
    ):
        old.avatar.delete(save=False)
