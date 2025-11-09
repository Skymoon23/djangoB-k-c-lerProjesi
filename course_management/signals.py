from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    yeni bir User oluşturulduğunda,
    ona bağlı bir Profile nesnesini de otomatik oluştur
    """
    if created:
        # yeni kullanıcı oluşturulduğunda rolü student olarak ata
        # bölüm başkanı veya hoca ise admin panelinden değiştir
        Profile.objects.create(user=instance, role='student')
    instance.profile.save()
