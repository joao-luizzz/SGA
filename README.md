# SGA — Sistema de Gestão Acadêmica

**Versão 1.0 — MVP Fase 1 concluído (31 de agosto de 2026)**

O SGA é um monólito Django para ensino superior. Centraliza a oferta acadêmica, matrícula administrativa, frequência, avaliações e consulta acadêmica pelo aluno, com acesso isolado por papel.

## Stack

- Python 3.12+, Django 5+, Django Templates, HTMX e Bootstrap 5.
- PostgreSQL 16, Docker Compose, pytest e pytest-django.
- Módulos: `accounts`, `academics`, `enrollment`, `attendance`, `assessments`, `materials`, `communications`, `transfers` e `notifications`.

## Fase 1 entregue

| Perfil | Funcionalidades |
| --- | --- |
| Aluno | Consulta suas matrículas, boletim, médias, situação e frequência. |
| Professor | Registra chamada completa e notas nas próprias turmas ativas; lança Exame somente a elegíveis. |
| Secretaria | Cria, edita, lista, ativa/inativa Alunos e Professores; efetiva matrículas e altera seus status. |
| Coordenação | Gerencia cursos, disciplinas, turmas e alocação docente. |

O sistema calcula MP, MF, frequência, situação e vagas. `Nota` pertence a `Matricula`; `Falta` pertence a Aluno, Turma e data; alterações desses registros são auditadas de forma imutável.

## Transferências simplificadas — Fase 2

O módulo `transfers` permite à Secretaria registrar solicitações de entrada/saída,
à Coordenação aprovar ou recusar com justificativa e ao Aluno consultar somente
suas solicitações. Acesse **Transferências** no menu após aplicar as migrations.
A aprovação é administrativa: preserva matrículas, notas e frequência e não
efetiva nem encerra matrículas automaticamente. Regras, limites e roteiro de
validação estão na [documentação de transferências](docs/SGA-09-TRANSFERENCIAS.md).

## Relatórios e integração — Semana 5

A Coordenação consulta relatórios com filtro de acompanhamento, motivos de risco,
exportação CSV e impressão A4 da consulta filtrada. A sinalização usa notas e
frequência disponíveis, sem modificar o resultado acadêmico. A integração de
relatórios e transferências foi concluída na PR #70. Consulte as regras e evidências
na [conclusão da Semana 5](docs/SGA-10-RELATORIOS-INTEGRACAO.md).

## Recuperação de senha e notificações — Semana 4

A opção **Esqueci minha senha** fica no login. A central **Notificações** na navbar
é pessoal para todos os papéis, inclusive superusuários. E-mails usam configuração
por ambiente; o padrão em memória não envia mensagens nem imprime links em logs.
Consulte [configuração, segurança e demonstração](docs/SGA-11-RECUPERACAO-NOTIFICACOES.md).

## Documentação

- [Documento consolidado](docs/SGA-DOCUMENTO-CONSOLIDADO.md)
- [Escopo](docs/SGA-01-ESCOPO.md), [regras](docs/SGA-02-REGRAS-DE-NEGOCIO.md), [requisitos](docs/SGA-03-REQUISITOS.md) e [modelo de dados](docs/SGA-04-MODELAGEM-DADOS.md)
- [Rastreabilidade](docs/SGA-05-RASTREABILIDADE.md), [casos de uso](docs/SGA-06-CASOS-DE-USO.md) e [roteiro de demonstração](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md)
- [Preparação técnica da Fase 2](docs/SGA-08-PREPARACAO-FASE-2.md) — proposta de arquitetura e revisão do backlog, sem implementação funcional
- [Transferências simplificadas](docs/SGA-09-TRANSFERENCIAS.md) — implementação das #49/#61 e integração com relatórios concluída na #51
- [Relatórios e integração da Semana 5](docs/SGA-10-RELATORIOS-INTEGRACAO.md) — risco acadêmico, filtros, CSV, impressão e validação integrada

## Executar com Docker Compose

```bash
git clone https://github.com/joao-luizzz/SGA.git
cd SGA
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py migrate
```

A aplicação fica em `http://localhost:8000`.

### Dados de demonstração

```bash
docker compose exec web python manage.py seed_demo
```

O seed é idempotente e cria contas de demonstração para os quatro papéis e cenários de aprovação direta, exame e reprovação por falta. Use apenas essas contas em apresentações e configure uma senha de demonstração com `--password`; não use senha real.

### Primeiro usuário de Secretaria

```bash
docker compose exec web python manage.py create_secretaria_user
```

O comando também aceita `--email`, `--full-name` e `--password`. A conta criada exige troca de senha no primeiro acesso.

## Validação e testes

```bash
docker compose exec web python manage.py check
docker compose exec web pytest
git diff --check
```

Com o ambiente virtual local ativado, a suíte também pode ser executada em SQLite:

```bash
USE_SQLITE=True pytest
```

Esse comando mede a cobertura do código relevante em `apps/`, mostra no terminal as linhas não cobertas e gera `coverage.xml` na raiz para consulta por ferramentas. O CI aplica essa medição no job SQLite; o job PostgreSQL executa a mesma suíte sem gerar o relatório novamente.

A suíte automatizada cobre autenticação, RBAC, usuários, oferta acadêmica, matrícula, vagas, chamada, frequência, notas, exame, auditoria, seed e fluxo ponta a ponta. A CI executa `python manage.py check`, `python manage.py makemigrations --check --dry-run` e `pytest` nos bancos **SQLite** e **PostgreSQL 16**. Não há uma contagem fixa de testes nesta documentação.

## Fora do MVP

Auto-matrícula, recuperação de senha, materiais, calendário, comunicados, documentos, transferências, financeiro, app mobile, integrações e pré-requisitos são Roadmap e não estão implementados na Fase 1.

Essa delimitação se refere à Fase 1. A transferência simplificada da Fase 2 está
descrita acima; os módulos implementados depois do MVP estão relacionados no
estado atual abaixo. “Fora do MVP” identifica o escopo original da Fase 1, não
indica que todos esses módulos continuam ausentes do código.


## Estado atual para apresentação — 08/10/2026

**Fase 1/MVP:** concluída.

**Fase 2:**

Semanas 1, 2, 3 e 5 integradas; Semana 4 implementada nesta entrega, aguardando revisão.

- Materiais e comunicados — concluídos na PR #66.
- Calendário, grade e conflitos — concluídos na PR #67.
- Relatórios acadêmicos — entregues na PR #68; complementados e integrados com transferências na PR #70.
- Transferências — concluídas na PR #69; integração com relatórios concluída na PR #70.
- Recuperação segura de senha — implementada nesta entrega (#35; solicitação #47 e redefinição/token #59).
- Notificações internas, leitura e testes — implementados nesta entrega (#35; central #48 e leitura/testes #60).

**Fase 3:** futura (#37). “Fora do MVP” significa fora do escopo original da Fase 1, não necessariamente ausente do código atual.

## Entrega da Semana 4 — Issue #35 (08/10/2026)

**Estado desta branch:** #35, #47, #48, #59 e #60 concluídas na implementação,
aguardando revisão e integração. Isso não declara merge na develop nem fechamento
das issues no GitHub. A base é `08d4407`; Semanas 1, 2, 3 e 5 permanecem entregues
e Fase 3 permanece futura.

Recuperação usa tokens nativos Django com expiração configurável, validação de
senha, uso único e confirmação serializada no PostgreSQL. A central pessoal tem
paginação, detalhe, leitura individual/todas via POST + CSRF e contador na navbar.
Comunicados, notas e frequência geram notificações conforme as regras existentes.
Detalhes, configuração e evidências: [Semana 4](docs/SGA-11-RECUPERACAO-NOTIFICACOES.md).

**Registro histórico da revisão após PR #70:** naquele ponto, recuperação de senha
e notificações ainda estavam pendentes. A implementação desta entrega é posterior;
o escopo original da Fase 1 e as evidências das PRs anteriores são preservados.
