# Semana 5 — conclusão dos relatórios e validação integrada

Escopo: conclusão de #62 e #51, dentro da issue mãe #36. Andrey assumiu a entrega em 24/09/2026.
Base inicial: `a41e42b5e467df9e6395060440c3a418c64f9ff3` (`develop`, após merge do PR #69). A entrega final foi integrada pela PR #70 no merge `950d871597dea7499bd9e63ca75029639314a97a`.

## Levantamento histórico anterior à PR #70

- #49 e #61 encerradas; transferência administrativa integrada no PR #69.
- #50 encerrada; notas, resultados, frequência, filtros e CSV já vieram no PR #68.
- Na revisão anterior ao complemento, #62 ainda estava aberta: faltavam identificação explícita de risco e impressão preparada.
- Na mesma revisão, #51 ainda estava aberta e exigia verificação conjunta de permissões, filtros e histórico.
- A #36 registrava então as entregas individuais concluídas, com integração e validação ainda por fazer. A PR #70 completou esse trabalho.

## Regra de risco adotada para revisão

Indicador de acompanhamento por matrícula ativa, calculado sem persistência ou
mudança de nota, frequência, matrícula ou resultado oficial. Usa limites do
AGENTS.md e das regras acadêmicas existentes: média 6 e frequência mínima 75%.

- Frequência registrada abaixo de 75% gera alerta, mesmo com notas incompletas.
- Se houver média final, ela prevalece: abaixo de 6 gera alerta por nota.
- Sem média final, média parcial abaixo de 6 gera alerta; inclui elegíveis a exame
  e situações já reprovadas. O resultado oficial continua em coluna separada.
- Com avaliações incompletas, média simples das notas já lançadas abaixo de 6
  gera alerta **provisório**, identificado como avaliações incompletas. Notas
  ausentes não viram zero; não se apresenta essa média como média parcial oficial.
- Sem alerta, mas sem todas as notas ou sem aulas, mostrar “Dados insuficientes”.
- “Sem alerta nos dados disponíveis” não garante aprovação futura.
- A sinalização é descritiva dos dados atuais; não usa previsão estatística nem
  novos limiares preventivos arbitrários. João revisa essa regra no PR.

## Divisão dos cinco commits

1. Regra de risco e testes de limites; 2. filtros e CSV; 3. tela e impressão;
4. testes de integração com demonstração; 5. documentação e evidências finais.

## Matriz de entrega

| Requisito | Implementação e evidência |
| --- | --- |
| #62 — notas e resultados | Reutiliza cálculo oficial existente; regressões em `test_reports.py`, preservando média zero e aprovação após exame |
| #62 — frequência | Mantém cálculo existente; tela distingue ausência de aulas de frequência real; tests de limites em `test_report_risk.py` |
| #62 — alunos em risco | `identificar_risco_academico` em services, integrado ao selector; motivos explícitos, filtro sim/não e testes de valores limítrofes |
| #62 — impressão | Botão chama impressão do navegador, CSS A4 paisagem, cabeçalho com data/filtros, menus removidos, cabeçalho da tabela repetível |
| #62 — CSV | Mesmos filtros da tela; duas colunas novas ao final: acompanhamento e motivos; formato anterior preservado nas demais colunas |
| #51 — integração | `test_semana5_flow.py` usa `seed_demo`, criação/decisão HTTP e compara CSV e registros acadêmicos antes/depois |
| #51 — acesso | Coordenação consulta relatórios; Secretaria solicita, Coordenação decide; Aluno só lê suas transferências; Professor bloqueado nestes módulos |
| #51 — filtros com demo | Curso, período, turma e risco combinados; dois alunos sinalizados no seed; ocupação permanece 3/30 apesar de mostrar duas linhas |
| #51 — regras críticas | Duplicidade, justificativa, reenvio de decisão, isolamento, preservação de histórico, fronteiras 6/75, notas ausentes/zero e média final |
| #36 — N+1 | Selector continua usando quatro consultas para turmas com alunos, também com filtro de risco; filtro não muda a ocupação real |

`risco=nao` significa ausência de alerta identificado e **inclui dados insuficientes**;
não é filtro de alunos aprovados. Filtro de risco remove turmas sem linhas correspondentes,
mas sem esse filtro turmas vazias continuam aparecendo. IDs/período/risco inválidos
retornam HTTP 400 em HTML e CSV, em vez de gerar erro de servidor.

Não há alteração de schema ou migration nesta entrega. CSV recebeu colunas ao final:
consumidores que exigem exatamente 17 colunas devem aceitar as duas novas colunas.
A impressão utiliza o diálogo do navegador (papel ou salvar como PDF), sem serviço PDF
adicional no servidor. Somente matrículas e turmas ativas compõem o relatório, conforme
escopo que já existia; registros históricos continuam armazenados.

## Registro histórico da validação local — 24/09/2026

- Suíte completa local SQLite: **380 passed, 2 skipped**, cobertura **88,75%** (mínimo 85%).
- 31 testes novos de risco, filtros, impressão HTTP e integração; testes anteriores mantidos.
- Os dois skips são de concorrência PostgreSQL, já existentes no módulo transfers;
  nesta execução local pré-merge, a confirmação do job PostgreSQL 16 ainda estava pendente.
- `manage.py check`, `makemigrations --check --dry-run` e `git diff --check` sem problemas.
- Migrations existentes aplicadas em banco SQLite novo; `seed_demo` executado.
- Revisão estática do diff: regra separada do resultado oficial, permissões, consultas,
  compatibilidade de filtros/exportação, ausência de escritas acadêmicas e CSS de impressão.
- Navegador real Chromium: login por perfil; filtro de risco retornou os dois alunos
  esperados; CSV baixado antes/depois idêntico; entrada aprovada e saída recusada;
  Aluno próprio 200, outro Aluno 404, Professor 403; decisão final sem novo botão.
- Botão de impressão acionou `window.print` (instrumentado no teste); renderização
  de mídia print e PDF Chromium executadas; inspeção visual de desktop 1440px,
  mobile 390px e PDF de uma página A4 paisagem realizada.
- A tabela no mobile permite rolagem horizontal, seguindo o layout Bootstrap existente.
- Limitação ambiental: fontes e ícones externos indisponíveis no teste. Bootstrap
  5.3.3 original servido de cache somente no navegador de teste, mantendo URL e SRI;
  CSS local renderizado normalmente. A aplicação não teve seu mecanismo de assets alterado.
- Impressão em impressora física não executada nesta revisão local. A evidência final
  da PR #70 inclui impressão do navegador e renderização PDF; ver a validação final abaixo.

## Reproduzir

Use **banco descartável**, nunca dados reais. Com as dependências do projeto instaladas:

```bash
export SGA_DEMO_PASSWORD='<senha-temporaria-exclusiva>'
USE_SQLITE=True python manage.py migrate
USE_SQLITE=True python manage.py seed_demo --password "$SGA_DEMO_PASSWORD"
USE_SQLITE=True python manage.py check
USE_SQLITE=True python manage.py makemigrations --check --dry-run
USE_SQLITE=True pytest
```

Verificação opcional em navegador: instale Playwright em ambiente de teste separado
(`pip install playwright` e `python -m playwright install chromium`), e execute:

```bash
python scripts/validar_semana5_browser.py \
  --django-python /caminho/do/venv-do-sga/bin/python \
  --output /caminho/temporario/evidencias \
  --confirmar-banco-demo
```

Esse script inicia servidor local na porta 8001 usando SQLite, utiliza contas de
`seed_demo`, cria duas solicitações fictícias, registra decisões e gera evidências.
Ele não limpa dados ao terminar e exige `SGA_DEMO_PASSWORD` com a mesma senha
temporária usada no seed. O parâmetro opcional `--bootstrap-cache` recebe diretório com os arquivos
originais `bootstrap.css` (bootstrap.min.css) e `bootstrap.js` (bootstrap.bundle.min.js)
da versão 5.3.3; nesse modo fontes/ícones de CDN são omitidos e somente os dois assets
Bootstrap são atendidos pelo cache do teste. Não versionar banco, senha ou evidências locais.

Roteiro manual: entrar como Coordenação, abrir Relatórios Acadêmicos, combinar os
quatro filtros, comparar tela/CSV e imprimir; depois executar uma entrada aprovada
 e uma saída recusada como Secretaria/Coordenação. Conferir relatórios/histórico
antes e depois e tentar acessar a transferência com outro aluno e Professor.

## Registro histórico da aceitação antes do merge da PR #70

Antes do merge da PR #70, o complemento da #62 e as evidências da #51 aguardavam revisão,
integração e validação final da Semana 5. Esse registro descreve o estado daquela revisão,
não o estado atual da develop.

## Conclusão da Semana 5 — estado atual em 08/10/2026

A PR #70 (`feat: conclui relatórios e validação integrada da Semana 5`) foi integrada
na develop pelo merge `950d871597dea7499bd9e63ca75029639314a97a`.

- #62 — concluída: relatórios acadêmicos com identificação e motivos de risco, filtro,
  CSV compatível e impressão A4.
- #51 — concluída: integração de transferências e relatórios, RBAC, filtros combinados,
  preservação do histórico e testes de fluxo integrado.
- #36 — concluída: Semana 5 finalizada e validada.
- #49 e #61 — concluídas na PR #69; a PR #70 adiciona validação integrada sem mudar
  o caráter administrativo da transferência.

### Evidência da validação da PR #70

- Suíte SQLite: **380 testes aprovados, 2 skips** de concorrência PostgreSQL.
- Cobertura: **88,75%**, com limite configurado de 85%.
- `manage.py check`, `makemigrations --check --dry-run` e `git diff --check`: aprovados.
- CI da PR #70: jobs SQLite e PostgreSQL aprovados; os testes de concorrência foram
  exercitados pelo job PostgreSQL.
- Validação de navegador realizada para filtros, CSV, impressão, aprovar/recusar
  transferências e permissões.

Os números acima são evidência desta validação específica da Semana 5, não uma promessa
de contagem ou cobertura fixa para execuções futuras. **Registro histórico após PR #70:** naquele momento, as pendências funcionais
da Fase 2 eram recuperação segura de senha e notificações (#35 e issues relacionadas);
Fase 3 (#37) permanece futura.

A Semana 4 foi implementada posteriormente nesta branch e aguarda revisão/integração.
Consulte [Recuperação e notificações](SGA-11-RECUPERACAO-NOTIFICACOES.md).
