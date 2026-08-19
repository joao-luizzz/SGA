from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academics', '0002_turma'),
        ('enrollment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Falta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_aula', models.DateField(verbose_name='data da aula')),
                ('presente', models.BooleanField(
                    help_text='Marque se o aluno esteve presente nesta aula.',
                    verbose_name='presente',
                )),
                ('registrado_em', models.DateTimeField(auto_now_add=True, verbose_name='registrado em')),
                ('aluno', models.ForeignKey(
                    limit_choices_to={'role': 'ALUNO'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='faltas',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='aluno',
                )),
                ('registrado_por', models.ForeignKey(
                    blank=True,
                    limit_choices_to={'role': 'PROFESSOR'},
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='chamadas_registradas',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='registrado por',
                )),
                ('turma', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='faltas',
                    to='academics.turma',
                    verbose_name='turma',
                )),
            ],
            options={
                'verbose_name': 'registro de frequência',
                'verbose_name_plural': 'registros de frequência',
                'ordering': ['-data_aula', 'aluno__full_name'],
            },
        ),
        migrations.AddConstraint(
            model_name='falta',
            constraint=models.UniqueConstraint(
                fields=['turma', 'aluno', 'data_aula'],
                name='unique_chamada_por_aula',
            ),
        ),
    ]
