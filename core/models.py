import os
from django.db import models
from django.contrib.auth.models import User

# Personale INAF (Nome completo e nome utente)
class PersonaleINAF(models.Model):
    nominativo = models.CharField(max_length=100, unique=True, verbose_name="Nominativo completo")
    nomeutente = models.CharField(max_length=50, unique=True, verbose_name="Nome utente INAF", null=True, blank=True)

    def __str__(self):
        return self.nominativo
    
    class Meta:
        verbose_name_plural = "Personale INAF"

# Presenza Personale INAF
class Presenza(models.Model):
    registro = models.ForeignKey('RegistroGiornaliero', on_delete=models.CASCADE, verbose_name="Registro giornaliero")
    personale = models.ForeignKey(PersonaleINAF, on_delete=models.CASCADE, verbose_name="Personale INAF")
    is_present = models.BooleanField(default=True, verbose_name="È attualmente presente?")

    class Meta:
        unique_together = ('registro', 'personale')
        verbose_name_plural = "Presenze del personale INAF"

    def __str__(self):
        status = "Presente" if self.is_present else "Uscito"
        return f"{self.personale.nominativo} ({status}) nel registro del {self.registro.data}"

# Turni di vigilanza
class TurnoVigilanza(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    vigilante = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Vigilante") 
    orario_inizio = models.DateTimeField(verbose_name="Orario di inizio")
    orario_fine = models.DateTimeField(blank=True, null=True, verbose_name="Orario di fine")
    data = models.DateField(verbose_name="Data del turno")

    def __str__(self):
        return f"Turno di {self.vigilante.username} il {self.data}"
    
    class Meta:
        verbose_name_plural = "Turni di vigilanza"

# Accessi registrati durante i turni di vigilanza
class Accesso(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    turno = models.ForeignKey(TurnoVigilanza, on_delete=models.CASCADE, verbose_name="Turno di vigilanza")
    nominativi = models.TextField(verbose_name="Nominativi degli accessi")
    ditta = models.CharField(max_length=100, verbose_name="Ditta")
    oraIngresso = models.DateTimeField(verbose_name="Ora di ingresso")
    oraUscita = models.DateTimeField(null=True, blank=True, verbose_name="Ora di uscita")

    def __str__(self):
        return f"Accesso {self.ditta} {self.nominativi} alle {self.oraIngresso}"
    
    class Meta:
        verbose_name_plural = "Accessi"

# Registro giornaliero - data accessi turni note personale
class RegistroGiornaliero(models.Model):
    data = models.DateField(unique=True, verbose_name="Data del registro")
    accessi = models.ManyToManyField(Accesso, blank=True, related_name='registri_giornalieri', verbose_name="Accessi del giorno")
    turni = models.ManyToManyField(TurnoVigilanza, blank=True, related_name='registri_giornalieri', verbose_name="Turni del giorno")
    note = models.TextField(blank=True, verbose_name="Note della giornata")
    personale = models.ManyToManyField(
        PersonaleINAF,
        through='Presenza',
        blank=True,
        related_name='registri_giornalieri',
        verbose_name="Personale presente"
    )

    def __str__(self):
        return f"Registro giornaliero del {self.data}"
    
    class Meta:
        verbose_name_plural = "Registri giornalieri"

# Impostazioni generali
class Impostazioni(models.Model):
    telegram_bot_token = models.CharField(max_length=200, blank=True, verbose_name="Token del bot Telegram")
    telegram_chat_id = models.CharField(max_length=100, blank=True, verbose_name="Chat ID Telegram")
    debug = models.BooleanField(default=False, verbose_name="Modalità debug")

    def __str__(self):
        return "Impostazioni generali"
    
    class Meta:
        verbose_name_plural = "Impostazioni generali"

# Logs
class Log(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    utente = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utente")
    azione = models.TextField(verbose_name="Log")

    def __str__(self):
        return f"{self.timestamp} - {self.utente.username} - {self.azione}"
    
    class Meta:
        verbose_name_plural = "Logs"

# Report giornaliero in PDF
class ReportGiornaliero(models.Model):
    data_riferimento = models.DateField(unique=True)
    pdf = models.FileField(upload_to='reports/%Y/%m_%B/')
    creato_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report del {self.data_riferimento}"
    
    class Meta:
        verbose_name_plural = "Report giornalieri"

# Model file fatture (data caricamento, file, descrizione)
class Fattura(models.Model):
    data_caricamento = models.DateTimeField(auto_now_add=True, verbose_name="Data di caricamento")
    data_riferimento = models.DateField(verbose_name="Data di riferimento della fattura")
    file = models.FileField(upload_to='fatture/%Y/%m_%B/', verbose_name="File della fattura")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione della fattura")

    def __str__(self):
        return f"Fattura caricata il {self.data_caricamento}"

    @property
    def nome_file(self):
        return os.path.basename(self.file.name)
    
    class Meta:
        verbose_name_plural = "Fatture"

# Model file programmazione turni (data caricamento, file, descrizione)
class Turni(models.Model):
    data_caricamento = models.DateTimeField(auto_now_add=True, verbose_name="Data di caricamento")
    data_riferimento = models.DateField(verbose_name="Data di riferimento della programmazione")
    file = models.FileField(upload_to='turni/%Y/%m_%B/', verbose_name="File della programmazione turni")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione della programmazione")

    def __str__(self):
        return f"Programmazione turni caricata il {self.data_caricamento}"
    
    @property
    def nome_file(self):
        return os.path.basename(self.file.name)
    
    class Meta:
        verbose_name_plural = "Programmazioni turni"