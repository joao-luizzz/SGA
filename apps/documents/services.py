import json
import re
import secrets

from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.crypto import salted_hmac

from academics.models import Aproveitamento, StatusAproveitamento
from accounts.models import AcaoAuditoria, CustomUser, UserRole
from accounts.services import registrar_auditoria
from assessments.selectors import SituacaoAcademica, calcular_resultado_academico
from enrollment.models import Matricula, StatusMatricula

from .models import DocumentoEmitido, TipoDocumento


SITUACOES_FINAIS = {
    SituacaoAcademica.APROVADO_DIRETO, SituacaoAcademica.APROVADO_EXAME,
    SituacaoAcademica.REPROVADO_NOTA, SituacaoAcademica.REPROVADO_FALTA,
}
SITUACOES_APROVADAS = {SituacaoAcademica.APROVADO_DIRETO, SituacaoAcademica.APROVADO_EXAME}
LIMITE_VERIFICACOES = 10
JANELA_VERIFICACOES = 60


def _decimal(valor):
    return None if valor is None else str(valor)


def _dados_aluno(aluno):
    return {'nome': aluno.full_name, 'email': aluno.email}


def _conteudo_declaracao(aluno):
    if not aluno.is_active:
        raise ValidationError("A declaração só pode ser emitida para aluno ativo.")
    matriculas = (
        Matricula.objects.filter(aluno=aluno, status=StatusMatricula.ATIVA)
        .select_related('turma__disciplina__curso')
        .order_by('turma__periodo_letivo', 'turma__disciplina__nome')
    )
    itens = [{
        'disciplina': m.turma.disciplina.nome,
        'codigo': m.turma.disciplina.codigo,
        'curso': m.turma.disciplina.curso.nome,
        'periodo': m.turma.periodo_letivo,
        'carga_horaria': m.turma.disciplina.carga_horaria,
    } for m in matriculas]
    if not itens:
        raise ValidationError("O aluno não possui matrícula ativa; a declaração não pode ser emitida.")
    return {'aluno': _dados_aluno(aluno), 'matriculas': itens}


def _conteudo_historico(aluno):
    matriculas = (
        Matricula.objects.filter(aluno=aluno)
        .exclude(status=StatusMatricula.CANCELADA)
        .select_related('aluno', 'turma__disciplina__curso')
        .order_by('turma__periodo_letivo', 'turma__disciplina__nome')
    )
    disciplinas, carga = [], 0
    for matricula in matriculas:
        resultado = calcular_resultado_academico(matricula)
        if resultado['situacao'] not in SITUACOES_FINAIS:
            continue
        disciplina = matricula.turma.disciplina
        if resultado['situacao'] in SITUACOES_APROVADAS:
            carga += disciplina.carga_horaria
        disciplinas.append({
            'disciplina': disciplina.nome,
            'codigo': disciplina.codigo,
            'curso': disciplina.curso.nome,
            'carga_horaria': disciplina.carga_horaria,
            'periodo': matricula.turma.periodo_letivo,
            'media_parcial': _decimal(resultado['media_parcial']),
            'media_final': _decimal(resultado['media_final']),
            'frequencia': _decimal(resultado['frequencia']['percentual']),
            'situacao': resultado['situacao'],
        })

    aproveitamentos = []
    for item in (
        Aproveitamento.objects.filter(aluno=aluno, status=StatusAproveitamento.DEFERIDO)
        .select_related('disciplina').order_by('disciplina__nome')
    ):
        carga += item.disciplina.carga_horaria
        aproveitamentos.append({
            'disciplina': item.disciplina.nome,
            'codigo': item.disciplina.codigo,
            'carga_horaria': item.disciplina.carga_horaria,
            'instituicao_origem': item.instituicao_origem,
            'disciplina_origem': item.disciplina_origem,
        })
    return {
        'aluno': _dados_aluno(aluno),
        'disciplinas': disciplinas,
        'aproveitamentos': aproveitamentos,
        'carga_horaria_integralizada': carga,
    }


def _novo_codigo():
    while True:
        codigo = secrets.token_hex(8).upper()
        if not DocumentoEmitido.objects.filter(codigo_verificacao=codigo).exists():
            return codigo


@transaction.atomic
def emitir_documento(*, usuario, aluno, tipo):
    """Aluno emite os próprios documentos; Secretaria emite para qualquer aluno (RN22)."""
    if not getattr(usuario, 'is_authenticated', False) or not usuario.is_active:
        raise PermissionDenied("Autentique-se para emitir documentos.")
    if not usuario.is_superuser:
        if usuario.role == UserRole.ALUNO and usuario.pk != aluno.pk:
            raise PermissionDenied("O aluno só pode emitir os próprios documentos.")
        if usuario.role not in (UserRole.ALUNO, UserRole.SECRETARIA):
            raise PermissionDenied("Seu perfil não pode emitir documentos.")
    if tipo not in TipoDocumento.values:
        raise ValidationError("Tipo de documento inválido.")

    aluno = CustomUser.objects.get(pk=aluno.pk)
    if aluno.role != UserRole.ALUNO:
        raise ValidationError("Documentos só podem ser emitidos para alunos.")
    conteudo = (
        _conteudo_declaracao(aluno) if tipo == TipoDocumento.DECLARACAO else _conteudo_historico(aluno)
    )
    documento = DocumentoEmitido.objects.create(
        aluno=aluno, tipo=tipo, codigo_verificacao=_novo_codigo(),
        conteudo=conteudo, emitido_por=usuario,
    )
    registrar_auditoria(
        usuario=usuario, tabela_afetada='DocumentoEmitido', registro_id=documento.pk,
        acao=AcaoAuditoria.CRIAR,
        valor_novo=json.dumps({'tipo': tipo, 'aluno_id': aluno.pk,
                               'codigo_verificacao': documento.codigo_verificacao}),
    )
    return documento


def mascarar_nome(nome):
    partes = (nome or '').split()
    if not partes:
        return ''
    return ' '.join([partes[0]] + [parte[0].upper() + '.' for parte in partes[1:]])


def normalizar_codigo(codigo):
    return re.sub(r'[^0-9A-Fa-f]', '', codigo or '').upper()


def verificar_documento(*, codigo, ip):
    """Verificação pública (RN23): limita tentativas por IP e não expõe dados acadêmicos.

    Retorna None para código inválido, inexistente ou excesso de tentativas, para
    que a resposta pública seja a mesma nos três casos.
    """
    chave = 'documentos:verificacao:' + salted_hmac('sga-documentos-verificacao', ip or '').hexdigest()
    cache.add(chave, 0, JANELA_VERIFICACOES)
    try:
        tentativas = cache.incr(chave)
    except ValueError:
        cache.set(chave, 1, JANELA_VERIFICACOES)
        tentativas = 1
    if tentativas > LIMITE_VERIFICACOES:
        return None

    codigo = normalizar_codigo(codigo)
    if len(codigo) != 16:
        return None
    documento = (
        DocumentoEmitido.objects.select_related('aluno')
        .filter(codigo_verificacao=codigo).first()
    )
    if documento is None:
        return None
    return {
        'tipo': documento.get_tipo_display(),
        'emitido_em': documento.emitido_em,
        'aluno': mascarar_nome(documento.aluno.full_name),
        'codigo': documento.codigo_formatado,
    }
