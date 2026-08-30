# SGA — Roteiro de demonstração e entrega

## Preparar os dados

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

O comando é idempotente: pode ser executado novamente sem duplicar usuários, turma, matrículas, notas, chamadas ou auditorias.

## Credenciais de demonstração

Senha padrão de todas as contas: `SgaDemo2026!`

| Papel/cenário | E-mail |
| :--- | :--- |
| Secretaria | `secretaria.demo@sga.edu.br` |
| Coordenação | `coordenacao.demo@sga.edu.br` |
| Professor | `professor.demo@sga.edu.br` |
| Aluno aprovado direto | `aluno.aprovado@sga.edu.br` |
| Aluno elegível ao exame | `aluno.exame@sga.edu.br` |
| Aluno reprovado por falta | `aluno.falta@sga.edu.br` |

Em uma demonstração compartilhada, altere a senha com `python manage.py seed_demo --password '...'` e não reutilize credenciais reais.

## Roteiro curto de apresentação (10 minutos)

1. Coordenação (1 min): entrar, mostrar Curso/Disciplina ligados diretamente, Turma completa e Professor alocado.
2. Secretaria (1 min): mostrar cadastro/inativação e matricular um Aluno em Turma válida; explicar vagas e duplicidade ativa.
3. Professor — frequência (2 min): abrir apenas a própria Turma, registrar/editar uma chamada e mostrar o relatório.
4. Professor — notas (2 min): lançar P1, P2 e Trabalho em lote; mostrar validação 0–10 e situação calculada.
5. Exame (1 min): usar o Aluno Elegível, lançar Exame e mostrar que o Aluno com frequência abaixo de 75% é bloqueado.
6. Aluno (2 min): entrar com cada cenário e mostrar boletim, médias, frequência e situação sem acesso a dados alheios.
7. Qualidade (1 min): mostrar testes, CI verde, auditoria imutável e fronteira entre MVP e roadmap.

## Divisão sugerida de fala

| Integrante | Parte |
| :--- | :--- |
| Andrey Kerges Nascimento | Cadastro, Secretaria, matrícula e vagas |
| Alexandre Hesse | Coordenação, Cursos, Disciplinas e Turmas |
| Max Iago Villafan | Notas, médias, Exame Final e boletim |
| Vitor Augusto | Frequência, reprovação por falta e auditoria |
| João Luiz | Arquitetura, testes, CI, seed, escopo e encerramento |

Se algum integrante estiver ausente, João conduz a abertura/encerramento e o integrante anterior assume a próxima etapa do roteiro.

## Checklist pré-apresentação

- [ ] Branch `develop` atualizada; `main` não foi alterada.
- [ ] Containers `web` e `db` em execução e PostgreSQL saudável.
- [ ] Migrations aplicadas e `manage.py check` sem erros.
- [ ] `manage.py makemigrations --check --dry-run` informa `No changes detected`.
- [ ] Suíte Pytest completa e CI do PR verdes.
- [ ] `seed_demo` executado e logins das seis contas conferidos.
- [ ] Fluxos de cadastro, matrícula, chamada, notas e boletim revisados no navegador.
- [ ] Aluno aprovado direto exibe MP 8,00.
- [ ] Aluno elegível exibe MP 5,00 e permite Exame.
- [ ] Aluno com 50% de frequência exibe `Reprovado por Falta` e não aceita Exame.
- [ ] Projetor, resolução, zoom do navegador e conexão preparados.
- [ ] Nenhum dado ou senha pessoal aparece na apresentação.

## MVP entregue

- Autenticação por sessão e RBAC para os quatro papéis.
- Cadastro/inativação de Alunos e Professores.
- Cursos, Disciplinas, Turmas e alocação docente.
- Matrícula administrativa e controle de vagas.
- Chamada, frequência e auditoria de faltas.
- P1, P2, Trabalho, Exame, médias, situação e auditoria de notas.
- Boletim isolado por Aluno.
- Seed de demonstração, testes automatizados e CI.

## Roadmap — não demonstrar como funcionalidade pronta

Auto-matrícula, materiais, calendário, comunicados, recuperação de senha, transferências, documentos, financeiro, aplicativo mobile, integrações externas e pré-requisitos estão fora da Fase 1.
