from django.conf import settings
from django.db import models

class Group(models.Model):
    STATUS_CHOICES = [('disponivel', 'Disponível'), ('em_visitacao', 'Em Visitação'), ('concluida', 'Concluída')]
    name = models.CharField('Nome da turma', max_length=50, unique=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='disponivel', db_index=True)
    current_guide = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_group', verbose_name='Guia atual')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['current_guide'], condition=models.Q(status='em_visitacao', current_guide__isnull=False), name='one_active_group_per_guide')]

    def __str__(self):
        return f'{self.name} - {self.get_status_display()}'

class Room(models.Model):
    STATUS_CHOICES = [('livre', 'Livre'), ('ocupada', 'Ocupada')]
    name = models.CharField('Nome da sala', max_length=50, unique=True)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='livre', db_index=True)
    current_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='rooms', verbose_name='Turma atual')
    x_position = models.FloatField('Posição X (%)', help_text='Porcentagem horizontal sobre a imagem do mapa (0 a 100).')
    y_position = models.FloatField('Posição Y (%)', help_text='Porcentagem vertical sobre a imagem do mapa (0 a 100).')
    visit_count = models.PositiveIntegerField('Total de visitas recebidas', default=0)
    occupied_at = models.DateTimeField('Ocupada desde', null=True, blank=True)

    def __str__(self):
        return f'{self.name} - {self.get_status_display()}'
