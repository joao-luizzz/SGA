"""Roteiro final de demonstração (SGA-07) percorrido via HTTP sobre os dados do seed_demo."""
from io import StringIO

import pytest
from django.core.management import call_command
from datetime import timedelta

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from academics.models import Aproveitamento, Disciplina, Turma
from accounts.models import CustomUser
from documents.models import DocumentoEmitido
from enrollment.models import Matricula
from finance.models import Cobranca

SENHA = 'SgaDemo2026!'


def entrar(email):
    c = Client()
    r = c.post(reverse('accounts:login'), {'username': email, 'password': SENHA})
    assert r.status_code == 302, f'login falhou para {email}: {r.status_code}'
    return c


def status(c, nome, *args, metodo='get', dados=None, **query):
    url = reverse(nome, args=args)
    r = getattr(c, metodo)(url, dados or query)
    return r.status_code, r


@pytest.mark.django_db
def test_roteiro_final_da_demonstracao():
    call_command('seed_demo', password=SENHA, stdout=StringIO())
    resultados = []

    def passo(numero, descricao, ok, detalhe=''):
        resultados.append((numero, descricao, ok, detalhe))

    coord = entrar('coordenacao.demo@sga.edu.br')
    secre = entrar('secretaria.demo@sga.edu.br')
    prof = entrar('professor.demo@sga.edu.br')
    aprovado = entrar('aluno.aprovado@sga.edu.br')
    exame = entrar('aluno.exame@sga.edu.br')
    falta = entrar('aluno.falta@sga.edu.br')
    anon = Client()

    u = {e: CustomUser.objects.get(email=e) for e in (
        'aluno.aprovado@sga.edu.br', 'aluno.exame@sga.edu.br', 'aluno.falta@sga.edu.br')}
    banco = Disciplina.objects.get(codigo='BD-DEMO')
    engenharia = Disciplina.objects.get(codigo='ES-DEMO')
    turma_bd = Turma.objects.get(disciplina=banco)

    # 1. Catálogo e grade
    s1, _ = status(coord, 'academics:index')
    s2, _ = status(coord, 'academics:grade_horaria')
    passo(1, 'Coordenação: catálogo e grade horária', s1 == s2 == 200, f'{s1}/{s2}')

    # 2. Pré-requisitos e ciclo recusado
    s, r = status(coord, 'academics:pre_requisitos', banco.pk)
    tem = 'Engenharia de Software' in r.content.decode()
    s_ciclo, r_ciclo = status(coord, 'academics:pre_requisitos', engenharia.pk, metodo='post',
                              dados={'requisito': banco.pk})
    passo(2, 'Coordenação: pré-requisito visível e ciclo recusado',
          s == 200 and tem and s_ciclo == 200 and 'ciclo' in r_ciclo.content.decode(),
          f'tela {s}, ciclo {s_ciclo}')

    # 3. Matrícula com pré-requisito
    s_ok, _ = status(secre, 'enrollment:matricula_create', metodo='post',
                     dados={'aluno': u['aluno.aprovado@sga.edu.br'].pk, 'turma': turma_bd.pk})
    s_bloq, r_bloq = status(secre, 'enrollment:matricula_create', metodo='post',
                            dados={'aluno': u['aluno.falta@sga.edu.br'].pk, 'turma': turma_bd.pk})
    ok_mat = Matricula.objects.filter(aluno=u['aluno.aprovado@sga.edu.br'], turma=turma_bd).exists()
    bloq = not Matricula.objects.filter(aluno=u['aluno.falta@sga.edu.br'], turma=turma_bd).exists()
    passo(3, 'Secretaria: aprovado matriculado; reprovado por falta bloqueado',
          ok_mat and bloq and 'pré-requisitos' in r_bloq.content.decode(), f'{s_ok}/{s_bloq}')

    # 4. Professor
    s1, _ = status(prof, 'assessments:index')
    s2, _ = status(prof, 'attendance:chamada_index')
    passo(4, 'Professor: turmas, notas e chamada', s1 == s2 == 200, f'{s1}/{s2}')

    # 5. Aluno do exame
    telas = [status(exame, n)[0] for n in ('assessments:index', 'attendance:boletim_frequencia',
                                            'notifications:central', 'academics:aproveitamento_index')]
    _, r = status(exame, 'academics:aproveitamento_index')
    passo(5, 'Aluno: boletim, frequência, notificações e aproveitamento pendente',
          all(t == 200 for t in telas) and 'Lógica' in r.content.decode(), str(telas))

    # 6. Deferir aproveitamento
    apr = Aproveitamento.objects.get(aluno=u['aluno.exame@sga.edu.br'])
    s, _ = status(coord, 'academics:aproveitamento_analisar', apr.pk, metodo='post',
                  dados={'decisao': 'DEFERIDO', 'justificativa': 'Ementa equivalente (validação).'})
    apr.refresh_from_db()
    passo(6, 'Coordenação: aproveitamento deferido', s == 302 and apr.status == 'DEFERIDO', str(s))

    # 7. Histórico pelo aluno
    s, r = status(aprovado, 'documents:emitir', metodo='post', dados={'tipo': 'HISTORICO'})
    doc = DocumentoEmitido.objects.filter(aluno=u['aluno.aprovado@sga.edu.br']).first()
    _, r_det = status(aprovado, 'documents:detalhe', doc.pk) if doc else (None, None)
    passo(7, 'Aluno: histórico emitido e imprimível',
          s == 302 and doc is not None and 'Engenharia de Software' in r_det.content.decode(),
          doc.codigo_formatado if doc else 'sem documento')

    # 8. Verificação pública
    s, r = status(anon, 'documents:verificar', codigo=doc.codigo_formatado)
    html = r.content.decode()
    passo(8, 'Visitante: código verificado, nome mascarado, sem notas',
          s == 200 and 'Documento autêntico' in html and 'Aluno A.' in html and '8.00' not in html, str(s))

    # 9. Financeiro da Secretaria
    cobrancas = list(Cobranca.objects.filter(aluno=u['aluno.aprovado@sga.edu.br']).order_by('vencimento'))
    atrasada, futura = cobrancas
    _, r = status(secre, 'finance:index', status='ATRASO')
    s_pag, _ = status(secre, 'finance:pagar', atrasada.pk, metodo='post')
    s_can, _ = status(secre, 'finance:cancelar', futura.pk, metodo='post',
                      dados={'justificativa': 'Cancelamento de validação.'})
    atrasada.refresh_from_db(); futura.refresh_from_db()
    passo(9, 'Secretaria: atraso listado, pagamento e cancelamento',
          'Mensalidade' in r.content.decode() and atrasada.status == 'PAGA' and futura.status == 'CANCELADA',
          f'{s_pag}/{s_can}')

    # 10. Extrato do aluno e isolamento
    s, _ = status(aprovado, 'finance:index')
    outra = Cobranca.objects.create(aluno=u['aluno.falta@sga.edu.br'], competencia='2026-12', descricao='Taxa validação',
                                    valor=10, vencimento=timezone.localdate() + timedelta(days=5),
                                    registrado_por=CustomUser.objects.get(email='secretaria.demo@sga.edu.br'))
    s404, _ = status(aprovado, 'finance:detalhe', outra.pk)
    passo(10, 'Aluno: extrato próprio; cobrança alheia 404', s == 200 and s404 == 404, f'{s}/{s404}')

    # 11. Painel gerencial
    s1, r = status(coord, 'academics:painel_gerencial')
    s2, _ = status(secre, 'academics:painel_gerencial')
    s3, _ = status(coord, 'academics:painel_gerencial', curso='abc')
    passo(11, 'Painel gerencial (Coordenação e Secretaria; filtro inválido 400)',
          s1 == s2 == 200 and s3 == 400 and 'Ocupação' in r.content.decode(), f'{s1}/{s2}/{s3}')

    # 12. Relatórios, CSV e transferências
    s1, _ = status(coord, 'academics:relatorios')
    s2, r_csv = status(coord, 'academics:relatorios_csv')
    s3, _ = status(coord, 'transfers:index')
    passo(12, 'Relatórios, CSV e transferências',
          s1 == s2 == s3 == 200 and r_csv['Content-Type'].startswith('text/csv'), f'{s1}/{s2}/{s3}')

    # 13. Acessos indevidos
    negados = {
        'aluno→painel': status(aprovado, 'academics:painel_gerencial')[0],
        'aluno→catálogo': status(aprovado, 'academics:index')[0],
        'professor→financeiro': status(prof, 'finance:index')[0],
        'professor→documentos': status(prof, 'documents:index')[0],
        'coordenação→financeiro': status(coord, 'finance:index')[0],
        'secretaria→pré-requisitos': status(secre, 'academics:pre_requisitos', banco.pk)[0],
        'aluno→documento alheio': status(falta, 'documents:detalhe', doc.pk)[0],
        'anônimo→painel': status(anon, 'academics:painel_gerencial')[0],
    }
    esperado = {k: (404 if 'alheio' in k else 302 if 'anônimo' in k else 403) for k in negados}
    passo(13, 'Acessos indevidos (403/404/login)', negados == esperado,
          ', '.join(f'{k}={v}' for k, v in negados.items()))

    # Extra: recuperação de senha com resposta neutra
    r1 = anon.post(reverse('accounts:password_reset'), {'email': 'aluno.aprovado@sga.edu.br'})
    r2 = Client(REMOTE_ADDR='10.9.9.9').post(
        reverse('accounts:password_reset'), {'email': 'naoexiste@sga.edu.br'})
    passo('+', 'Recuperação de senha: mesma resposta para e-mail existente e inexistente',
          r1.status_code == r2.status_code == 302 and r1.url == r2.url, f'{r1.status_code}/{r2.status_code}')

    falhas = [r for r in resultados if not r[2]]
    assert not falhas, falhas
    assert len(resultados) == 14
