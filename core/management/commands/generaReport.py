from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.views import salvaPDFgiornaliero

class Command(BaseCommand):
    help = 'Genera e salva il report PDF per la giornata di ieri'

    def handle(self, *args, **options):
        ieri = timezone.now().date() - timedelta(days=1)
        
        self.stdout.write(f"Inizio generazione report per: {ieri}")

        try:
            salvaPDFgiornaliero(ieri)
            self.stdout.write(self.style.SUCCESS(f'Report salvato con successo per il {ieri}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore durante la generazione: {e}'))