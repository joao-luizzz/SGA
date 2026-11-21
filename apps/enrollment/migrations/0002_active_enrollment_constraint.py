from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='matricula',
            name='unique_aluno_turma',
        ),
        migrations.AddConstraint(
            model_name='matricula',
            constraint=models.UniqueConstraint(
                condition=models.Q(status='ATIVA'),
                fields=('aluno', 'turma'),
                name='unique_matricula_ativa_aluno_turma',
            ),
        ),
    ]
