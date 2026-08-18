# SGA — Instruções do projeto

## Stack obrigatória
- Python 3.12+, Django 5+, PostgreSQL, Docker Compose.
- Django Templates, Bootstrap 5 e HTMX.
- Testes com pytest e pytest-django.
- Não adicionar React, Vite, Tailwind, SPA, Django REST Framework ou JWT
  sem aprovação explícita.

## Arquitetura
- Monólito Django.
- Apps em `apps/`.
- Regras de negócio em `services.py`.
- Consultas reutilizáveis em `selectors.py`.
- Permissões por papel em decorators/mixins.
- `CustomUser` é o modelo de usuário oficial.
- Evite lógica de negócio em templates e views.

## Qualidade
Antes de concluir qualquer alteração, execute:
1. `docker compose exec web python manage.py check`
2. `docker compose exec web pytest`
3. `git diff --check`

## Git
- Nunca trabalhe diretamente em `develop` ou `main`.
- Use branches `feature/<nome>` ou `fix/<nome>`.
- Não faça push, commit ou merge sem pedir confirmação.
- Não altere arquivos não relacionados à issue.

## Interface
- Preserve `base.html` e os componentes compartilhados.
- Use Bootstrap antes de criar CSS próprio.
- Use HTMX apenas quando houver benefício real de atualização parcial.
- Toda tela deve respeitar permissões de Aluno, Professor, Secretaria e Coordenação.

## Regras acadêmicas críticas
- Média parcial = (P1 + P2 + Trabalho) / 3.
- MP >= 6: aprovado.
- 4 <= MP < 6: exame.
- MP < 4: reprovado por nota.
- Média final = (MP + Exame) / 2; aprovação com MF >= 6.
- Frequência mínima = 75%; abaixo disso reprova por falta e não faz exame.