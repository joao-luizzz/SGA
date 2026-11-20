# SGA — Sistema de Gestão Acadêmica

## Requisitos da Fase 1

| Metadado | Valor |
| --- | --- |
| Versão | **1.0 — MVP Fase 1 concluído** |
| Data | **31 de agosto de 2026** |

| ID | Requisito | Ator | Estado na Fase 1 |
| --- | --- | --- | --- |
| RF01 | Autenticar por e-mail e senha e direcionar ao painel do papel. | Todos | Implementado |
| RF02 | Encerrar a sessão por requisição POST. | Todos | Implementado |
| RF03 | Exigir troca da senha inicial quando `must_change_password=True`. | Todos | Implementado |
| RF04 | Restringir páginas e operações por papel e recurso associado. | Sistema | Implementado |
| RF06 | Exibir ao Aluno suas notas, médias e situação. | Aluno | Implementado |
| RF07 | Exibir ao Aluno sua frequência por turma. | Aluno | Implementado |
| RF10 | Registrar chamada completa por turma e data. | Professor | Implementado |
| RF11 | Lançar e editar P1, P2 e Trabalho em turma própria ativa. | Professor | Implementado |
| RF13 | Consultar alunos com matrícula ativa da própria turma. | Professor | Implementado |
| RF14 | Criar, editar, listar, ativar e inativar contas de Professor. | Secretaria | Implementado |
| RF15 | Criar, editar, listar, ativar e inativar contas de Aluno. | Secretaria | Implementado |
| RF16 | Criar matrícula administrativa com validação de aluno, turma, vagas e duplicidade. | Secretaria | Implementado |
| RF17 | Preservar histórico acadêmico ao inativar conta. | Secretaria | Implementado |
| RF20 | Criar, editar e inativar cursos. | Coordenação | Implementado |
| RF21 | Criar, editar e inativar disciplinas vinculadas diretamente a curso. | Coordenação | Implementado |
| RF22 | Criar, editar e inativar turmas com período, horários, sala e vagas. | Coordenação | Implementado |
| RF23 | Alocar Professor responsável à turma. | Coordenação | Implementado |
| RF27 | Calcular MP, MF e situação acadêmica sem persistir os resultados. | Sistema | Implementado |
| RF28 | Calcular frequência e reprovação por falta. | Sistema | Implementado |
| RF29 | Controlar vagas por matrículas ativas. | Sistema | Implementado |
| RF30 | Auditar criação e edição de notas e faltas de forma imutável. | Sistema | Implementado |
| RF31 | Validar dados em formulário, serviço e banco. | Sistema | Implementado |
| RF32 | Lançar Exame apenas para matrícula elegível. | Professor | Implementado |
| RF33 | Apresentar situação: em andamento, aprovado direto/após exame, elegível ou reprovado. | Sistema | Implementado |
| RF34 | Permitir retentativa apenas em nova turma/período, sem misturar o histórico. | Secretaria | Implementado |
| RF35 | Gerir status da matrícula ativa: trancar, cancelar ou concluir. | Secretaria | Implementado |

RF16 cobre a criação da matrícula; RF35 cobre a mudança de status posterior, sem duplicidade de escopo.

## Requisitos não funcionais implementados

| ID | Requisito | Estado na Fase 1 |
| --- | --- | --- |
| RNF01 | Monólito Django 5+ com Templates, HTMX e Bootstrap 5. | Implementado |
| RNF02 | PostgreSQL 16 e Docker Compose para execução da aplicação. | Implementado |
| RNF03 | Sessão Django, CSRF, hash de senha e e-mail único. | Implementado |
| RNF04 | Regras de negócio em serviços e consultas reutilizáveis em selectors. | Implementado |
| RNF05 | Suíte automatizada e CI em SQLite e PostgreSQL 16. | Implementado |
| RNF06 | Auditoria de Nota e Falta imutável. | Implementado |

## Limites dos requisitos da Fase 1

Os requisitos tabelados acima descrevem a Fase 1. As extensões posteriores não se tornam requisitos retroativos desta especificação. Os requisitos da Fase 3 (RF36–RF45, RNF07–RNF10) estão na seção abaixo.

## Referências

- [Regras de negócio](SGA-02-REGRAS-DE-NEGOCIO.md)
- [Matriz de rastreabilidade](SGA-05-RASTREABILIDADE.md)


## Estado atual — 20/11/2026

| Fase | Estado | Entregas |
| --- | --- | --- |
| Fase 1/MVP | Concluída | Núcleo acadêmico descrito neste documento. |
| Fase 2 | Concluída | Materiais e comunicados (PR #66), calendário/grade/conflitos (PR #67), relatórios (PR #68, #70), transferências (PR #69, #70), recuperação de senha e notificações (PR #73, ajustes na #75). |
| Fase 3 | Implementada | Pré-requisitos e aproveitamento (PR #76), painel gerencial (PR #77), documentos oficiais (PR #78) e financeiro básico (PR #79), conforme a [especificação da Fase 3](SGA-12-ESPECIFICACAO-FASE-3.md). |
| Estudos | Somente estudo | API pública e integrações ([SGA-13](SGA-13-ESTUDO-API-INTEGRACOES.md)): recomendação de não expor API nesta evolução. App mobile e IA ([SGA-14](SGA-14-ESTUDO-MOBILE-IA.md)): recomendação de não implementar nesta evolução. |
| Fechamento | Em andamento | Documentação final (PR #80), validação com instalação limpa (PR #81) e lacunas da auditoria das issues: comunicados no painel, filtro por turma na grade, testes de vínculo curricular e `CONTRIBUTING.md` (PR #82); correções da conferência visual em desktop e celular (PR #84). Pré-release `v3.0.0-rc1`. Pendentes: ensaio da apresentação (#53), merge em `main` e `v3.0.0`. |

“Fora do MVP” nos trechos da Fase 1 significa fora do escopo **original**, não ausente do código atual. As seções de estado de 08/10/2026 foram substituídas por esta; o histórico permanece no Git.

## Requisitos da Fase 3

Evidências de implementação e testes em [SGA-12](SGA-12-ESPECIFICACAO-FASE-3.md#rastreabilidade).

| ID | Requisito | Ator | Estado |
| --- | --- | --- | --- |
| RF36 | Manter pré-requisitos de disciplina com validação de ciclo | Coordenação | Implementado (PR #76) |
| RF37 | Bloquear matrícula sem pré-requisito cumprido, informando quais faltam | Secretaria | Implementado (PR #76) |
| RF38 | Registrar aproveitamento de disciplina | Secretaria | Implementado (PR #76) |
| RF39 | Analisar aproveitamento (deferir/indeferir) | Coordenação | Implementado (PR #76) |
| RF40 | Emitir declaração de matrícula | Aluno, Secretaria | Implementado (PR #78) |
| RF41 | Emitir histórico escolar | Aluno, Secretaria | Implementado (PR #78) |
| RF42 | Verificar autenticidade de documento por código | Público | Implementado (PR #78) |
| RF43 | Lançar, baixar e cancelar cobrança | Secretaria | Implementado (PR #79) |
| RF44 | Consultar extrato financeiro próprio | Aluno | Implementado (PR #79) |
| RF45 | Consultar painel gerencial | Coordenação, Secretaria | Implementado (PR #77) |

| ID | Requisito não funcional | Evidência |
| --- | --- | --- |
| RNF07 | Novas telas respeitam RBAC e retornam 403/404 conforme o padrão atual | testes de permissão em cada módulo |
| RNF08 | Listagens paginadas (20 itens) e consultas com `select_related` | views de aproveitamentos, documentos e cobranças |
| RNF09 | Constraints condicionais testadas em SQLite e PostgreSQL 16 | CI nos dois bancos |
| RNF10 | Verificação pública com limite de tentativas por IP | `documents.services.verificar_documento` |
