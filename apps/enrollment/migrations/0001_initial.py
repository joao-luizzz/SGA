from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academics', '0002_turma'),
    ]

    operations = [
        migrations.CreateModel(
            name='Matricula',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('ATIVA', 'Ativa'),
                        ('TRANCADA', 'Trancada'),
                        ('CONCLUIDA', 'Concluída'),
                        ('CANCELADA', 'Cancelada'),
                    ],
                    default='ATIVA',
                    max_length=20,
                    verbose_name='status',
                )),
                ('matriculado_em', models.DateTimeField(auto_now_add=True, verbose_name='matriculado em')),
                ('aluno', models.ForeignKey(
                    limit_choices_to={'role': 'ALUNO'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='matriculas',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='aluno',
                )),
                ('turma', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='matriculas',
                    to='academics.turma',
                    verbose_name='turma',
                )),
            ],
            options={
                'verbose_name': 'matrícula',
                'verbose_name_plural': 'matrículas',
                'ordering': ['-matriculado_em'],
            },
        ),
        migrations.AddConstraint(
            model_name='matricula',
            constraint=models.UniqueConstraint(
                fields=['aluno', 'turma'],
                name='unique_aluno_turma',
            ),
        ),
    ]
