"""Verificação opcional em navegador. Use somente banco local descartável com seed_demo.

Requer Playwright/Chromium no Python que executa este script; não integra pytest.
A aplicação Django pode usar outro Python, fornecido por --django-python.
"""
import argparse
import csv
import os
import re
from pathlib import Path
import subprocess
import sys
import time
from io import StringIO
from uuid import uuid4
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--django-python', default=sys.executable)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--bootstrap-cache', type=Path,
                        help='Cache opcional dos arquivos originais bootstrap.css/js 5.3.3 para ambientes sem CDN.')
    parser.add_argument('--confirmar-banco-demo', action='store_true', required=True)
    args = parser.parse_args()
    senha = os.environ.get('SGA_DEMO_PASSWORD')
    if not senha:
        parser.error('Defina SGA_DEMO_PASSWORD com a senha temporária usada no seed_demo.')
    args.output.mkdir(parents=True, exist_ok=True)
    raiz = Path(__file__).resolve().parents[1]
    base = 'http://127.0.0.1:8001'
    servidor = subprocess.Popen([args.django_python, 'manage.py', 'runserver',
                                 '127.0.0.1:8001', '--noreload'], cwd=raiz,
                                env={**os.environ, 'USE_SQLITE': 'True'},
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urlopen(base + '/accounts/login/', timeout=1).close()
                break
            except OSError:
                if servidor.poll() is not None:
                    raise RuntimeError('Servidor encerrou antes de iniciar.')
                time.sleep(.2)
        else:
            raise RuntimeError('Servidor não iniciou em tempo hábil.')
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True, args=['--no-sandbox'])

            def entrar(email):
                contexto = navegador.new_context(viewport={'width': 1440, 'height': 1000})
                if args.bootstrap_cache:
                    # Só o teste usa cache. Preserva URLs e integridade SRI do HTML.
                    contexto.route(re.compile(r'^https?://(?!127\.0\.0\.1:)'), lambda route: route.abort())
                    contexto.route('https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
                                   lambda route: route.fulfill(path=str(args.bootstrap_cache / 'bootstrap.css'),
                                                              content_type='text/css', headers={'Access-Control-Allow-Origin': '*'}))
                    contexto.route('https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
                                   lambda route: route.fulfill(path=str(args.bootstrap_cache / 'bootstrap.js'),
                                                              content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
                pagina = contexto.new_page()
                pagina.goto(base + '/accounts/login/', wait_until='domcontentloaded')
                pagina.locator('[name=username]').fill(email)
                pagina.locator('[name=password]').fill(senha)
                pagina.locator('button[type=submit]').click()
                pagina.wait_for_url('**/dashboard/**')
                return pagina

            coord = entrar('coordenacao.demo@sga.edu.br')
            coord.goto(base + '/academics/relatorios/', wait_until='domcontentloaded')
            coord.locator('#id_risco').select_option('sim')
            coord.get_by_role('button', name='Aplicar filtros').click()
            expect(coord.locator('tbody tr')).to_have_count(2)
            expect(coord.locator('.report-actions')).to_have_css('display', 'flex')
            with coord.expect_download() as evento:
                coord.get_by_role('link', name='Exportar CSV').click()
            download = evento.value
            download.save_as(args.output / 'relatorio.csv')
            csv_antes = (args.output / 'relatorio.csv').read_bytes().decode('utf-8-sig')
            assert len(list(csv.DictReader(StringIO(csv_antes)))) == 2
            coord.screenshot(path=str(args.output / 'relatorio-tela.png'), full_page=True)
            coord.evaluate('window.print = () => { window.impressaoSolicitada = true; }')
            coord.get_by_role('button', name='Imprimir relatório').click()
            assert coord.evaluate('window.impressaoSolicitada === true')
            coord.emulate_media(media='print')
            expect(coord.locator('.report-actions')).to_be_hidden()
            expect(coord.locator('.report-filters')).to_be_hidden()
            expect(coord.locator('.sidebar-custom')).to_be_hidden()
            coord.pdf(path=str(args.output / 'relatorio.pdf'), prefer_css_page_size=True)
            coord.emulate_media(media='screen')
            coord.set_viewport_size({'width': 390, 'height': 844})
            coord.screenshot(path=str(args.output / 'relatorio-mobile.png'), full_page=True)

            secretaria = entrar('secretaria.demo@sga.edu.br')
            detalhes = []
            for tipo, decisao in [('ENTRADA', 'APROVADA'), ('SAIDA', 'RECUSADA')]:
                secretaria.goto(base + '/transfers/criar/', wait_until='domcontentloaded')
                aluno = secretaria.locator('#id_aluno option').filter(has_text='aluno.exame@sga.edu.br').get_attribute('value')
                curso = secretaria.locator('#id_curso option').filter(has_text='ADS-DEMO').get_attribute('value')
                secretaria.locator('#id_aluno').select_option(aluno)
                secretaria.locator('#id_curso').select_option(curso)
                secretaria.locator('#id_tipo').select_option(tipo)
                secretaria.locator('#id_instituicao_externa').fill('Demo navegador ' + uuid4().hex[:8])
                secretaria.locator('#id_curso_externo').fill('ADS externo')
                secretaria.locator('#id_data_referencia').fill('2026-09-24')
                secretaria.locator('#id_documentos').fill('Histórico fictício conferido para demonstração.')
                secretaria.get_by_role('button', name='Registrar solicitação pendente').click()
                secretaria.wait_for_url(re.compile(r'/transfers/\d+/$'))
                detalhe = secretaria.url
                detalhes.append(detalhe)
                expect(secretaria.locator('h1')).to_contain_text('Pendente')
                coord.goto(detalhe, wait_until='domcontentloaded')
                coord.locator('#id_decisao').select_option(decisao)
                coord.locator('#id_justificativa').fill('Validado em navegador com dados fictícios.')
                coord.get_by_role('button', name='Confirmar decisão').click()
                expect(coord.locator('h1')).to_contain_text('Aprovada' if decisao == 'APROVADA' else 'Recusada')
                expect(coord.get_by_role('button', name='Confirmar decisão')).to_have_count(0)
            aluno = entrar('aluno.exame@sga.edu.br')
            assert aluno.goto(detalhes[0], wait_until='domcontentloaded').status == 200
            outro = entrar('aluno.aprovado@sga.edu.br')
            assert outro.goto(detalhes[0], wait_until='domcontentloaded').status == 404
            professor = entrar('professor.demo@sga.edu.br')
            assert professor.goto(base + '/academics/relatorios/', wait_until='domcontentloaded').status == 403
            assert professor.goto(base + '/transfers/', wait_until='domcontentloaded').status == 403
            csv_depois = coord.request.get(base + '/academics/relatorios/exportar.csv?risco=sim')
            assert csv_depois.body().decode('utf-8-sig') == csv_antes
            navegador.close()
            print('OK: filtro, CSV, impressão, entrada/aprovação, saída/recusa e isolamento por perfil.')
    finally:
        servidor.terminate()
        servidor.wait(timeout=10)


if __name__ == '__main__':
    main()
