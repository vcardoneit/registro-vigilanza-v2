import calendar
from datetime import date
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from core.models import *
from django.contrib.auth.models import User
import csv
from django.http import HttpResponse
from django.utils.dateparse import parse_datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.units import cm
import os
from PyPDF2 import PdfReader, PdfWriter

@staff_member_required(login_url='')
def dashboard(request):
    if request.method == 'POST' and 'data' in request.POST:
        try:
            data = timezone.datetime.strptime(request.POST['data'], '%Y-%m-%d').date()
        except ValueError:
            data = timezone.localdate()
    else:
        data = timezone.localdate()

    listaAccessi = Accesso.objects.filter(oraIngresso__date=data).order_by('oraIngresso')
    listaTurni = TurnoVigilanza.objects.filter(orario_inizio__date=data).order_by('orario_inizio')
    listaPresenze = Presenza.objects.filter(registro__data=data).select_related('personale').order_by('personale__nominativo')
    note = RegistroGiornaliero.objects.filter(data=data).values_list('note', flat=True)

    context = {
        'data': data,
        'accessi': listaAccessi,
        'turni': listaTurni,
        'note': note[0] if note else '',
        'personale': listaPresenze,
    }

    return render(request, 'areariservata/index.html', context)

def impostazioni(request):
    if request.method == "POST" and request.user.is_staff:
        bot_token = request.POST.get("telegram_bot_token")
        chat_id = request.POST.get("telegram_chat_id")

        impostazioni, created = Impostazioni.objects.get_or_create(id=1)
        impostazioni.telegram_bot_token = bot_token
        impostazioni.telegram_chat_id = chat_id
        impostazioni.save()

        messages.success(request, "Impostazioni salvate con successo.")
        log = Log(timestamp=timezone.now(), utente=request.user, azione="Impostazioni Telegram aggiornate")
        log.save()
        return redirect("/impostazioni/")
    bot_token = Impostazioni.objects.first().telegram_bot_token if Impostazioni.objects.exists() else ""
    chat_id = Impostazioni.objects.first().telegram_chat_id if Impostazioni.objects.exists() else ""
    return render(request, 'areariservata/impostazioni.html', {
        "telegram_bot_token": bot_token,
        "telegram_chat_id": chat_id,
    })

def utenti(request):
    personaleINAF = PersonaleINAF.objects.all().order_by('nominativo')
    vigilanti = User.objects.filter(is_staff=False).order_by('username').exclude(username='centrale_operativa')
    return render(request, 'areariservata/utenti.html', {
        'personaleINAF': personaleINAF,
        'vigilanti': vigilanti,
    })

# --------------- Gestione Utenti INAF ---------------

def aggiungiPersonaleINAF(request):
    if request.method == "POST" and request.user.is_staff:
        nome_completo = request.POST.get("nome")
        nomeutenteInaf = request.POST.get("associated_username")
        
        if PersonaleINAF.objects.filter(nominativo=nome_completo).exists():
            messages.warning(request, "Esiste già un utente INAF con questo nome completo.")
            return redirect("/utenti/")

        if nomeutenteInaf and PersonaleINAF.objects.filter(nomeutente=nomeutenteInaf).exists():
            messages.warning(request, "Esiste già un utente INAF con questo nome utente INAF.")
            return redirect("/utenti/")

        PersonaleINAF.objects.create(
            nominativo=nome_completo,
            nomeutente=nomeutenteInaf if nomeutenteInaf else None
        )
        messages.success(request, "Utente INAF aggiunto con successo.")
        log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Aggiunto utente INAF: {nome_completo}")
        log.save()
        return redirect("/utenti/")
    else:
        return redirect("/utenti/")

def rimuoviPersonaleINAF(request, personale_id):
    if request.user.is_staff:
        try:
            personale = PersonaleINAF.objects.get(id=personale_id)
            personale.delete()
            messages.success(request, "Utente INAF eliminato con successo.")
            log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Eliminato utente INAF: {personale.nominativo}")
            log.save()
        except PersonaleINAF.DoesNotExist:
            messages.warning(request, "Utente INAF non trovato.")
        return redirect("/utenti/")
    else:
        return redirect("/")

def modificaPersonaleINAF(request, personale_id):
    if request.method == "POST" and request.user.is_staff:
        nome_completo = request.POST.get("nome")
        nomeutenteInaf = request.POST.get("associated_username")

        try:
            personale = PersonaleINAF.objects.get(id=personale_id)
        except PersonaleINAF.DoesNotExist:
            messages.warning(request, "Utente INAF non trovato.")
            return redirect("/utenti/")

        if PersonaleINAF.objects.filter(nominativo=nome_completo).exclude(id=personale_id).exists():
            messages.warning(request, "Esiste già un utente INAF con questo nome completo.")
            return redirect("/utenti/")

        if nomeutenteInaf and PersonaleINAF.objects.filter(nomeutente=nomeutenteInaf).exclude(id=personale_id).exists():
            messages.warning(request, "Esiste già un utente INAF con questo nome utente INAF.")
            return redirect("/utenti/")

        personale.nominativo = nome_completo
        personale.nomeutente = nomeutenteInaf if nomeutenteInaf else None
        personale.save()

        messages.success(request, "Utente INAF aggiornato con successo.")
        log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Aggiornato utente INAF ID {personale_id}: {nome_completo}")
        log.save()
        return redirect("/utenti/")
    else:
        return redirect("/utenti/")

# --------------- Fine Gestione Utenti INAF ---------------


# --------------- Gestione Vigilanti ---------------

def aggiungiVigilante(request):
    if request.method == "POST" and request.user.is_staff:
        username = request.POST.get("username")
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        password = request.POST.get("password")
        
        if User.objects.filter(username=username).exists():
            messages.warning(request, "Esiste già un vigilante con questo username.")
            return redirect("/utenti/")

        User.objects.create_user(username=username, password=password, first_name=firstname, last_name=lastname, is_staff=False)
        messages.success(request, "Vigilante aggiunto con successo.")
        log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Aggiunto vigilante: {username}")
        log.save()
        return redirect("/utenti/")
    else:
        return redirect("/utenti/")

def rimuoviVigilante(request, vigilante_id):
    if request.user.is_staff:
        try:
            vigilante = User.objects.get(id=vigilante_id, is_staff=False)
            vigilante.delete()
            messages.success(request, "Vigilante eliminato con successo.")
            log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Eliminato vigilante: {vigilante.username}")
            log.save()
        except User.DoesNotExist:
            messages.warning(request, "Vigilante non trovato.")
        return redirect("/utenti/")
    else:
        return redirect("/utenti/")
    
def modificaVigilante(request, vigilante_id):
    if request.method == "POST" and request.user.is_staff:
        username = request.POST.get("username")
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        password = request.POST.get("password")

        try:
            vigilante = User.objects.get(id=vigilante_id, is_staff=False)
        except User.DoesNotExist:
            messages.warning(request, "Vigilante non trovato.")
            return redirect("/utenti/")

        if User.objects.filter(username=username).exclude(id=vigilante_id).exists():
            messages.warning(request, "Esiste già un vigilante con questo username.")
            return redirect("/utenti/")

        vigilante.username = username
        vigilante.first_name = firstname
        vigilante.last_name = lastname
        if password:
            vigilante.set_password(password)
        vigilante.save()

        messages.success(request, "Vigilante aggiornato con successo.")
        log = Log(timestamp=timezone.now(), utente=request.user, azione=f"Aggiornato vigilante ID {vigilante_id}: {username}")
        log.save()
        return redirect("/utenti/")
    else:
        return redirect("/utenti/")

# --------------- Fine Gestione Vigilanti ---------------

def logs(request):
    logs = Log.objects.all().order_by('-timestamp')
    users = User.objects.all()
    return render(request, 'areariservata/logs.html', {'logs': logs, 'users': users})

def esportaLogs(request):
    if request.method == "POST" and request.user.is_staff:
        data_inizio = parse_datetime(request.POST.get("date_start"))
        data_fine = parse_datetime(request.POST.get("date_end"))
        users = request.POST.get("user_select")
        
        logs = Log.objects.filter(
            timestamp__gte=data_inizio, 
            timestamp__lte=data_fine,
            **({} if users == "all" else {'utente__id': int(users)})
        ).order_by('timestamp')
            
        filename = f"logs_{data_inizio.strftime('%Y%m%d_%H%M')}_to_{data_fine.strftime('%Y%m%d_%H%M')}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Utente', 'Azione'])
        for log in logs:
            writer.writerow([
                timezone.localtime(log.timestamp),
                log.utente.username if log.utente else "N/A", 
                log.azione
            ])

        log_azione = f"Esportati log dal {data_inizio} al {data_fine}"
        Log.objects.create(timestamp=timezone.now(), utente=request.user, azione=log_azione)

        return response
    else:
        return redirect("logs")

def documenti(request):
    if request.method == "POST" and (request.user.is_staff or request.user.username == "centrale_operativa"):
        documento = request.FILES.get("file")
        descrizione = request.POST.get("descrizione", "")
        data_riferimento = request.POST.get("data_riferimento")
        tipo_documento = request.POST.get("tipo_documento")
        
        if tipo_documento == "fattura":
            Fattura.objects.create(
                file=documento,
                descrizione=descrizione,
                data_riferimento=data_riferimento,
                data_caricamento=timezone.now()
            )
            messages.success(request, "Fattura caricata con successo.")
            Log.objects.create(timestamp=timezone.now(), utente=request.user, azione=f"Caricata fattura {documento.name}")
        elif tipo_documento == "turno":
            Turni.objects.create(
                file=documento,
                descrizione=descrizione,
                data_riferimento=data_riferimento,
                data_caricamento=timezone.now()
            )
            messages.success(request, "Documento turno caricato con successo.")
            Log.objects.create(timestamp=timezone.now(), utente=request.user, azione=f"Caricato documento turni {documento.name}")
        else:
            messages.warning(request, "Tipo di documento non valido.")

        return redirect("/documenti/")
    report_Giornalieri = ReportGiornaliero.objects.all().order_by('-data_riferimento')
    report_Mensili = ReportMensile.objects.all().order_by('-data_riferimento')
    reports = sorted(
        list(report_Giornalieri) + list(report_Mensili),
        key=lambda x: x.data_riferimento, reverse=True
    )
    fatture = Fattura.objects.all().order_by('-data_riferimento')
    turni = Turni.objects.all().order_by('-data_riferimento')
    return render(request, 'areariservata/documenti.html', {'reports': reports, 'fatture': fatture, 'turni': turni})

def ricerca(request):
    if request.user.is_staff:
        custodi = User.objects.filter(is_staff=False).order_by('username').exclude(username='centrale_operativa')

        if request.method == "POST":
            tipo_ricerca = request.POST.get("data_type")
            custode = request.POST.get("custode")
            data_inizio = request.POST.get("start_date")
            data_fine = request.POST.get("end_date")

            registri = RegistroGiornaliero.objects.filter(
                data__range=[data_inizio, data_fine]
            ).order_by('data')
            
            turni_risultati = []
            accessi_risultati = []

            for registro in registri:
                if tipo_ricerca in ["turni", "all"]:
                    qs_turni = registro.turni.all()
                    if custode and custode != "tutti":
                        qs_turni = qs_turni.filter(vigilante__username=custode)
                    turni_risultati.extend(qs_turni)
                if tipo_ricerca in ["accessi", "all"]:
                    qs_accessi = registro.accessi.all()
                    if custode and custode != "tutti":
                        qs_accessi = qs_accessi.filter(turno__vigilante__username=custode)
                    accessi_risultati.extend(qs_accessi)

            if "generaPdf" in request.POST:
                if tipo_ricerca == "all":
                    return creaReportSearch(turni_risultati, accessi_risultati, data_inizio, data_fine)
                elif tipo_ricerca == "turni":
                    return creaReportSearch(turni_risultati, [], data_inizio, data_fine)
                elif tipo_ricerca == "accessi":
                    return creaReportSearch([], accessi_risultati, data_inizio, data_fine)
                return redirect("/search")

            context = {"custodi": custodi, "data_type": tipo_ricerca, "start_date": data_inizio, "end_date": data_fine, "custode": custode}
            if tipo_ricerca == "turni":
                context["turni"] = turni_risultati
            elif tipo_ricerca == "accessi":
                context["accessi"] = accessi_risultati
            elif tipo_ricerca == "all":
                context["turni"] = turni_risultati
                context["accessi"] = accessi_risultati

            return render(request, "areariservata/ricerca.html", context)

        return render(request, "areariservata/ricerca.html", { "custodi": custodi })
    else:
        return redirect("/")
    

def creaReport(data):
    datiRegistro = RegistroGiornaliero.objects.get(data=data)
    datiRegistro.turni.set(TurnoVigilanza.objects.filter(orario_inizio__date=data))
    datiRegistro.accessi.set(Accesso.objects.filter(oraIngresso__date=data))
    datiRegistro.save()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=3.5*cm, bottomMargin=3.3*cm)
    
    story = []
    
    styles = getSampleStyleSheet()
    INAF_BLUE = colors.Color(red=(2/255), green=(44/255), blue=(89/255))

    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=1*cm, textColor=INAF_BLUE))
    styles.add(ParagraphStyle(name='CustomH2', parent=styles['h2'], spaceAfter=0.3*cm, textColor=INAF_BLUE))
    styles.add(ParagraphStyle(name='TableCell', parent=styles['Normal'], alignment=1))
    styles.add(ParagraphStyle(name='TableCellWrap', parent=styles['Normal'], wordWrap='CJK'))

    titolo_data = datiRegistro.data.strftime('%d/%m/%Y')
    story.append(Paragraph(f"Registro di Vigilanza del {titolo_data}", styles['CustomTitle']))

    story.append(Paragraph("Personale esterno", styles['CustomH2']))
    
    accessi_data = [['Custode', 'Nominativi', 'Ditta', 'Ingresso', 'Uscita']]
    for accesso in datiRegistro.accessi.all().order_by('oraIngresso'):
        ora_ingresso = timezone.localtime(accesso.oraIngresso).strftime('%H:%M')
        ora_uscita = timezone.localtime(accesso.oraUscita).strftime('%H:%M') if accesso.oraUscita else 'In Corso'
        riga = [
            Paragraph(accesso.turno.vigilante.get_full_name(), styles['TableCell']),
            Paragraph(accesso.nominativi, styles['TableCellWrap']),
            Paragraph(accesso.ditta, styles['TableCell']),
            Paragraph(ora_ingresso, styles['TableCell']),
            Paragraph(ora_uscita, styles['TableCell'])
        ]
        accessi_data.append(riga)

    accessi_table = Table(accessi_data, colWidths=[4*cm, 5.5*cm, 4.5*cm, 2*cm, 2.5*cm])
    accessi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INAF_BLUE), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.ghostwhite), ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(accessi_table)
    story.append(Spacer(1, 1*cm))

    story.append(Paragraph("Lista turni", styles['CustomH2']))

    turni_data = [['Custode', 'Orario Inizio', 'Orario Fine']]
    for turno in datiRegistro.turni.all().order_by('-orario_inizio'):
        riga = [
            Paragraph(turno.vigilante.get_full_name(), styles['TableCell']),
            Paragraph((timezone.localtime(turno.orario_inizio)).strftime('%H:%M'), styles['TableCell']),
            Paragraph((timezone.localtime(turno.orario_fine)).strftime('%H:%M') if turno.orario_fine else 'Attivo', styles['TableCell'])
        ]
        turni_data.append(riga)
    
    turni_table = Table(turni_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    turni_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INAF_BLUE), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.ghostwhite), ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(turni_table)
    story.append(Spacer(1, 1.2*cm))

    story.append(PageBreak())
    
    personale_presente_list = []
    for presenza in datiRegistro.presenza_set.order_by('personale__nominativo'):
        nome = str(presenza.personale.nominativo)
        if presenza.is_present:
            personale_presente_list.append(nome)
        else:
            personale_presente_list.append(f"<strike>{nome}</strike>")
    personaleINAF_html = "<br/>".join(personale_presente_list)

    note_content = Paragraph(datiRegistro.note or 'Nessuna nota.', styles['TableCellWrap'])
    personale_content = Paragraph(personaleINAF_html or 'Nessun personale registrato.', styles['TableCellWrap'])
    
    note_personale_data = [
        [Paragraph('<b>Note</b>', styles['TableCell']), Paragraph('<b>Personale INAF</b>', styles['TableCell'])],
        [note_content, personale_content]
    ]
    note_personale_table = Table(note_personale_data, colWidths=[8.25*cm, 8.25*cm])
    note_personale_table.setStyle(TableStyle([
        ('VALIGN', (0,1), (-1,-1), 'TOP'), ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('BOTTOMPADDING', (0,1), (-1,-1), 8),
        ('TOPPADDING', (0,1), (-1,-1), 8), ('LEFTPADDING', (0,1), (-1,-1), 8),
        ('RIGHTPADDING', (0,1), (-1,-1), 8),
    ]))
    story.append(note_personale_table)

    def add_timestamp(canvas, doc):
        timestamp = timezone.localtime().strftime("Generato il %d/%m/%Y alle %H:%M")
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc.leftMargin, 3 * cm, timestamp)
        canvas.restoreState()

    doc.build(story, onFirstPage=add_timestamp, onLaterPages=add_timestamp)
    
    buffer.seek(0)
    return buffer


def unisciPDF(data):
    template_path = os.path.join('templates', 'areariservata', 'Carta-intestata-IRA-NUOVA-2023.pdf')
    template_reader = PdfReader(template_path)
    template_page = template_reader.pages[0]
    report_buffer = creaReport(data)
    report_reader = PdfReader(report_buffer)
    writer = PdfWriter()

    for page in report_reader.pages:
        page.merge_page(template_page)
        writer.add_page(page)

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer


def generaPDF(request):
    data = request.POST.get("data")
    pdf_buffer = unisciPDF(data)
    data_obj = timezone.datetime.strptime(data, '%Y-%m-%d').date()
    today_str = data_obj.strftime("%d-%m-%Y")
    filename = f"ReportServizioVigilanza_{today_str}.pdf"
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def creaReportSearch(turni=None, accessi=None, start=None, end=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=3.5*cm, bottomMargin=3.3*cm)
    
    story = []
    
    styles = getSampleStyleSheet()
    INAF_BLUE = colors.Color(red=(2/255), green=(44/255), blue=(89/255))

    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=1*cm, textColor=INAF_BLUE))
    styles.add(ParagraphStyle(name='CustomH2', parent=styles['h2'], spaceAfter=0.3*cm, textColor=INAF_BLUE))
    styles.add(ParagraphStyle(name='TableCell', parent=styles['Normal'], alignment=1))
    styles.add(ParagraphStyle(name='TableCellWrap', parent=styles['Normal'], wordWrap='CJK'))

    if accessi:
        story.append(Paragraph(f"Personale esterno dal {start} al {end}", styles['CustomH2']))
        
        accessi_data = [['Custode', 'Nominativi', 'Ditta', 'Ingresso', 'Uscita']]
        for accesso in accessi:
            ora_ingresso = timezone.localtime(accesso.oraIngresso).strftime('%H:%M')
            ora_uscita = timezone.localtime(accesso.oraUscita).strftime('%H:%M') if accesso.oraUscita else 'In Corso'
            riga = [
                Paragraph(accesso.turno.vigilante.get_full_name(), styles['TableCellWrap']),
                Paragraph(accesso.nominativi, styles['TableCellWrap']),
                Paragraph(accesso.ditta, styles['TableCellWrap']),
                Paragraph(ora_ingresso, styles['TableCell']),
                Paragraph(ora_uscita, styles['TableCell'])
            ]
            accessi_data.append(riga)

        accessi_table = Table(accessi_data, colWidths=[4*cm, 5.5*cm, 4.5*cm, 3.5*cm, 2*cm])
        accessi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), INAF_BLUE), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.ghostwhite), ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(accessi_table)
        story.append(Spacer(1, 1*cm))

        story.append(PageBreak())

    if turni:
        story.append(Paragraph(f"Lista turni dal {start} al {end}", styles['CustomH2']))

        turni_data = [['Data', 'Custode', 'Orario Inizio', 'Orario Fine']]
        for turno in turni:
            riga = [
                Paragraph(turno.data.strftime("%d/%m/%Y"), styles['TableCell']),
                Paragraph(turno.vigilante.get_full_name(), styles['TableCellWrap']),
                Paragraph((timezone.localtime(turno.orario_inizio)).strftime('%H:%M'), styles['TableCell']),
                Paragraph((timezone.localtime(turno.orario_fine)).strftime('%H:%M') if turno.orario_fine else 'Attivo', styles['TableCell'])
            ]
            turni_data.append(riga)
        
        turni_table = Table(turni_data, colWidths=[2.2*cm, 4*cm, 3*cm, 3*cm])
        turni_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), INAF_BLUE), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.ghostwhite), ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(turni_table)
        story.append(Spacer(1, 1.2*cm))

    def add_timestamp(canvas, doc):
        timestamp = timezone.localtime().strftime("Generato il %d/%m/%Y alle %H:%M")
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc.leftMargin, 3 * cm, timestamp)
        canvas.restoreState()

    doc.build(story, onFirstPage=add_timestamp, onLaterPages=add_timestamp)
    
    buffer.seek(0)

    template_path = os.path.join('templates', 'areariservata', 'Carta-intestata-IRA-NUOVA-2023.pdf')

    template_reader = PdfReader(template_path)
    template_page = template_reader.pages[0]

    report_buffer = buffer
    report_reader = PdfReader(report_buffer)

    writer = PdfWriter()

    for page in report_reader.pages:
        page.merge_page(template_page)
        writer.add_page(page)

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    pdf_buffer = output_buffer
    filename = "Report servizio di vigilanza " + timezone.localtime().strftime("%d%m%Y-%H%M") + ".pdf"
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def generaReportMensile(request, year, month):
    try:
        year = int(year)
        month = int(month)

        reports = ReportGiornaliero.objects.filter(
            data_riferimento__year=year, 
            data_riferimento__month=month
        ).order_by('data_riferimento')

        if not reports.exists():
            messages.warning(request, "Nessun report giornaliero trovato per il mese selezionato.")
            return redirect("documenti")

        merger = PdfWriter()
        files_count = 0

        for report in reports:
            try:
                if report.pdf and os.path.exists(report.pdf.path):
                    merger.append(report.pdf.path)
                    files_count += 1
            except Exception as e:
                print(f"Errore lettura file {report}: {e}")

        if files_count == 0:
            messages.warning(request, "Record trovati nel DB, ma i file PDF fisici risultano mancanti.")
            return redirect("documenti")

        output_buffer = BytesIO()
        merger.write(output_buffer)
        merger.close()
        
        output_buffer.seek(0)

        last_day = calendar.monthrange(year, month)[1]
        data_ref_mensile = date(year, month, last_day)
        
        month_name_eng = calendar.month_name[month]
        filename = f"Report_Mensile_{month_name_eng}_{year}.pdf"

        report_mensile, created = ReportMensile.objects.update_or_create(
            data_riferimento=data_ref_mensile,
            defaults={}
        )

        if report_mensile.pdf:
            report_mensile.pdf.delete(save=False)
            
        report_mensile.pdf.save(filename, ContentFile(output_buffer.getvalue()), save=True)

        action = "creato" if created else "aggiornato"
        messages.success(request, f"Report mensile di {month_name_eng} {year} {action} con successo.")
        
        return redirect("documenti")

    except Exception as e:
        messages.warning(request, f"Errore durante la generazione del report: {str(e)}")
        return redirect("documenti")