# SGA — Sistema de Gestão Acadêmica

## Documento consolidado da Fase 1

| Metadado | Detalhe |
| :--- | :--- |
| **Versão** | `1.0` |
| **Data** | Agosto de 2026 |
| **Produto** | SGA — Sistema de Gestão Acadêmica |
| **Arquitetura** | Monólito Django com Templates, Bootstrap 5 e HTMX |

## 1. Escopo entregue

O MVP atende quatro papéis no modelo oficial `CustomUser`:

- Aluno consulta apenas as próprias matrículas, notas, médias, frequência e situação.
- Professor consulta apenas as turmas em que foi alocado e lança notas e chamada.
- Secretaria cadastra/inativa Alunos e Professores e realiza matrícula administrativa.
- Coordenação mantém Cursos e Disciplinas, abre Turmas e aloca Professores.

Recursos transversais incluem sessão Django, RBAC, troca obrigatória da primeira senha, controle de vagas, auditoria imutável de notas e faltas e cálculos acadêmicos derivados.

## 2. Regras acadêmicas

```text
MP = (P1 + P2 + Trabalho) / 3

MP >= 6,00        -> Aprovado Direto
4,00 <= MP < 6,00 -> Elegível para Exame Final
MP < 4,00         -> Reprovado por Nota

MF = (MP + Exame) / 2
MF >= 6,00        -> Aprovado após Exame
MF < 6,00         -> Reprovado por Nota

Frequência < 75%  -> Reprovado por Falta e Exame bloqueado
```

Enquanto P1, P2 ou Trabalho estiver ausente, a situação é `Em andamento`. O Exame só pode ser criado ou editado quando a média parcial está na faixa elegível e a frequência é de pelo menos 75%.

## 3. Decisões de dados

- `CustomUser` é a única entidade de usuário; os papéis ficam em `role`.
- `Disciplina.curso` é uma chave estrangeira direta.
- Horários são armazenados em `Turma.horarios` e validados pelo domínio.
- `Matricula` representa uma tentativa do aluno na turma e aceita `ATIVA`, `TRANCADA`, `CONCLUIDA` ou `CANCELADA`.
- `Nota` referencia a `Matricula` e aceita os tipos `P1`, `P2`, `TRABALHO` e `EXAME`.
- Uma restrição garante uma nota por matrícula e tipo.
- Média, frequência, vagas ocupadas e situação são calculadas, não persistidas.
- `AuditoriaLog` registra criação/edição de Nota e Falta e impede edição/exclusão do próprio log.

## 4. Fluxo ponta a ponta

1. A Coordenação cria Curso e Disciplina, abre a Turma e aloca o Professor.
2. A Secretaria cadastra Aluno e Professor e matricula o Aluno em uma Turma válida.
3. O Professor registra chamadas e lança P1, P2 e Trabalho.
4. O sistema calcula média, frequência e situação.
5. Se elegível, o Professor lança o Exame Final.
6. O Aluno consulta o próprio boletim.

## 5. Segurança e integridade

- Views usam decorators de papel e filtram recursos pelo usuário autenticado.
- Serviços repetem as validações críticas e operam lotes dentro de transações.
- Somente a Secretaria matricula; somente a Coordenação abre turmas/aloca professor.
- Professor alheio não lança nota ou frequência.
- Matrícula cancelada/trancada não recebe novos lançamentos e não bloqueia nova tentativa ativa.
- Notas são limitadas no formulário, serviço, validadores e banco de dados.

## 6. Roadmap fora da Fase 1

Auto-matrícula, materiais, calendário, comunicados, recuperação de senha, transferências, documentos, financeiro, aplicativo mobile, integrações externas e pré-requisitos não fazem parte do MVP entregue.

## 7. Demonstração e entrega

O comando `python manage.py seed_demo` prepara contas e três cenários acadêmicos idempotentes. Credenciais, roteiro, checklist e divisão da apresentação estão em [SGA-07-ROTEIRO-DEMO-E-ENTREGA.md](SGA-07-ROTEIRO-DEMO-E-ENTREGA.md).
