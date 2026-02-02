# Generated manually for StudentProfile model

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ai', '0002_airesponselog_user_feedback'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zdp_level', models.CharField(
                    choices=[
                        ('autonomous', 'Autónomo'),
                        ('minimal_support', 'Apoio mínimo'),
                        ('intermediate', 'Apoio intermédio'),
                        ('substantial_support', 'Apoio substancial'),
                        ('intensive', 'Apoio intensivo'),
                    ],
                    default='intermediate',
                    help_text='Nível atual de apoio na ZDP',
                    max_length=20,
                )),
                ('learning_preferences', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Preferências de aprendizagem: visual, auditiva, cinestésica, etc.',
                )),
                ('collaboration_success_rate', models.FloatField(
                    default=0.5,
                    help_text='Taxa de sucesso em trabalhos colaborativos (0-1)',
                )),
                ('strengths', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Lista de áreas fortes: ["matemática", "leitura", ...]',
                )),
                ('growth_areas', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Lista de áreas a desenvolver',
                )),
                ('total_interactions', models.PositiveIntegerField(default=0)),
                ('successful_scaffolds', models.PositiveIntegerField(
                    default=0,
                    help_text='Vezes em que o scaffolding nível 1-2 foi suficiente',
                )),
                ('needed_full_support', models.PositiveIntegerField(
                    default=0,
                    help_text='Vezes em que precisou de nível 3 (resposta completa)',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_student_profile',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('preferred_collaborators', models.ManyToManyField(
                    blank=True,
                    help_text='Colegas com quem trabalha bem',
                    related_name='collaboration_partners',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Perfil de Aluno (IA)',
                'verbose_name_plural': 'Perfis de Alunos (IA)',
            },
        ),
    ]
