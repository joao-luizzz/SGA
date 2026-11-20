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

A matriz acima cobre a Fase 1. A rastreabilidade das Fases 2 e 3 está nas seções abaixo.

## Referências

- [Requisitos](SGA-03-REQUISITOS.md)
- [Regras](SGA-02-REGRAS-DE-NEGOCIO.md)
- [Casos de uso](SGA-06-CASOS-DE-USO.md)


## Estado atual — 20/11/2026

| Fase | Estado | Entregas |
| --- | --- | --- |
| Fase 1/MVP | Concluída | Núcleo acadêmico descrito neste documento. |
| Fase 2 | Concluída | Materiais e comunicados (PR #66), calendário/grade/conflitos (PR #67), relatórios (PR #68, #70), transferências (PR #69, #70), recuperação de senha e notificações (PR #73, ajustes na #75). |
| Fase 3 | Implementada | Pré-requisitos e aproveitamento (PR #76), painel gerencial (PR #77), documentos oficiais (PR #78) e financeiro básico (PR #79), conforme a [especificação da Fase 3](SGA-12-ESPECIFICACAO-FASE-3.md). |
| Estudos | Somente estudo | API pública e integrações ([SGA-13](SGA-13-ESTUDO-API-INTEGRACOES.md)): recomendação de não expor API nesta evolução. App mobile e IA não foram implementados. |

“Fora do MVP” nos trechos da Fase 1 significa fora do escopo **original**, não ausente do código atual. As seções de estado de 08/10/2026 foram substituídas por esta; o histórico permanece no Git.

## Rastreabilidade das extensões da Fase 2

| Issue / entrega | Estado | Evidência principal |
| --- | --- | --- |
| #34 — Materiais e comunicados | Concluída | PR #66; `apps/materials/`, `apps/communications/` e testes. |
| #33 — Calendário, grade e conflitos | Concluída | PR #67; `HorarioTurma`, `EventoCalendario` e testes de conflito. |
| #36, #49, #61 — Transferências | Concluídas | PR #69; `apps/transfers/` e `tests/test_transfers/`. |
| #50, #62 — Relatórios, risco e impressão | Concluídas | PR #68 e #70; `get_relatorio_turmas`, `identificar_risco_academico`, CSV e impressão. |
| #51 — Integração transferências + relatórios | Concluída | PR #70; `tests/test_integration/test_semana5_flow.py`. |
| #35, #47, #59 — Recuperação de senha | Concluídas | PR #73 e #75; `accounts/recovery.py`, `tests/test_accounts/test_recovery.py`. |
| #48, #60 — Notificações | Concluídas | PR #73; `apps/notifications/` e `tests/test_notifications/`. |

## Rastreabilidade da Fase 3 (#37)

| RF | CU | RN | Implementação | Testes |
| --- | --- | --- | --- | --- |
| RF36 | CU20 | RN18, RN27 | `PreRequisito`, `adicionar_pre_requisito`, `remover_pre_requisito` (PR #76) | `tests/test_academics/test_prerequisitos.py` |
| RF37 | CU21 | RN05–RN08, RN19 | `get_pre_requisitos_pendentes` em `matricular_aluno_administrativo` (PR #76) | idem |
| RF38 | CU22 | RN20, RN27 | `Aproveitamento`, `registrar_aproveitamento` (PR #76) | idem |
| RF39 | CU23 | RN20, RN27 | `analisar_aproveitamento` (PR #76) | idem |
| RF40 | CU25 | RN21, RN22, RN27 | `DocumentoEmitido`, `emitir_documento` (PR #78) | `tests/test_documents/` |
| RF41 | CU26 | RN11–RN14, RN21, RN22 | histórico com snapshot de resultados (PR #78) | idem |
| RF42 | CU27 | RN23 | `documents:verificar`, `verificar_documento` (PR #78) | idem |
| RF43 | CU28 | RN24, RN27 | `Cobranca`, `lancar_cobranca`, `registrar_pagamento`, `cancelar_cobranca` (PR #79) | `tests/test_finance/` |
| RF44 | CU29 | RN24, RN25 | `listar_cobrancas`, `resumir_cobrancas` (PR #79) | idem |
| RF45 | CU30 | RN26 | `get_indicadores_gerenciais`, `academics/painel.py` (PR #77, #79) | `tests/test_academics/test_painel_gerencial.py` |

RNF07–RNF10 são cobertos pelos testes de permissão, paginação e limite de tentativas dos mesmos módulos e pela CI em SQLite e PostgreSQL 16.
