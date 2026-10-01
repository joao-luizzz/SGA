from decimal import Decimal

import pytest

from academics.services import identificar_risco_academico


@pytest.mark.parametrize('valores,mp,mf,frequencia,aulas,esperado', [
    ([], None, None, '100', 0, False),
    (['0'], None, None, '100', 0, True),
    (['6'], None, None, '100', 0, False),
    (['6','6','6'], '6', None, '75', 4, False),
    (['6','6','6'], '6', None, '74.99', 4, True),
    ([], None, None, '50', 2, True),
    (['5','5','5'], '5', None, '100', 4, True),
    (['5','5','5'], '5', '6', '100', 4, False),
    (['5','5','5'], '5', '5.99', '100', 4, True),
    (['0','0','0'], '0', None, '100', 4, True),
])
def test_risco_respeita_limites_e_dados_parciais(valores, mp, mf, frequencia, aulas, esperado):
    notas = dict(zip(['P1','P2','TRABALHO'], map(Decimal, valores)))
    resultado = {'media_parcial': Decimal(mp) if mp is not None else None,
                 'media_final': Decimal(mf) if mf is not None else None,
                 'frequencia': {'percentual': Decimal(frequencia), 'total_aulas': aulas}}
    risco = identificar_risco_academico(notas=notas, resultado=resultado)
    assert risco['em_risco'] is esperado
    assert bool(risco['motivos']) is esperado
    assert risco['dados_incompletos'] == (len(valores) < 3 or not aulas)
    assert resultado['media_parcial'] == (Decimal(mp) if mp is not None else None)


def test_risco_informa_os_dois_motivos_sem_reprovar_automaticamente():
    resultado = {'media_parcial': None, 'media_final': None,
                 'situacao': 'Em andamento',
                 'frequencia': {'percentual': Decimal('50'), 'total_aulas': 2}}
    risco = identificar_risco_academico(notas={'P1': Decimal('2')}, resultado=resultado)
    assert len(risco['motivos']) == 2
    assert 'incompletas' in risco['motivos'][1]
    assert resultado['situacao'] == 'Em andamento'
