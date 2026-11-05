import json
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from .models import Group, Room

@login_required
def selecao_turma(request):
    # Busca se o guia já possui alguma turma ativa em visitação
    turma_atual = Group.objects.filter(current_guide=request.user, status='em_visitacao').first()

    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        try:
            with transaction.atomic():
                # Valida se o usuário já possui outra turma em andamento de forma atômica
                if Group.objects.select_for_update().filter(current_guide=request.user, status='em_visitacao').exists():
                    messages.error(request, 'Você já está conduzindo uma turma. Encerre a visitação antes de assumir outra.')
                    return redirect('selecao_turma')

                group = Group.objects.select_for_update().get(pk=group_id)
                
                if group.status != 'disponivel' or group.current_guide_id is not None:
                    messages.error(request, 'Esta turma não está disponível. Atualize a página e tente outra.')
                    return redirect('selecao_turma')
                
                # Atribui a turma ao guia
                group.status, group.current_guide = 'em_visitacao', request.user
                group.save(update_fields=['status', 'current_guide'])
                return redirect('mapa')
                
        except (Group.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Turma inválida. Selecione uma turma disponível.')
        except IntegrityError:
            messages.error(request, 'Conflito ao assumir a turma. Atualize e tente novamente.')
            
    groups = Group.objects.all().order_by('name')
    return render(request, 'visitas/selecao_turma.html', {'groups': groups, 'turma_atual': turma_atual})

@login_required
def mapa(request):
    group = Group.objects.filter(current_guide=request.user, status='em_visitacao').first()
    if group is None:
        messages.info(request, 'Assuma uma turma disponível para abrir o mapa.')
        return redirect('selecao_turma')
    rooms = Room.objects.all().order_by('name')
    return render(request, 'visitas/mapa.html', {'group': group, 'rooms': rooms})

@login_required
@require_POST
def encerrar_visitacao(request):
    with transaction.atomic():
        group = Group.objects.select_for_update().filter(current_guide=request.user, status='em_visitacao').first()
        if group is None:
            messages.info(request, 'Você não possui uma visitação ativa.')
            return redirect('selecao_turma')
        Room.objects.select_for_update().filter(current_group=group).update(status='livre', current_group=None, occupied_at=None)
        group.status, group.current_guide = 'concluida', None
        group.save(update_fields=['status', 'current_guide'])
    messages.success(request, f'Visitação de {group.name} encerrada; salas ocupadas foram liberadas.')
    return redirect('selecao_turma')
@login_required
@require_POST
def api_toggle_room(request, room_id):
    try:
        room_id = int(room_id)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Sala inválida.'}, status=400)
        
    with transaction.atomic():
        group = Group.objects.select_for_update().filter(current_guide=request.user, status='em_visitacao').first()
        if group is None:
            return JsonResponse({'error': 'Nenhuma turma ativa vinculada ao guia.'}, status=409)
            
        room = get_object_or_404(Room.objects.select_for_update(), pk=room_id)
        
        # Se a sala já está ocupada por OUTRA turma, bloqueia
        if room.status == 'ocupada' and room.current_group_id != group.id:
            return JsonResponse({'error': 'Esta sala está ocupada por outra turma.'}, status=403)
            
        # Se a sala já é da própria turma, significa que ele quer LIBERAR a sala
        if room.status == 'ocupada' and room.current_group_id == group.id:
            room.status, room.current_group, room.occupied_at = 'livre', None, None
            
        # Se a sala está LIVRE, ele quer ocupar. TRAVA DE SEGURANÇA: A turma já tem outra sala ocupada?
        else:
            sala_ocupada_existente = Room.objects.filter(current_group=group, status='ocupada').exclude(pk=room.pk).exists()
            if sala_ocupada_existente:
                return JsonResponse({
                    'error': 'Sua turma já possui uma sala ocupada! Libere a sala atual antes de ocupar outra.'
                }, status=400)
                
            # Se não tiver nenhuma outra ocupada, libera para ocupar esta
            room.status, room.current_group, room.occupied_at = 'ocupada', group, timezone.now()
            room.visit_count += 1
            
        room.save(update_fields=['status', 'current_group', 'occupied_at', 'visit_count'])
        
    return JsonResponse(room_payload(room))
def room_payload(room):
    return {
        'id': room.id, 
        'name': room.name, 
        'status': room.status, 
        'status_label': room.get_status_display(), 
        'current_group': room.current_group.name if room.current_group else None, 
        'occupied_at': room.occupied_at.isoformat() if room.occupied_at else None, 
        'visit_count': room.visit_count, 
        'x_position': room.x_position, 
        'y_position': room.y_position
    }

@login_required
@require_GET
def api_polling(request):
    return JsonResponse({
        'server_time': timezone.now().isoformat(), 
        'rooms': [room_payload(r) for r in Room.objects.select_related('current_group').all().order_by('id')]
    })