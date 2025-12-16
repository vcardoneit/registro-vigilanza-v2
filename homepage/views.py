from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import RegistroGiornaliero, PersonaleINAF, TurnoVigilanza, Accesso, Presenza, Log, Marcatura
from core.views import telegram
from django.utils import timezone
from django.contrib import messages

@login_required(login_url='/login/')
def homepage(request):
    if RegistroGiornaliero.objects.filter(data=timezone.now().date()).exists() == False:
        RegistroGiornaliero.objects.create(data=timezone.now().date())

    if request.user.is_staff:
        return redirect('dashboard')
    
    if request.method == "POST" and "esegui_marcatura" in request.POST:
        
        Marcatura.objects.create(
            utente=request.user,
            orario=timezone.now(),
        )
        
        log = Log(timestamp=timezone.now(), utente=request.user, azione="Marcatura effettuata")
        log.save()

        messages.success(request, "Marcatura eseguita con successo")
        return redirect('/')

    if request.method == "POST" and "data_ricerca" in request.POST:
        data = request.POST['data_ricerca']
        if data == timezone.now().date().strftime("%Y-%m-%d"):
            return redirect('/')
        personaleINAF = Presenza.objects.filter(registro__data=data).select_related('personale').order_by('personale__nominativo')
    else:
        data = timezone.now().date()
        personaleINAF = PersonaleINAF.objects.all().order_by('nominativo')
    try:
        RegistroGiornaliero.objects.get(data=data)
    except RegistroGiornaliero.DoesNotExist:
        messages.warning(request, f"Non esiste un registro per la data {data}.")
        return redirect('/')
    
    turno_attivo = TurnoVigilanza.objects.filter(vigilante=request.user, orario_fine__isnull=True).first()
    accessi = Accesso.objects.filter(turno__data=data).select_related('turno').order_by('-oraUscita')
    
    note = RegistroGiornaliero.objects.get(data=data).note
    registro = RegistroGiornaliero.objects.get(data=data)
    personaleINAFpresente = set(registro.presenza_set.filter(is_present=True).values_list('personale_id', flat=True))
    ultimaMarcatura = Marcatura.objects.all().order_by('-orario').first()
    return render(request, 'homepage/index.html', {
        'data': data,
        'turno_attivo': turno_attivo,
        'accessi': accessi,
        'note': note,
        'listaPersonaleINAF': personaleINAF,
        'personaleINAFpresente': personaleINAFpresente,
        'ultimaMarcatura': ultimaMarcatura
    })

@login_required(login_url='/login/')
def messaggioTelegram(request):
    if request.method == "POST" and request.user.is_authenticated:
        messaggio = request.POST.get("messaggio")
        utente = request.user.get_full_name() or request.user.username

        message = (
            "🔔 <b>REGISTRO VIGILANZA</b> 🔔\n\n"
            f"👤 <b>Utente:</b> {utente}\n\n"
            f"<i>{messaggio}</i>"
        )
        telegram(message)
        
        log = Log(timestamp=timezone.now(), utente=request.user, azione="Invio messaggio telegram: " + messaggio)
        log.save()
        messages.success(request, "Messaggio inviato con successo")
        return redirect("/")
    else:
        return redirect("/")