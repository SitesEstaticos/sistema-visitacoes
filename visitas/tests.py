from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Group, Room

class VisitationFlowTests(TestCase):
    def setUp(self):
        self.guide = User.objects.create_user(username='guia', password='senha-forte-123')
        self.other = User.objects.create_user(username='outro', password='senha-forte-123')
        self.group = Group.objects.create(name='Turma 01', status='em_visitacao', current_guide=self.guide)
        self.room = Room.objects.create(name='Laboratório A', x_position=30, y_position=40)
        self.client.force_login(self.guide)

    def test_toggle_occupy_and_release_tracks_metrics(self):
        response = self.client.post(reverse('api_toggle_room', args=[self.room.pk]))
        self.assertEqual(response.status_code, 200)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'ocupada')
        self.assertEqual(self.room.current_group, self.group)
        self.assertEqual(self.room.visit_count, 1)
        self.assertIsNotNone(self.room.occupied_at)
        response = self.client.post(reverse('api_toggle_room', args=[self.room.pk]))
        self.assertEqual(response.status_code, 200)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'livre')
        self.assertIsNone(self.room.occupied_at)
        self.assertEqual(self.room.visit_count, 1)

    def test_map_screen_renders_panzoom_and_map_markers(self):
        response = self.client.get(reverse('mapa'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panzoom')
        self.assertContains(response, 'INSERIR IMAGEM DO MAPA DA SNCT AQUI')
        self.assertContains(response, 'X e Y são percentuais')
        self.assertContains(response, 'setInterval(poll,5000)')

    def test_foreign_group_cannot_release_room(self):
        self.room.status, self.room.current_group, self.room.occupied_at = 'ocupada', Group.objects.create(name='Turma 02', status='em_visitacao', current_guide=self.other), timezone.now()
        self.room.save()
        response = self.client.post(reverse('api_toggle_room', args=[self.room.pk]))
        self.assertEqual(response.status_code, 403)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'ocupada')

    def test_end_visit_releases_all_group_rooms(self):
        self.room.status, self.room.current_group, self.room.occupied_at = 'ocupada', self.group, timezone.now() - timedelta(minutes=20)
        self.room.save()
        response = self.client.post(reverse('encerrar_visitacao'))
        self.assertEqual(response.status_code, 302)
        self.room.refresh_from_db(); self.group.refresh_from_db()
        self.assertEqual(self.room.status, 'livre')
        self.assertIsNone(self.room.current_group)
        self.assertIsNone(self.room.occupied_at)
        self.assertEqual(self.group.status, 'concluida')
        self.assertIsNone(self.group.current_guide)

    def test_only_available_group_can_be_assumed(self):
        free = Group.objects.create(name='Turma 03')
        response = self.client.post(reverse('selecao_turma'), {'group_id': free.pk})
        self.assertEqual(response.status_code, 200)
        free.refresh_from_db()
        self.assertIsNone(free.current_guide)
        # Um guia não pode assumir uma segunda turma enquanto mantém a primeira ativa.

class AdminEmergencyActionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='senha-forte-123', email='admin@example.com')
        self.group = Group.objects.create(name='Turma Emergência', status='em_visitacao', current_guide=User.objects.create_user(username='guia-admin'))
        self.room = Room.objects.create(name='Sala Emergência', status='ocupada', current_group=self.group, x_position=10, y_position=10, occupied_at=timezone.now())
        self.client.force_login(self.admin)

    def test_group_force_release_cleans_group_and_linked_rooms(self):
        response = self.client.post('/admin/visitas/group/', {'action': 'force_release_group', '_selected_action': [self.group.pk]})
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db(); self.room.refresh_from_db()
        self.assertEqual(self.group.status, 'disponivel')
        self.assertIsNone(self.group.current_guide)
        self.assertEqual(self.room.status, 'livre')
        self.assertIsNone(self.room.current_group)
        self.assertIsNone(self.room.occupied_at)

    def test_room_force_release_clears_room_state(self):
        response = self.client.post('/admin/visitas/room/', {'action': 'force_release_room', '_selected_action': [self.room.pk]})
        self.assertEqual(response.status_code, 302)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'livre')
        self.assertIsNone(self.room.current_group)
        self.assertIsNone(self.room.occupied_at)
