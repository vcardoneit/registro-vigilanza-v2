from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from ldap3 import Server, Connection, ALL, core
import requests
from .models import PersonaleINAF, Presenza, TurnoVigilanza, Accesso, RegistroGiornaliero, Log, Impostazioni
from areariservata.views import unisciPDF
from .models import ReportGiornaliero
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def login(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    if request.method == 'POST':
        if 'ldap_username' in request.POST:
            ldap_username = request.POST['ldap_username']
            ldap_password = request.POST['ldap_password']

            try:
                if not PersonaleINAF.objects.filter(nomeutente=ldap_username).exists():
                    messages.warning(request, "Utente non autorizzato")
                    return redirect("/")
            except Exception:
                messages.warning(request, "Errore interno")
                return redirect("/")

            server = Server("ldap://ldap.ced.inaf.it", get_info=ALL)
            search_base = "ou=people,dc=inaf,dc=it"
            user_dn = f"uid={ldap_username},{search_base}"
            try:
                conn = Connection(server, user=user_dn, password=ldap_password, auto_bind=True)
                conn.search(search_base, f"(uid={ldap_username})", attributes=['givenName', 'sn', 'mail'])
            except core.exceptions.LDAPException:
                messages.warning(request, "Username o password LDAP errati")
                return redirect("/")

            user_obj, created = User.objects.get_or_create(username=ldap_username)
            user_obj.set_unusable_password()
            user_obj.is_staff = True
            user_obj.is_superuser = True
 
            if conn.entries:
                entry = conn.entries[0]
                
                if hasattr(entry, 'givenName'):
                    user_obj.first_name = str(entry.givenName)
                
                if hasattr(entry, 'sn'):
                    user_obj.last_name = str(entry.sn)
                    
                if hasattr(entry, 'mail'):
                    user_obj.email = str(entry.mail)

            user_obj.save()

            log = Log(timestamp=timezone.now(), utente=user_obj, azione="Login LDAP effettuato")
            log.save()
            auth_login(request, user_obj)
            return redirect('/')

        if 'username' in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if username == "centrale_operativa":
                auth_login(request, user)
                log = Log(timestamp=timezone.now(), utente=user, azione="Login effettuato")
                log.save()
                return redirect('documenti')
            if user is not None:
                auth_login(request, user)
                if request.user.is_staff == False:
                    turno = TurnoVigilanza.objects.create(
                        vigilante=user,
                        orario_inizio=timezone.now(),
                        orario_fine=None,
                        data=timezone.now().date()
                    )
                    turno.save()
                log = Log(timestamp=timezone.now(), utente=user, azione="Login effettuato")
                log.save()
                return redirect('/')
            else:
                messages.warning(request, 'Password errata')
                return redirect('/')

    usernames = User.objects.filter(is_staff=False).exclude(username='centrale_operativa')
    return render(request, 'login.html', {'usernames': usernames})

@login_required(login_url='/login/')
def logout(request):
    if request.user.is_staff == False:
        try:
            turno = TurnoVigilanza.objects.get(vigilante=request.user, orario_fine__isnull=True)
            turno.orario_fine = timezone.now()
            turno.save()
        except TurnoVigilanza.DoesNotExist:
            pass
    log = Log(timestamp=timezone.now(), utente=request.user, azione="Logout effettuato")
    log.save()
    auth_logout(request)
    messages.success(request, "Logout effettuato con successo")
    return redirect('/')

def cambiaPassword(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        nomeutente = request.POST.get("nomeutente")
        oldpass = request.POST.get("oldpass")
        newpassword = request.POST.get("newpassword")
        conferma = request.POST.get("conferma")
        if nomeutente == "" or oldpass == "" or newpassword == "" or conferma == "":
            messages.warning(request, "Compilare tutti i campi")
            return redirect("/cambiaPassword/")
        if newpassword != conferma:
            messages.warning(request, "Le nuove password non coincidono")
            return redirect("/cambiaPassword/")
        user = authenticate(username=nomeutente, password=oldpass)
        if user is None:
            messages.warning(request, "Vecchia password errata")
            return redirect("/cambiaPassword/")
        log = Log(timestamp=timezone.now(), utente=user, azione=f"Password cambiata per utente: {nomeutente}")
        log.save()
        user.set_password(newpassword)
        user.save()
        messages.success(request, "Password cambiata con successo")
        return redirect("/")
    else:
        usernames = User.objects.filter(is_staff=False).exclude(username='centrale_operativa')
        return render(request, "changepassword.html", {"usernames": usernames})

@login_required(login_url='/login/')
def aggiornaRegistroVigilanza(request):
    if request.method == "POST" and request.user.is_authenticated:
        registro = RegistroGiornaliero.objects.get(data=timezone.now().date())

        personaleINAF = request.POST.getlist("personale_ids")
        Presenza.objects.filter(registro=registro).exclude(personale_id__in=personaleINAF).update(is_present=False)
        for personale_id in personaleINAF:
            Presenza.objects.update_or_create(
                registro=registro,
                personale_id=personale_id,
                defaults={'is_present': True} 
            )

        note = request.POST.get("note")
        registro.note = note

        registro.save()
        log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Aggiornato registro vigilanza: Note={note}, Personale INAF={personaleINAF}")
        log.save()
        messages.success(request, "Note e/o personale aggiornato con successo")
        return redirect("/")
    else:
        return redirect("/")

@login_required(login_url='/login/')
def registraAccesso(request, turno_id):
    if request.method == "POST" and request.user.is_authenticated:
        nominativi_raw = request.POST.get("nominativi")
        ditta = request.POST.get("ditta")
        oraIngresso_time = timezone.datetime.strptime(request.POST.get("oraIngresso"), "%H:%M").time()
        oraIngresso = timezone.make_aware(
            timezone.datetime.combine(timezone.now().date(), oraIngresso_time),
            timezone.get_current_timezone()
        )
        
        nominativi_list = [n.strip() for n in nominativi_raw.split('\n') if n.strip()]
        
        accessi_creati = []
        for nominativo in nominativi_list:
            nuovo_accesso = Accesso(turno_id=turno_id, nominativi=nominativo, ditta=ditta, oraIngresso=oraIngresso)
            nuovo_accesso.save()
            accessi_creati.append(nominativo)
        
        log = Log(
            timestamp=timezone.now(),
            utente=request.user,
            azione=f"Registrati {len(accessi_creati)} nuovi accessi: Nominativi={', '.join(accessi_creati)}, Ditta={ditta}, Ora Ingresso={oraIngresso}"
        )
        log.save()
        
        if len(accessi_creati) == 1:
            messages.success(request, "Accesso registrato con successo")
        else:
            messages.success(request, f"{len(accessi_creati)} accessi registrati con successo")
        return redirect("/")
    else:
        return redirect("/")

@login_required(login_url='/login/')
def aggiornaAccesso(request, accesso_id):
    if request.method == "POST" and request.user.is_authenticated:
        nominativi = request.POST.get("nominativi")
        ditta = request.POST.get("ditta")
        oraIngresso_time = timezone.datetime.strptime(request.POST.get("oraIngresso"), "%H:%M").time()
        oraIngresso = timezone.make_aware(
            timezone.datetime.combine(timezone.now().date(), oraIngresso_time),
            timezone.get_current_timezone()
        )
        accesso = Accesso.objects.get(id=accesso_id)
        accesso.nominativi = nominativi
        accesso.ditta = ditta
        accesso.oraIngresso = oraIngresso
        if request.POST.get("oraUscita"):
            oraUscita_time = timezone.datetime.strptime(request.POST.get("oraUscita"), "%H:%M").time()
            oraUscita = timezone.make_aware(
                timezone.datetime.combine(timezone.now().date(), oraUscita_time),
                timezone.get_current_timezone()
            )
            accesso.oraUscita = oraUscita
        else:
            accesso.oraUscita = None
        accesso.save()

        log_entry = Log(
            timestamp=timezone.now(),
            utente=request.user,
            azione=f"Aggiornato accesso ID {accesso_id}: Nominativi={nominativi}, Ditta={ditta}, Ora Ingresso={oraIngresso}, Ora Uscita={accesso.oraUscita}"
        )
        log_entry.save()
        
        messages.success(request, "Accesso aggiornato con successo")
        return redirect("/")
    else:
        return redirect("/")

@login_required(login_url='/login/')
def eliminaAccesso(request, accesso_id):
    if request.method == "POST" and request.user.is_authenticated:
        accesso = Accesso.objects.get(id=accesso_id)

        log = Log(
            timestamp=timezone.now(),
            utente=request.user,
            azione=f"Eliminato accesso ID {accesso_id}: Nominativi={accesso.nominativi}, Ditta={accesso.ditta}, Ora Ingresso={accesso.oraIngresso}, Ora Uscita={accesso.oraUscita}"
        )
        log.save()

        accesso.delete()
        messages.success(request, "Accesso eliminato con successo")
        return redirect("/")
    else:
        return redirect("/")
    
def telegram(message):
    token = Impostazioni.objects.first().telegram_bot_token if Impostazioni.objects.exists() else "False"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": Impostazioni.objects.first().telegram_chat_id if Impostazioni.objects.exists() else "False",
        "text": message,
        "parse_mode": "HTML",
    }
    
    if token == "False" or payload["chat_id"] == "False":
        return {"ok": False, "description": "Token or Chat ID not set in environment variables."}

    response = requests.post(url, data=payload)
    return response.json()

def salvaPDFgiornaliero(date_obj):
    date_for_merge = date_obj.strftime("%Y-%m-%d")
    today_str = date_obj.strftime("%d-%m-%Y")

    pdf_buffer = unisciPDF(date_for_merge)

    filename = f"ReportServizioVigilanza_{today_str}.pdf"

    report, created = ReportGiornaliero.objects.update_or_create(
        data_riferimento=date_obj,
        defaults={} 
    )

    report.pdf.save(filename, ContentFile(pdf_buffer.getvalue()), save=True)

    return report

@csrf_exempt
def telegramWebhook(request):
    try:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                chat_id = data['message']['chat']['id']
                chat_id_env = Impostazioni.objects.first().telegram_chat_id if Impostazioni.objects.exists() else "False"
                
                if 'message' in data and 'text' in data['message'] and str(chat_id) == chat_id_env:
                    try:
                        msg = data['message']
                        text = msg.get('text', '')
                        username = msg['from'].get('first_name', '') + ' ' + msg['from'].get('last_name', '')

                        if text.startswith('!send '):
                            message_to_send = text.replace('!send ', '', 1).strip()
                            if message_to_send:
                                try:
                                    turno_attivo = TurnoVigilanza.objects.get(orario_fine=None)
                                    target_user = turno_attivo.vigilante

                                    channel_layer = get_channel_layer()
                                    async_to_sync(channel_layer.group_send)(
                                        f"user_{target_user.id}",
                                        {
                                            'type': 'send_reply',
                                            'message': f"<b>{username}</b>: {message_to_send}"
                                        }
                                    )
                                    telegram(f"Messaggio inoltrato all'utente in turno <b>{target_user.username}</b>.")
                                except TurnoVigilanza.DoesNotExist:
                                    telegram("Nessun utente è attualmente in turno.")
                            else:
                                telegram("Il messaggio non può essere vuoto.")
                    except Exception as e:
                        telegram(f"Errore inaspettato nel webhook: {str(e)}")

            except json.JSONDecodeError:
                telegram("Errore inaspettato nel webhook")
                return JsonResponse({'status': 'bad request'}, status=400)
    except Exception as e:
        print(f"Errore inaspettato nel webhook: {str(e)}")
            
    return JsonResponse({'status': 'ok'})
