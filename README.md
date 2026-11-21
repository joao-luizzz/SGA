# SGA — Sistema de Gestão Acadêmica

[![CI](https://github.com/joao-luizzz/SGA/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/joao-luizzz/SGA/actions/workflows/ci.yml)

**Versão 3.0 — entrega final (Fases 1, 2 e 3) · novembro de 2026**

O SGA é um sistema web de gestão acadêmica para ensino superior. Ele centraliza oferta de disciplinas e turmas, matrícula, frequência, notas, comunicação, documentos e financeiro, com acesso isolado para **Aluno**, **Professor**, **Secretaria** e **Coordenação**.

Projeto da disciplina **Laboratório de Engenharia de Software**, com o professor Rodrigo Salgado.

## Sumário

- [Funcionalidades](#funcionalidades)
- [Regras acadêmicas](#regras-acadêmicas)
- [Arquitetura](#arquitetura)
- [Como executar](#como-executar)
- [Demonstração](#demonstração)
- [Testes e qualidade](#testes-e-qualidade)
- [Documentação](#documentação)
- [Como contribuir](#como-contribuir)
- [Implantação fora do ambiente local](#implantação-fora-do-ambiente-local)
- [Escopo e estado do projeto](#escopo-e-estado-do-projeto)
- [Equipe](#equipe)

## Funcionalidades

| Papel | O que pode fazer |
| --- | --- |
| **Aluno** | Painel com comunicados recentes; matrículas, boletim (MP, MF, situação) e frequência; materiais das próprias turmas; mural de avisos; notificações de nota, frequência e comunicados; transferências e aproveitamentos próprios; **declaração de matrícula e histórico escolar** com código de verificação; **extrato financeiro**. |
| **Professor** | Turmas próprias; chamada completa por aula; notas P1, P2 e Trabalho; exame apenas para alunos elegíveis; publicação de materiais; grade horária com sala. |
| **Secretaria** | Cadastro e ativação de Alunos e Professores; matrícula com controle de vagas e **verificação de pré-requisitos**; status e retentativa; comunicados gerais e por perfil; registro de transferências e **aproveitamentos**; emissão de **documentos oficiais**; **cobranças** (lançar, dar baixa e cancelar); **painel gerencial**. |
| **Coordenação** | Cursos, disciplinas, turmas, grade horária e alocação docente; **pré-requisitos** com bloqueio de ciclos; análise de transferências e aproveitamentos; relatórios acadêmicos com risco, CSV e impressão; comunicados por curso e turma; materiais; **painel gerencial**. |
| **Visitante** | Login, recuperação de senha e **verificação pública de documento** pelo código. |

Todas as alterações sensíveis (notas, frequência, pré-requisitos, aproveitamentos, documentos e cobranças) ficam registradas em um log de auditoria imutável.

## Regras acadêmicas

```text
MP = (P1 + P2 + Trabalho) / 3
MP >= 6            => aprovado direto
4 <= MP < 6        => elegível ao exame (com frequência >= 75%)
MP < 4             => reprovado por nota
MF = (MP + Exame) / 2; MF >= 6 => aprovado após exame
Frequência < 75%   => reprovado por falta, sem direito a exame
```

As comparações usam a média **exata**; o arredondamento para duas casas é apenas de exibição. Por exemplo, MP 5,9967 aparece como 6,00, mas leva o aluno a exame. Regras completas (RN01–RN27) em [SGA-02](docs/SGA-02-REGRAS-DE-NEGOCIO.md).

## Arquitetura

Monólito **Django** com renderização no servidor, sem SPA.

- **Backend:** Python 3.12+, Django 5.1.
- **Interface:** Django Templates, Bootstrap 5 e HTMX pontual.
- **Banco:** PostgreSQL 16 (SQLite opcional para rodar testes localmente).
- **Infraestrutura:** Docker Compose (aplicação, banco e Mailpit).
- **Testes:** pytest e pytest-django, com CI no GitHub Actions.

Regras de negócio ficam em `services.py`, consultas reutilizáveis em `selectors.py` e permissões em decorators/mixins, revalidadas nos services. Operações concorrentes usam `transaction.atomic`, `select_for_update` e compare-and-set.

| App | Responsabilidade |
| --- | --- |
| `accounts` | Usuário customizado (e-mail), papéis, login, troca e recuperação de senha, auditoria |
| `academics` | Cursos, disciplinas, turmas, grade e calendário, pré-requisitos, aproveitamentos, relatórios e painel gerencial |
| `enrollment` | Matrícula administrativa, vagas, status e verificação de pré-requisitos |
| `attendance` | Chamada e cálculo de frequência |
| `assessments` | Notas, exame, médias, situação acadêmica e `seed_demo` |
| `materials` | Materiais por turma, com download protegido |
| `communications` | Mural e comunicados segmentados por perfil, curso e turma |
| `notifications` | Central pessoal de notificações |
| `transfers` | Transferências de entrada e saída |
| `documents` | Declaração e histórico imutáveis e verificação pública |
| `finance` | Cobranças e extrato do aluno |

```text
SGA/
├── apps/              # apps Django listados acima
├── config/            # settings (base.py, local.py) e URLs
├── templates/         # templates por app e componentes compartilhados (includes/)
├── static/            # CSS do tema, relatórios e documentos
├── tests/             # testes por app e de integração
├── docs/              # documentação técnica (SGA-01 a SGA-14)
├── docker-compose.yml # web, db (PostgreSQL 16) e mailpit
└── .env.example       # variáveis de ambiente comentadas
```

## Como executar

Pré-requisitos: **Docker** e **Docker Compose**.

```bash
git clone https://github.com/joao-luizzz/SGA.git
cd SGA
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

| Serviço | Endereço |
| --- | --- |
| Aplicação | http://localhost:8000 |
| Mailpit (e-mails da demonstração) | http://localhost:8025 |

Para criar uma conta real de Secretaria, que exige troca de senha no primeiro acesso:

```bash
docker compose exec web python manage.py create_secretaria_user
```

O comando aceita `--email`, `--full-name` e `--password`.

## Demonstração

O `seed_demo` é idempotente. Ele cria as contas abaixo, uma turma com cenários de aprovação direta, exame e reprovação por falta, e os cenários da Fase 3: pré-requisito, aproveitamento pendente e mensalidades, uma delas em atraso. A senha de todas as contas é a definida em `--password` (padrão do comando: `SgaDemo2026!`). Use apenas essas contas em apresentações.

| Papel / cenário | E-mail |
| --- | --- |
| Coordenação | `coordenacao.demo@sga.edu.br` |
| Secretaria | `secretaria.demo@sga.edu.br` |
| Professor | `professor.demo@sga.edu.br` |
| Aluno aprovado direto | `aluno.aprovado@sga.edu.br` |
| Aluno elegível ao exame | `aluno.exame@sga.edu.br` |
| Aluno reprovado por falta | `aluno.falta@sga.edu.br` |

O roteiro da apresentação, em 13 passos pelos quatro papéis, está em [SGA-07](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md).

**E-mail de recuperação de senha:** por padrão, os e-mails ficam em memória e nada é enviado. Para vê-los chegar no Mailpit, configure no `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailpit
EMAIL_PORT=1025
EMAIL_USE_TLS=False
```

Depois rode `docker compose restart web`.

## Testes e qualidade

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest
git diff --check
```

Com um ambiente virtual local, a suíte também roda em SQLite: `USE_SQLITE=True pytest`.

- **574 testes** e **cobertura de 90,79%** (mínimo exigido: 85%).
- A CI roda `check`, a verificação de migrations e `pytest` em **SQLite** e **PostgreSQL 16** a cada PR.
- Os testes cobrem regras acadêmicas e suas fronteiras, permissões (403/404) por papel, constraints, concorrência, auditoria, seed e fluxos ponta a ponta. O roteiro da demonstração também é executado como teste (`tests/test_integration/test_roteiro_final.py`).

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [Documento consolidado](docs/SGA-DOCUMENTO-CONSOLIDADO.md) | Visão geral para apresentação |
| [SGA-01 Escopo](docs/SGA-01-ESCOPO.md) | Escopo e roadmap |
| [SGA-02 Regras de negócio](docs/SGA-02-REGRAS-DE-NEGOCIO.md) | RN01–RN27 |
| [SGA-03 Requisitos](docs/SGA-03-REQUISITOS.md) | RF01–RF45 e RNF |
| [SGA-04 Modelagem de dados](docs/SGA-04-MODELAGEM-DADOS.md) | 18 entidades e MER |
| [SGA-05 Rastreabilidade](docs/SGA-05-RASTREABILIDADE.md) | RF ↔ CU ↔ RN ↔ evidência |
| [SGA-06 Casos de uso](docs/SGA-06-CASOS-DE-USO.md) | CU01–CU30 |
| [SGA-07 Roteiro de demonstração](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md) | Roteiro, checklist e validações da entrega |
| [SGA-08 Preparação da Fase 2](docs/SGA-08-PREPARACAO-FASE-2.md) | Planejamento técnico (registro histórico) |
| [SGA-09 Transferências](docs/SGA-09-TRANSFERENCIAS.md) | Fluxo e regras de transferência |
| [SGA-10 Relatórios](docs/SGA-10-RELATORIOS-INTEGRACAO.md) | Relatórios, risco, CSV e impressão |
| [SGA-11 Recuperação e notificações](docs/SGA-11-RECUPERACAO-NOTIFICACOES.md) | Segurança da recuperação de senha e notificações |
| [SGA-12 Especificação da Fase 3](docs/SGA-12-ESPECIFICACAO-FASE-3.md) | Pré-requisitos, documentos, financeiro e painel |
| [SGA-13 Estudo de API](docs/SGA-13-ESTUDO-API-INTEGRACOES.md) | API pública e integrações |
| [SGA-14 Estudo de mobile e IA](docs/SGA-14-ESTUDO-MOBILE-IA.md) | App mobile e inteligência artificial |

## Como contribuir

O fluxo de branches (`feature/<nome>` ou `fix/<nome>` a partir da `develop`), os padrões de código e o checklist de PR estão em [CONTRIBUTING.md](CONTRIBUTING.md). As regras do projeto estão em [AGENTS.md](AGENTS.md).

## Implantação fora do ambiente local

O projeto usa `config.settings.local`, pensado para desenvolvimento e demonstração. Para expor o sistema em um servidor, defina no ambiente pelo menos:

- `DEBUG=False`;
- uma `SECRET_KEY` própria e secreta;
- `ALLOWED_HOSTS` com o domínio real;
- `PASSWORD_RESET_DOMAIN` e `PASSWORD_RESET_USE_HTTPS=True`;
- um SMTP real.

Os valores padrão (`DEBUG=True` e uma `SECRET_KEY` de exemplo) não são seguros para produção. Arquivos de materiais nunca são servidos diretamente: o download passa por uma view que confere o acesso à turma.

## Escopo e estado do projeto

| Fase | Estado | Entregas |
| --- | --- | --- |
| Fase 1/MVP | Concluída | Autenticação e papéis, usuários, oferta acadêmica, matrícula, frequência, notas, exame e auditoria |
| Fase 2 | Concluída | Materiais e comunicados, calendário e grade, relatórios, transferências, recuperação de senha e notificações (PRs #66–#75) |
| Fase 3 | Concluída | Pré-requisitos e aproveitamento, painel gerencial, documentos oficiais e financeiro básico (PRs #74–#79) |
| Estudos | Concluídos | API pública e integrações ([SGA-13](docs/SGA-13-ESTUDO-API-INTEGRACOES.md)); app mobile e IA ([SGA-14](docs/SGA-14-ESTUDO-MOBILE-IA.md)). Recomendação: não implementar nesta evolução |
| Fechamento | Concluído | Documentação, validação com instalação limpa, auditoria das issues, conferência visual, auditoria geral e release `v3.0.0` (PRs #80–#90) |

**Fora do escopo:** API pública, integrações externas, aplicativo mobile, IA, auto-matrícula e meios de pagamento.

## Equipe

| Integrante | Principais entregas |
| --- | --- |
| Alexandre Hesse | Catálogo acadêmico, turmas, grade horária e calendário |
| Andrey Kerges Nascimento | Usuários, matrícula e transferências |
| João Luiz | Base do projeto, autenticação e RBAC, recuperação de senha e notificações, Fase 3, documentação e fechamento |
| Max Iago Villafan | Avaliações, médias e relatórios acadêmicos |
| Vitor Augusto | Frequência, auditoria, materiais e comunicados |

Licença [MIT](LICENSE).
