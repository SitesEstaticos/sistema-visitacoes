from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from .models import Group, Room

@admin.action(description='Desvincular guia e disponibilizar turma (emergência)')
def force_release_group(modeladmin, request, queryset):
    released = 0
    with transaction.atomic():
        for group in queryset.select_for_update():
            Room.objects.filter(current_group=group).update(status='livre', current_group=None, occupied_at=None)
            group.status, group.current_guide = 'disponivel', None
            group.save(update_fields=['status', 'current_guide'])
            released += 1
    messages.success(request, f'{released} turma(s) liberada(s); salas ocupadas vinculadas foram limpas.')

@admin.action(description='Forçar liberação de sala (emergência)')
def force_release_room(modeladmin, request, queryset):
    with transaction.atomic():
        count = queryset.select_for_update().update(status='livre', current_group=None, occupied_at=None)
    messages.success(request, f'{count} sala(s) liberada(s) com sucesso.')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'current_guide')
    list_filter = ('status',)
    search_fields = ('name', 'current_guide__username')
    actions = (force_release_group,)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'current_group', 'visit_count', 'occupied_at')
    list_filter = ('status',)
    readonly_fields = ('visit_count', 'occupied_at')
    search_fields = ('name',)
    actions = (force_release_room,)
    fieldsets = (('Sala e coordenadas no mapa', {'fields': ('name', 'status', 'current_group', 'x_position', 'y_position'), 'description': 'X e Y são porcentagens de 0 a 100% relativas à imagem do mapa; ajuste a posição dos marcadores por aqui.'}), ('Métricas (somente leitura)', {'fields': ('visit_count', 'occupied_at')}))
