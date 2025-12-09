from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('cambiaPassword/', views.cambiaPassword, name='cambiaPassword'),

    path('aggiornaRegistro/', views.aggiornaRegistroVigilanza, name='aggiornaRegistro'),

    path('registraAccesso/<int:turno_id>/', views.registraAccesso, name='registraAccesso'),
    path('aggiornaAccesso/<int:accesso_id>/', views.aggiornaAccesso, name='aggiornaAccesso'),
    path('eliminaAccesso/<int:accesso_id>/', views.eliminaAccesso, name='eliminaAccesso'),

    path('mkdfnj4uNDSnmD348DAHsd/', views.telegramWebhook, name='telegramWebhook'),
]