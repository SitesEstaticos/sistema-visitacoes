from django.core.management.base import BaseCommand
from visitas.models import Group, Room

class Command(BaseCommand):
    help = 'Cria turmas e salas de exemplo, sem duplicar registros.'

    def handle(self, *args, **options):
        for i in range(1, 6):
            Group.objects.get_or_create(name=f'Turma {i:02d}')
        rooms = [('Recepção', 10, 15), ('Laboratório de Física', 40, 25), ('Laboratório de Química', 75, 30), ('Auditório', 30, 65), ('Biblioteca', 70, 75)]
        for name, x, y in rooms:
            Room.objects.get_or_create(name=name, defaults={'x_position': x, 'y_position': y})
        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados. Crie guias com createsuperuser ou no admin.'))
