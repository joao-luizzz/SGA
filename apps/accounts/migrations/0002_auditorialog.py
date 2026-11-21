from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditoriaLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tabela_afetada', models.CharField(
                    help_text='Nome da entidade alterada, ex.: Nota ou Falta.',
                    max_length=50,
                    verbose_name='tabela afetada',
                )),
                ('registro_id', models.BigIntegerField(verbose_name='ID do registro')),
                ('acao', models.CharField(
                    choices=[('CRIAR', 'Criar'), ('EDITAR', 'Editar'), ('EXCLUIR', 'Excluir')],
                    max_length=10,
                    verbose_name='ação',
                )),
                ('valor_antigo', models.TextField(blank=True, null=True, verbose_name='valor anterior')),
                ('valor_novo', models.TextField(blank=True, null=True, verbose_name='novo valor')),
                ('realizado_em', models.DateTimeField(auto_now_add=True, verbose_name='realizado em')),
                ('usuario', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='logs_auditoria',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='usuário responsável',
                )),
            ],
            options={
                'verbose_name': 'log de auditoria',
                'verbose_name_plural': 'logs de auditoria',
                'ordering': ['-realizado_em'],
                'default_permissions': ('add', 'view'),
            },
        ),
    ]
