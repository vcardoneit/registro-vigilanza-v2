from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('impostazioni/', views.impostazioni, name='impostazioni'),
    
    path('utenti/', views.utenti, name='utenti'),

    path('personaleINAF/add/', views.aggiungiPersonaleINAF, name='aggiungiPersonaleINAF'),
    path('personaleINAF/delete/<int:personale_id>/', views.rimuoviPersonaleINAF, name='rimuoviPersonaleINAF'),
    path('personaleINAF/edit/<int:personale_id>/', views.modificaPersonaleINAF, name='modificaPersonaleINAF'),

    path('vigilanti/add/', views.aggiungiVigilante, name='aggiungiVigilante'),
    path('vigilanti/delete/<int:vigilante_id>/', views.rimuoviVigilante, name='rimuoviVigilante'),
    path('vigilanti/edit/<int:vigilante_id>/', views.modificaVigilante, name='modificaVigilante'),

    path('logs/', views.logs, name='logs'),
    path('logs/export/', views.esportaLogs, name='esportaLogs'),

    path('documenti/', views.documenti, name='documenti'),

    path('ricerca/', views.ricerca, name='ricerca'),

    path('report/genera/', views.generaPDF, name='generaPDF'),
]