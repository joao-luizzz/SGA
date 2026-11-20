# SGA — Sistema de Gestão Acadêmica

**Versão 3.0 — Fases 1, 2 e 3 (20 de novembro de 2026)**

O SGA é um monólito Django para ensino superior. Centraliza a oferta acadêmica, matrícula administrativa, frequência, avaliações e consulta acadêmica pelo aluno, com acesso isolado por papel.

## Stack

- Python 3.12+, Django 5+, Django Templates, HTMX e Bootstrap 5.
- PostgreSQL 16, Docker Compose, pytest e pytest-django.
- Módulos: `accounts`, `academics`, `enrollment`, `attendance`, `assessments`, `materials`, `communications`, `transfers`, `notifications`, `documents` e `finance`.

## Fase 1 entregue

| Perfil | Funcionalidades |
| --- | --- |
| Aluno | Consulta suas matrículas, boletim, médias, situação e frequência. |
| Professor | Registra chamada completa e notas nas próprias turmas ativas; lança Exame somente a elegíveis. |
| Secretaria | Cria, edita, lista, ativa/inativa Alunos e Professores; efetiva matrículas e altera seus status. |
| Coordenação | Gerencia cursos, disciplinas, turmas e alocação docente. |

## Fases 2 e 3

| Módulo | Quem usa | Onde |
| --- | --- | --- |
| Materiais e comunicados | Professor, Secretaria, Coordenação, Aluno | **Materiais**, **Mural de Avisos** |
| Calendário e grade horária | Todos | **Grade Horária** |
| Transferências | Secretaria registra, Coordenação analisa, Aluno consulta | **Transferências** |
| Relatórios acadêmicos (risco, CSV, impressão) | Coordenação | **Relatórios Acadêmicos** |
| Recuperação de senha | Todos | **Esqueci minha senha** no login |
| Notificações | Todos | sino **Notificações** na barra superior |
| Pré-requisitos | Coordenação | botão de pré-requisitos no catálogo de disciplinas |
| Aproveitamento de disciplinas | Secretaria registra, Coordenação analisa, Aluno consulta | **Aproveitamentos** |
| Painel gerencial | Coordenação, Secretaria | **Painel Gerencial** |
| Documentos oficiais | Aluno (próprios), Secretaria | **Meus Documentos** / **Documentos Oficiais**; verificação pública no login |
| Financeiro básico | Secretaria opera, Aluno consulta | **Financeiro** / **Meu Financeiro** |

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
- [Recuperação de senha e notificações](docs/SGA-11-RECUPERACAO-NOTIFICACOES.md) — Semana 4, integrada na PR #73
- [Especificação da Fase 3](docs/SGA-12-ESPECIFICACAO-FASE-3.md) — casos de uso, regras, DER e rastreabilidade de pré-requisitos, documentos, financeiro e dashboard
- [Estudo de API pública e integrações](docs/SGA-13-ESTUDO-API-INTEGRACOES.md) — opções avaliadas e recomendação
- [Estudo de app mobile e IA](docs/SGA-14-ESTUDO-MOBILE-IA.md) — opções avaliadas e recomendação

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

O seed é idempotente e cria contas de demonstração para os quatro papéis, cenários de aprovação direta, exame e reprovação por falta, e os cenários da Fase 3 (pré-requisito, aproveitamento pendente e mensalidades, uma em atraso). O roteiro está em [SGA-07](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md). Use apenas essas contas em apresentações e configure uma senha de demonstração com `--password`; não use senha real.

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

A suíte automatizada cobre autenticação, RBAC, usuários, oferta acadêmica, matrícula, vagas, chamada, frequência, notas, exame, auditoria, seed, fluxos ponta a ponta e todos os módulos das Fases 2 e 3. A CI executa `python manage.py check`, `python manage.py makemigrations --check --dry-run` e `pytest` nos bancos **SQLite** e **PostgreSQL 16**. Não há uma contagem fixa de testes nesta documentação.

## Fora do escopo

API pública, integrações externas, aplicativo mobile, IA, auto-matrícula e meios de pagamento não estão implementados. API e integrações foram avaliadas no [estudo técnico](docs/SGA-13-ESTUDO-API-INTEGRACOES.md).


## Estado atual — 20/11/2026

| Fase | Estado | Entregas |
| --- | --- | --- |
| Fase 1/MVP | Concluída | Núcleo acadêmico descrito neste documento. |
| Fase 2 | Concluída | Materiais e comunicados (PR #66), calendário/grade/conflitos (PR #67), relatórios (PR #68, #70), transferências (PR #69, #70), recuperação de senha e notificações (PR #73, ajustes na #75). |
| Fase 3 | Implementada | Pré-requisitos e aproveitamento (PR #76), painel gerencial (PR #77), documentos oficiais (PR #78) e financeiro básico (PR #79), conforme a [especificação da Fase 3](docs/SGA-12-ESPECIFICACAO-FASE-3.md). |
| Estudos | Somente estudo | API pública e integrações ([SGA-13](docs/SGA-13-ESTUDO-API-INTEGRACOES.md)): recomendação de não expor API nesta evolução. App mobile e IA ([SGA-14](docs/SGA-14-ESTUDO-MOBILE-IA.md)): recomendação de não implementar nesta evolução. |

“Fora do MVP” nos trechos da Fase 1 significa fora do escopo **original**, não ausente do código atual. As seções de estado de 08/10/2026 foram substituídas por esta; o histórico permanece no Git.
