# SGA — Sistema de Gestão Acadêmica

## Regras de negócio

| Metadado | Valor |
| --- | --- |
| Versão | **1.0 — MVP Fase 1 concluído** |
| Data | **31 de agosto de 2026** |

As regras abaixo descrevem somente comportamentos implementados na Fase 1. Os IDs são a referência única para requisitos, casos de uso e rastreabilidade.

| ID | Regra |
| --- | --- |
| **RN01** | Cada `CustomUser` possui um único papel: `ALUNO`, `PROFESSOR`, `SECRETARIA` ou `COORDENACAO`. As telas e ações são protegidas por papel e pelo vínculo com o recurso. |
| **RN02** | Contas criadas administrativamente recebem senha inicial e `must_change_password=True`; o primeiro acesso exige sua alteração antes do painel. Conta inativa não autentica. |
| **RN03** | A Secretaria cria, edita, lista, ativa e inativa somente contas de Aluno e Professor. A edição administrativa preserva senha, papel, flag de primeira senha e estado de ativação; não pode atingir a própria conta, Secretaria ou Coordenação. |
| **RN04** | A Coordenação administra `Curso`, `Disciplina` e `Turma`. `Disciplina` pertence diretamente a um `Curso`; horários são texto validado em `Turma.horarios`. |
| **RN05** | Uma turma só recebe matrícula se estiver ativa, com professor, horários, sala e vagas máximas positivas configurados. Professor não pode ter sobreposição de horários em turmas ativas do mesmo período. |
| **RN06** | Vagas ocupadas são a contagem de matrículas `ATIVA`; a Secretaria bloqueia matrícula quando a capacidade for atingida. |
| **RN07** | Somente a Secretaria efetiva matrícula de Aluno ativo. A matrícula aceita `ATIVA`, `TRANCADA`, `CANCELADA` e `CONCLUIDA`; somente uma matrícula ativa pode ser alterada para os três últimos status. |
| **RN08** | Não se cria nova matrícula para aluno e mesma turma quando houver qualquer matrícula anterior naquela turma. Retentativa ocorre em **outra `Turma`/período**, preservando faltas e notas da tentativa anterior. |
| **RN09** | O Professor registra ou edita chamada apenas para turma ativa sob sua responsabilidade. A chamada deve informar exatamente todos os alunos com matrícula ativa naquela turma. |
| **RN10** | `Falta` representa presença/ausência de um Aluno em uma Turma e data de aula; há no máximo um registro por `Turma + Aluno + data_aula`. |
| **RN11** | Frequência é calculada pelos registros de chamada. Abaixo de 75% resulta em reprovação por falta e bloqueia o exame; sem aulas registradas, a frequência exibida é 100% e a situação de frequência é “Sem aulas registradas”. |
| **RN12** | O Professor responsável por turma ativa lança P1, P2 e Trabalho para matrículas ativas. Cada nota vale de 0 a 10 e pertence à matrícula, não à turma ou ao aluno diretamente. `MP = (P1 + P2 + Trabalho) / 3`. |
| **RN13** | Com MP completa: MP >= 6 aprova diretamente; 4 <= MP < 6, com frequência mínima, torna o aluno elegível ao exame; MP < 4 reprova por nota. |
| **RN14** | O Exame só pode ser lançado para matrícula elegível. `MF = (MP + Exame) / 2`; MF >= 6 aprova após exame e MF < 6 reprova por nota. |
| **RN15** | Criação e edição de `Nota` e `Falta` registram `AuditoriaLog` com autor, ação, valor anterior/novo e momento. O log não pode ser atualizado ou excluído. |
| **RN16** | Integridade de dados: e-mail é único; há no máximo uma matrícula ativa por Aluno+Turma; uma nota por Matrícula+tipo; e chamada única por Turma+Aluno+data. |
| **RN17** | Formulários, serviços e restrições de banco validam os dados críticos; a CI executa `check`, verificação de migrations e a suíte automatizada em SQLite e PostgreSQL 16. |

## Fora do MVP

Não há regra implementada para auto-matrícula, recuperação de senha, materiais, calendário, comunicados, documentos, transferências, financeiro, aplicativo mobile, integrações ou pré-requisitos. Esses tópicos são apenas Roadmap.

## Referências

- [Requisitos](SGA-03-REQUISITOS.md)
- [Casos de uso](SGA-06-CASOS-DE-USO.md)
- [Rastreabilidade](SGA-05-RASTREABILIDADE.md)
