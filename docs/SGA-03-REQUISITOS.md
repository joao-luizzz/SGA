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

## Roadmap (não implementado)

Auto-matrícula, recuperação de senha, materiais, horário consolidado, calendário, comunicados, documentos, transferências, financeiro, aplicativo mobile, integrações e pré-requisitos não são requisitos da Fase 1.

## Referências

- [Regras de negócio](SGA-02-REGRAS-DE-NEGOCIO.md)
- [Matriz de rastreabilidade](SGA-05-RASTREABILIDADE.md)
