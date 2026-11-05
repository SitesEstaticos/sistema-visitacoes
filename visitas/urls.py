from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='visitas/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('turmas/', views.selecao_turma, name='selecao_turma'),
    path('mapa/', views.mapa, name='mapa'),
    path('visita/encerrar/', views.encerrar_visitacao, name='encerrar_visitacao'),
    path('api/salas/', views.api_polling, name='api_polling'),
    path('api/salas/<int:room_id>/alternar/', views.api_toggle_room, name='api_toggle_room'),
]
