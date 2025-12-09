from django.contrib import admin
from .models import PersonaleINAF, TurnoVigilanza, Accesso, RegistroGiornaliero, Presenza, Log, Impostazioni, ReportGiornaliero, Fattura, Turni

admin.site.register(PersonaleINAF)
admin.site.register(TurnoVigilanza)
admin.site.register(Accesso)
admin.site.register(RegistroGiornaliero)
admin.site.register(Presenza)
admin.site.register(Log)
admin.site.register(Impostazioni)
admin.site.register(ReportGiornaliero)
admin.site.register(Fattura)
admin.site.register(Turni)