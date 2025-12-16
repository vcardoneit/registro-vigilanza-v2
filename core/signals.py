from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TurnoVigilanza, Accesso, RegistroGiornaliero


@receiver(post_save, sender=TurnoVigilanza)
def collega_turno_a_registro(sender, instance, created, **kwargs):
    registro, _ = RegistroGiornaliero.objects.get_or_create(data=instance.data)
    
    if not registro.turni.filter(id=instance.id).exists():
        registro.turni.add(instance)


@receiver(post_save, sender=Accesso)
def collega_accesso_a_registro(sender, instance, created, **kwargs):
    data_accesso = instance.oraIngresso.date()
    
    registro, _ = RegistroGiornaliero.objects.get_or_create(data=data_accesso)
    
    if not registro.accessi.filter(id=instance.id).exists():
        registro.accessi.add(instance)
