# SGA — Roteiro de demonstração e entrega

| Metadado | Valor |
| --- | --- |
| Versão | **3.0 — entrega final (Fases 1, 2 e 3)** |
| Data | **20 de novembro de 2026** |

## Preparação

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo --password 'SgaDemo2026!'
```

`seed_demo` é idempotente e prepara os quatro papéis, uma turma completa e cenários de aprovação direta, exame e reprovação por falta. Para a Fase 3 também cria: `Banco de Dados — Demo` (turma 2027/1) com pré-requisito `Engenharia de Software — Demo`, um aproveitamento pendente de `Lógica — Demo` para o aluno do exame e duas mensalidades do aluno aprovado, uma delas em atraso. Todas as contas abaixo usam a senha `SgaDemo2026!`, definida explicitamente no comando. Para usar outra senha, altere o valor de `--password`; não reutilize uma senha real.

| Papel/cenário | E-mail |
| --- | --- |
| Secretaria | `secretaria.demo@sga.edu.br` |
| Coordenação | `coordenacao.demo@sga.edu.br` |
| Professor | `professor.demo@sga.edu.br` |
| Aluno aprovado direto | `aluno.aprovado@sga.edu.br` |
| Aluno elegível ao exame | `aluno.exame@sga.edu.br` |
| Aluno reprovado por falta | `aluno.falta@sga.edu.br` |

## Sequência de demonstração da Fase 1

1. **Coordenação:** entrar com a conta demo de Coordenação, criar/mostrar Curso e Disciplina, abrir ou editar Turma com período, horários textuais validados, sala, vagas e Professor responsável.
2. **Secretaria — usuários:** listar Alunos e Professores, criar ou editar uma conta e mostrar ativação/inativação sem expor credenciais reais.
3. **Secretaria — matrícula:** efetivar matrícula em turma apta e explicar que as vagas são calculadas pelas matrículas ativas.
4. **Secretaria — status e retentativa:** alterar uma matrícula ativa para Trancada, Cancelada ou Concluída; explicar que nova tentativa exige outra Turma/período, preservando o histórico.
5. **Professor — chamada:** abrir somente uma turma própria ativa, registrar uma chamada completa e mostrar o relatório de frequência e a auditoria.
6. **Professor — notas:** lançar P1, P2 e Trabalho para matrículas ativas; mostrar MP e a validação de 0 a 10.
7. **Professor — exame:** no cenário elegível, lançar Exame e mostrar MF; contrastar com o cenário abaixo de 75%, no qual o exame é bloqueado.
8. **Aluno:** entrar com as contas demo e mostrar boletim, situação e frequência sem acesso a registros de outros alunos.
9. **Qualidade:** apresentar a suíte automatizada, a CI nos dois bancos e a separação entre MVP e Roadmap.

## Validação antes da entrega

```bash
docker compose exec web python manage.py check
docker compose exec web pytest
git diff --check
```

Além da execução local em Docker/PostgreSQL, a CI executa, nessa ordem, `python manage.py check`, `python manage.py makemigrations --check --dry-run` e `pytest` nos jobs **SQLite** e **PostgreSQL 16**.

## Checklist da demonstração da Fase 1

- [ ] Containers `web` e `db` ativos; migrations aplicadas.
- [ ] `seed_demo` executado e contas de demonstração acessíveis.
- [ ] Quatro papéis demonstrados: Coordenação, Secretaria, Professor e Aluno.
- [ ] Cadastro/edição de usuários, matrícula e gestão de status demonstrados.
- [ ] Chamada completa, notas, exame, boletim e frequência demonstrados.
- [ ] Retentativa em nova turma/período explicada e histórico anterior preservado.
- [ ] Sem senha real, dado pessoal real ou credencial de produção em tela.
- [ ] Validações locais e CI verdes.

## Estado atual — 20/11/2026

| Fase | Estado | Entregas |
| --- | --- | --- |
| Fase 1/MVP | Concluída | Núcleo acadêmico descrito neste documento. |
| Fase 2 | Concluída | Materiais e comunicados (PR #66), calendário/grade/conflitos (PR #67), relatórios (PR #68, #70), transferências (PR #69, #70), recuperação de senha e notificações (PR #73, ajustes na #75). |
| Fase 3 | Implementada | Pré-requisitos e aproveitamento (PR #76), painel gerencial (PR #77), documentos oficiais (PR #78) e financeiro básico (PR #79), conforme a [especificação da Fase 3](SGA-12-ESPECIFICACAO-FASE-3.md). |
| Estudos | Somente estudo | API pública e integrações ([SGA-13](SGA-13-ESTUDO-API-INTEGRACOES.md)): recomendação de não expor API nesta evolução. App mobile e IA ([SGA-14](SGA-14-ESTUDO-MOBILE-IA.md)): recomendação de não implementar nesta evolução. |
| Fechamento | Em andamento | Documentação final (PR #80), validação com instalação limpa (PR #81) e lacunas da auditoria das issues: comunicados no painel, filtro por turma na grade, testes de vínculo curricular e `CONTRIBUTING.md` (PR #82); correções da conferência visual em desktop e celular (PR #84). Pré-release `v3.0.0-rc1`. Pendentes: ensaio da apresentação (#53), merge em `main` e `v3.0.0`. |

“Fora do MVP” nos trechos da Fase 1 significa fora do escopo **original**, não ausente do código atual. As seções de estado de 08/10/2026 foram substituídas por esta; o histórico permanece no Git.

## Roteiro da apresentação final (Fases 1, 2 e 3)

Preparação: banco descartável, `migrate` e `seed_demo` como acima. Todas as contas usam a senha definida em `--password`.

| # | Papel (conta demo) | O que mostrar | Regra em destaque |
| --- | --- | --- | --- |
| 1 | Coordenação | Painel com comunicados recentes; catálogo (curso, disciplina, turma); grade horária com filtros por curso, turma e período; conflito de horário. | RN04, RN05 |
| 2 | Coordenação | Botão **Pré-requisitos** em `Banco de Dados — Demo`: mostrar o pré-requisito e tentar criar um ciclo (é recusado). | RN18 |
| 3 | Secretaria | Matricular `aluno.aprovado` na turma 2027/1 de Banco de Dados (aceito) e `aluno.falta` (bloqueado, lista o pré-requisito pendente). | RN19 |
| 4 | Professor | Chamada e notas na turma própria; exame só para o aluno elegível. | RN09–RN14 |
| 5 | Aluno (`aluno.exame`) | Boletim, frequência, notificações de nota/frequência e o aproveitamento pendente. | RN11–RN14 |
| 6 | Coordenação | **Aproveitamentos**: deferir o pendente com justificativa; mostrar a regra dos 75%. | RN20 |
| 7 | Aluno (`aluno.aprovado`) | **Meus Documentos**: emitir histórico, imprimir (A4) e copiar o código. | RN21, RN22 |
| 8 | Visitante (sem login) | No login, **Verificar autenticidade de documento**: colar o código; ver nome mascarado e nenhuma nota. | RN23 |
| 9 | Secretaria | **Financeiro**: mensalidade em atraso, registrar pagamento e cancelar outra com justificativa. | RN24 |
| 10 | Aluno (`aluno.aprovado`) | **Meu Financeiro**: extrato próprio; tentar abrir cobrança de outro aluno (404). | RN25 |
| 11 | Coordenação / Secretaria | **Painel Gerencial**: ocupação, situações, risco e pendências; filtro por curso/período. | RN26 |
| 12 | Coordenação | Relatórios acadêmicos com risco, CSV e impressão; transferência registrada e analisada. | Fase 2 |
| 13 | Todos | Acessos indevidos retornam 403/404; encerrar com arquitetura, testes e CI. | RN01 |

**Recuperação de senha na demo (Mailpit):** por segurança, o padrão em memória não exibe o link e os backends de console e arquivo são bloqueados. Para mostrar o e-mail chegando, use o Mailpit, a caixa de e-mail local que já vem no `docker-compose.yml`:

1. No `.env`, troque as linhas de e-mail por `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST=mailpit`, `EMAIL_PORT=1025` e `EMAIL_USE_TLS=False`.
2. `docker compose up -d` e, se o `web` já estava rodando, `docker compose restart web`.
3. No login, **Esqueci minha senha** com uma conta demo; repita com um e-mail inexistente e mostre que a mensagem é a mesma.
4. Abra `http://localhost:8025`: só a conta existente recebeu o e-mail. Clique no link e defina a nova senha.
5. Rode `seed_demo` de novo para restaurar a senha das contas demo.

Sem o Mailpit, mostre a mensagem neutra e cite os testes de token válido, expirado e reutilizado em `tests/test_accounts/test_recovery.py`. Detalhes em [SGA-11](SGA-11-RECUPERACAO-NOTIFICACOES.md).

## Checklist final de entrega

- [ ] `docker compose exec web python manage.py check`
- [ ] `docker compose exec web python manage.py makemigrations --check --dry-run`
- [ ] `docker compose exec web pytest` (cobertura mínima de 85%)
- [ ] `git diff --check`
- [ ] CI verde em SQLite e PostgreSQL 16 na `develop`
- [ ] Instalação limpa seguindo o README em máquina ou volume novo
- [ ] Roteiro acima executado com os quatro papéis
- [ ] Tag/release da versão entregue

## Registro da validação final — 20/11/2026 (#63, #53)

**Instalação limpa:** clone da `develop` (`02ba483`) do GitHub em diretório e volume novos, seguindo o README (`cp .env.example .env`, `docker compose up --build -d`, `migrate`, `seed_demo`). `check` sem problemas, `makemigrations --check` sem mudanças e páginas públicas (login, recuperação de senha, verificação de documento) respondendo.

**Roteiro percorrido via HTTP** sobre os dados do `seed_demo`, com login real de cada conta demo: **14/14 passos aprovados**, incluindo pré-requisito e ciclo recusado, matrícula aceita e bloqueada, deferimento de aproveitamento, histórico emitido e verificado publicamente com nome mascarado, pagamento e cancelamento de cobrança, painel gerencial, relatórios/CSV, transferências, recuperação de senha com resposta neutra e acessos indevidos (403, 404 e redirecionamento ao login). O mesmo percurso é executado pela CI em `tests/test_integration/test_roteiro_final.py`. Depois disso, a PR #82 completou critérios revisados na auditoria das issues (comunicados no painel, filtro por turma na grade); a suíte final registrou **545 testes aprovados e cobertura de 90,53%**, e foi criada a pré-release `v3.0.0-rc1`.

**Conferência visual (20/11/2026):** feita no Chrome com os quatro papéis e o visitante, em 1366px e 390px. A PR #84 corrigiu a sidebar no celular (agora recolhível pelo botão **Menu**), a tabela do histórico no celular, a vírgula decimal nas notas, o selo do painel gerencial, o rótulo de sala na grade e o layout da verificação pública. Testes em `tests/test_integration/test_conferencia_visual.py`; suíte com 549 testes.

**Pendente:** ensaio da apresentação. Upload de materiais é coberto pelos testes de `tests/test_materials/`, não por este percurso.
