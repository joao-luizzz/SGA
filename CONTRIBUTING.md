# Como contribuir com o SGA

Guia rápido para a equipe. As regras completas do projeto estão em [AGENTS.md](AGENTS.md).

## Ambiente

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

A aplicação fica em `http://localhost:8000`. As contas de demonstração estão em [SGA-07](docs/SGA-07-ROTEIRO-DEMO-E-ENTREGA.md).

## Fluxo de trabalho

1. Parta sempre da `develop` atualizada: `git switch develop && git pull`.
2. Crie uma branch por issue: `feature/<nome>` ou `fix/<nome>` (AGENTS.md). Também são usados `docs/`, `chore/` e `ci/`.
3. Nunca trabalhe direto em `develop` ou `main`.
4. Abra a PR para `develop`, referencie a issue (`Refs #NN`) e descreva o que mudou e como foi validado.
5. A PR só é integrada com o CI verde (SQLite e PostgreSQL 16).

## Padrões de código

- Monólito Django com apps em `apps/`.
- Regras de negócio em `services.py`; consultas reutilizáveis em `selectors.py`; views finas.
- Permissões por papel com `role_required`/`RoleRequiredMixin`, revalidadas nos services. Esconder botão no template não é segurança.
- Operações que mudam estado e podem concorrer usam `transaction.atomic`, `select_for_update` e, quando houver decisão única, compare-and-set (veja `transfers/services.py`).
- Alterações sensíveis registram `AuditoriaLog` via `accounts.services.registrar_auditoria`.
- Interface: Django Templates, Bootstrap 5 e HTMX apenas quando houver ganho real de atualização parcial. Preserve `base.html` e os componentes de `templates/includes/`.
- Não adicione React, Vite, Tailwind, SPA, Django REST Framework ou JWT sem aprovação explícita da equipe.

## Regras acadêmicas que não podem quebrar

- `MP = (P1 + P2 + Trabalho) / 3`; `MP >= 6` aprova; `4 <= MP < 6` vai a exame; `MP < 4` reprova por nota.
- `MF = (MP + Exame) / 2`; aprova com `MF >= 6`.
- Frequência abaixo de 75% reprova por falta e bloqueia o exame.

Regras completas em [SGA-02](docs/SGA-02-REGRAS-DE-NEGOCIO.md).

## Antes de abrir a PR

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest
git diff --check
```

- Toda regra nova vem com teste, incluindo os casos de permissão (403/404) para cada papel.
- A cobertura mínima é de 85% (o CI falha abaixo disso).
- Se a mudança altera regra, requisito, modelo ou fluxo, atualize os documentos em `docs/` (regras SGA-02, requisitos SGA-03, modelo SGA-04, rastreabilidade SGA-05, casos de uso SGA-06).
- Nova migration: confira que ela não apaga nem altera dados existentes sem intenção explícita.
