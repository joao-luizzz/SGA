from django.conf import settings
from django.db import models


class TipoNotificacao(models.TextChoices):
    COMUNICADO = 'COMUNICADO', 'Comunicado'
    NOTA = 'NOTA', 'Nota'
    FREQUENCIA = 'FREQUENCIA', 'Frequência'


class Notificacao(models.Model):
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=20, choices=TipoNotificacao.choices)
    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)
    comunicado = models.ForeignKey(
        'communications.Comunicado', null=True, blank=True, on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['-criada_em', '-pk']
        constraints = [models.UniqueConstraint(
            fields=['destinatario', 'comunicado'], name='notificacao_comunicado_destinatario_unico',
        )]
        indexes = [models.Index(
            fields=['destinatario', 'lida_em', '-criada_em'], name='notif_usuario_leitura_idx',
        )]

    @property
    def lida(self):
        return self.lida_em is not None
