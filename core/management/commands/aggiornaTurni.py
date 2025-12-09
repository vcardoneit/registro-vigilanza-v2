from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from core.models import TurnoVigilanza

class Command(BaseCommand):
    help = 'Chiude i turni aperti del giorno precedente e crea i nuovi turni per oggi'

    def handle(self, *args, **kwargs):
        oggi = timezone.now().date()
        ieri = oggi - timezone.timedelta(days=1)
        
        with transaction.atomic():
            turni_aperti = TurnoVigilanza.objects.select_for_update().filter(
                orario_fine__isnull=True, 
                data=ieri
            )
            
            if not turni_aperti.exists():
                self.stdout.write("Nessun turno da aggiornare.")
                return

            count = 0
            for t in turni_aperti:
                fine_ieri = timezone.make_aware(
                    timezone.datetime.combine(ieri, timezone.datetime.max.time()), 
                    timezone.get_current_timezone()
                )
                t.orario_fine = fine_ieri
                t.save()

                inizio_oggi = timezone.make_aware(
                    timezone.datetime.combine(oggi, timezone.datetime.min.time()), 
                    timezone.get_current_timezone()
                )
                
                if not TurnoVigilanza.objects.filter(vigilante=t.vigilante, data=oggi).exists():
                    TurnoVigilanza.objects.create(
                        vigilante=t.vigilante,
                        orario_inizio=inizio_oggi,
                        orario_fine=None,
                        data=oggi
                    )
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Aggiornati {count} turni.'))