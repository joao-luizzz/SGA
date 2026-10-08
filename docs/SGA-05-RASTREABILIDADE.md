# SGA — Sistema de Gestão Acadêmica

## Matriz de rastreabilidade

| Metadado | Valor |
| --- | --- |
| Versão | **1.0 — MVP Fase 1 concluído** |
| Data | **31 de agosto de 2026** |

| RF | CU | RN | Entidades / evidência |
| --- | --- | --- | --- |
| RF01 | CU01 | RN01, RN02 | `CustomUser`, autenticação por sessão |
| RF02 | CU02 | RN01 | `CustomUser`, logout POST |
| RF03 | CU03 | RN02 | `CustomUser.must_change_password` |
| RF04 | CU01–CU19 | RN01 | `CustomUser`, decorators e filtros de recurso |
| RF06 | CU04 | RN01, RN11–RN14 | `Matricula`, `Nota`, `Falta` |
| RF07 | CU05 | RN01, RN09–RN11 | `Matricula`, `Falta` |
| RF10 | CU06 | RN01, RN09, RN10, RN15 | `Turma`, `Matricula`, `Falta`, `AuditoriaLog` |
| RF11 | CU07 | RN01, RN12, RN15, RN16 | `Matricula`, `Nota`, `AuditoriaLog` |
| RF13 | CU08 | RN01, RN07 | `Turma`, `Matricula`, `CustomUser` |
| RF14 | CU09 | RN01–RN03 | `CustomUser` Professor |
| RF15 | CU10 | RN01–RN03 | `CustomUser` Aluno |
| RF16 | CU11 | RN05–RN08, RN16 | `Turma`, `Matricula`, `CustomUser` |
| RF17 | CU09, CU10 | RN02, RN03 | `CustomUser`, histórico relacionado |
| RF20 | CU13 | RN01, RN04 | `Curso` |
| RF21 | CU14 | RN01, RN04 | `Curso`, `Disciplina` |
| RF22 | CU15 | RN01, RN04, RN05 | `Turma` |
| RF23 | CU16 | RN01, RN04, RN05 | `Turma`, `CustomUser` Professor |
| RF27 | CU04, CU07, CU17 | RN11–RN14 | `Nota`, `Matricula`, `Falta` |
| RF28 | CU05, CU06 | RN09–RN11 | `Falta`, `Turma`, `Matricula` |
| RF29 | CU11 | RN05, RN06 | `Turma`, `Matricula` |
| RF30 | CU06, CU07, CU17 | RN15 | `AuditoriaLog`, `Nota`, `Falta` |
| RF31 | CU01, CU06, CU07, CU11, CU13–CU17 | RN16, RN17 | formulários, serviços e constraints |
| RF32 | CU17 | RN11, RN13, RN14 | `Nota`, `Matricula`, `Falta` |
| RF33 | CU04 | RN11–RN14 | resultados calculados |
| RF34 | CU18 | RN08, RN16 | `Matricula`, `Turma`, `Falta`, `Nota` |
| RF35 | CU12, CU19 | RN07, RN16 | `Matricula` |

## Cobertura de qualidade

RN17 é evidenciada por testes unitários, de integração e de permissões, além da CI que executa `python manage.py check`, `python manage.py makemigrations --check --dry-run` e `pytest` nos jobs SQLite e PostgreSQL 16.

Não há RF, RN ou CU do Roadmap nesta matriz: recursos futuros não têm implementação a rastrear na Fase 1.

## Referências

- [Requisitos](SGA-03-REQUISITOS.md)
- [Regras](SGA-02-REGRAS-DE-NEGOCIO.md)
- [Casos de uso](SGA-06-CASOS-DE-USO.md)


## Estado atual e rastreabilidade das extensões — 08/10/2026

As matrizes RF/CU/RN acima preservam a rastreabilidade da **Fase 1/MVP**. A tabela abaixo registra o estado das entregas da Fase 2 na develop após o merge da PR #70; não cria requisitos novos nem altera o contrato da Fase 1.

| Issue / entrega | Estado na develop | Evidência principal |
| --- | --- | --- |
| #36 — Semana 5 | Concluída | PR #69 implementa transferências; PR #70 conclui integração, relatórios e validação da Semana 5. |
| #49 — Solicitação de transferência | Concluída | PR #69; `apps/transfers/` e `tests/test_transfers/`. |
| #50 — Relatórios acadêmicos | Concluída | PR #68; consultas e testes de relatórios em `apps/academics/` e `tests/test_academics/`. |
| #51 — Integração transferências + relatórios | Concluída | PR #70; `tests/test_integration/test_semana5_flow.py`. |
| #61 — Análise da transferência | Concluída | PR #69; services, permissões e testes em `apps/transfers/` e `tests/test_transfers/`. |
| #62 — Relatórios, risco e impressão | Concluída | PR #70; `identificar_risco_academico`, filtros, CSV, impressão e testes em `tests/test_academics/`. |
| #35 — Recuperação de senha e notificações | Pendente | Fluxos e testes correspondentes ainda não existem na develop. Ver issues #47–#48 e #59–#60. |
| #47 e #59 — Recuperação de senha | Pendentes | Solicitação segura, redefinição e testes de token ainda não existem na develop. |
| #48 e #60 — Notificações | Pendentes | Central, leitura/marcação, isolamento e testes de notificações ainda não existem na develop; #60 permanece dedicada a notificações. |
| #37 — Fase 3 | Futura | Planejada para etapa posterior; não faz parte das entregas integradas da Fase 2. |

PR #66 (materiais/comunicados), PR #67 (calendário/grade/conflitos), PR #68 (relatórios), PR #69 (transferências) e PR #70 (conclusão dos relatórios e integração da Semana 5) estão integradas na develop. “Fora do MVP” continua significando fora do escopo original da Fase 1, não necessariamente ausente do código atual.
