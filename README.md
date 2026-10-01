# SGA — Sistema de Gestão Acadêmica

**Versão 1.0 — MVP Fase 1 concluído (31 de agosto de 2026)**

O SGA é um monólito Django para ensino superior. Centraliza a oferta acadêmica, matrícula administrativa, frequência, avaliações e consulta acadêmica pelo aluno, com acesso isolado por papel.

## Stack

- Python 3.12+, Django 5+, Django Templates, HTMX e Bootstrap 5.
- PostgreSQL 16, Docker Compose, pytest e pytest-django.
- Módulos: `accounts`, `academics`, `enrollment`, `attendance` e `assessments`.

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

## Documentação

- [Documento consolidado](docs/SGA-DOCUMENTO-CONSOLIDADO.md)
- [Escopo](docs/SGA-01-ESCOPO.md), [regras](docs/SGA-02-REGRAS-DE-NEGOCIO.md), [requisitos](docs/SGA-03-REQUISITOS.md) e [modelo de dados](docs/SGA-04-MODELAGEM-DADOS.md)
- [Rastreabilidade](docs/SGA-05-RASTREABILIDADE.md), [casos de uso](docs/SGA-06-CASOS-DE-USO.md) e [roteiro de demonstração](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md)
- [Preparação técnica da Fase 2](docs/SGA-08-PREPARACAO-FASE-2.md) — proposta de arquitetura e revisão do backlog, sem implementação funcional
- [Transferências simplificadas](docs/SGA-09-TRANSFERENCIAS.md) — implementação das #49/#61, regras adotadas e contribuição para #51

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
descrita acima; sua entrega não conclui todas as atividades da issue #36.


## Estado para apresentação — 01/10/2026

A Fase 1/MVP está concluída. A Fase 2 já possui entregas integradas em materiais/comunicados (#66), calendário/grade/conflitos (#67), relatórios (#68) e transferências (#69). Permanecem em aberto #51, #62, #35 e #37. “Fora do MVP” refere-se ao escopo original da Fase 1.
