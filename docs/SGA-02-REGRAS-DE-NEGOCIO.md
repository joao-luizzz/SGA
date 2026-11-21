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
| **RN05** | Uma turma só recebe matrícula se estiver ativa, com professor, horários, sala e vagas máximas positivas configurados. Professor não pode ter sobreposição de horários em turmas ativas do mesmo período. Turma com matrícula ativa não pode ser inativada; as matrículas devem ser concluídas, trancadas ou canceladas antes. |
| **RN06** | Vagas ocupadas são a contagem de matrículas `ATIVA`; a Secretaria bloqueia matrícula quando a capacidade for atingida. |
| **RN07** | Somente a Secretaria efetiva matrícula de Aluno ativo. A matrícula aceita `ATIVA`, `TRANCADA`, `CANCELADA` e `CONCLUIDA`; somente uma matrícula ativa pode ser alterada para os três últimos status. |
| **RN08** | Não se cria nova matrícula para aluno e mesma turma quando houver qualquer matrícula anterior naquela turma. Retentativa ocorre em **outra `Turma`/período**, preservando faltas e notas da tentativa anterior. |
| **RN09** | O Professor registra ou edita chamada apenas para turma ativa sob sua responsabilidade. A chamada deve informar exatamente todos os alunos com matrícula ativa naquela turma. A data da aula não pode ser futura. |
| **RN10** | `Falta` representa presença/ausência de um Aluno em uma Turma e data de aula; há no máximo um registro por `Turma + Aluno + data_aula`. |
| **RN11** | Frequência é calculada pelos registros de chamada. Abaixo de 75% resulta em reprovação por falta e bloqueia o exame; sem aulas registradas, a frequência exibida é 100% e a situação de frequência é “Sem aulas registradas”. |
| **RN12** | O Professor responsável por turma ativa lança P1, P2 e Trabalho para matrículas ativas. Cada nota vale de 0 a 10 e pertence à matrícula, não à turma ou ao aluno diretamente. `MP = (P1 + P2 + Trabalho) / 3`. |
| **RN13** | Com MP completa: MP >= 6 aprova diretamente; 4 <= MP < 6, com frequência mínima, torna o aluno elegível ao exame; MP < 4 reprova por nota. As comparações usam a média **exata**; o arredondamento para duas casas é só de exibição (ex.: MP 5,9967 aparece como 6,00, mas vai a exame). |
| **RN14** | O Exame só pode ser lançado para matrícula elegível. `MF = (MP + Exame) / 2`; MF >= 6 aprova após exame e MF < 6 reprova por nota. MF também é comparada pelo valor exato (MF 5,995 reprova). |
| **RN15** | Criação e edição de `Nota` e `Falta` registram `AuditoriaLog` com autor, ação, valor anterior/novo e momento. O log não pode ser atualizado ou excluído. |
| **RN16** | Integridade de dados: e-mail é único; há no máximo uma matrícula ativa por Aluno+Turma; uma nota por Matrícula+tipo; e chamada única por Turma+Aluno+data. |
| **RN17** | Formulários, serviços e restrições de banco validam os dados críticos; a CI executa `check`, verificação de migrations e a suíte automatizada em SQLite e PostgreSQL 16. |

## Limites do contrato da Fase 1

As regras acima descrevem somente o contrato da Fase 1. Os módulos posteriores não alteram retroativamente estas regras. As regras da Fase 3 (RN18–RN27) estão na seção abaixo; o estado de cada fase está no Documento Consolidado.

## Referências

- [Requisitos](SGA-03-REQUISITOS.md)
- [Casos de uso](SGA-06-CASOS-DE-USO.md)
- [Rastreabilidade](SGA-05-RASTREABILIDADE.md)


## Estado atual — 20/11/2026

| Fase | Estado | Entregas |
| --- | --- | --- |
| Fase 1/MVP | Concluída | Núcleo acadêmico descrito neste documento. |
| Fase 2 | Concluída | Materiais e comunicados (PR #66), calendário/grade/conflitos (PR #67), relatórios (PR #68, #70), transferências (PR #69, #70), recuperação de senha e notificações (PR #73, ajustes na #75). |
| Fase 3 | Implementada | Pré-requisitos e aproveitamento (PR #76), painel gerencial (PR #77), documentos oficiais (PR #78) e financeiro básico (PR #79), conforme a [especificação da Fase 3](SGA-12-ESPECIFICACAO-FASE-3.md). |
| Estudos | Somente estudo | API pública e integrações ([SGA-13](SGA-13-ESTUDO-API-INTEGRACOES.md)): recomendação de não expor API nesta evolução. App mobile e IA ([SGA-14](SGA-14-ESTUDO-MOBILE-IA.md)): recomendação de não implementar nesta evolução. |
| Fechamento | Em andamento | Documentação final (PR #80), validação com instalação limpa (PR #81) e lacunas da auditoria das issues: comunicados no painel, filtro por turma na grade, testes de vínculo curricular e `CONTRIBUTING.md` (PR #82); correções da conferência visual em desktop e celular (PR #84). Pré-release `v3.0.0-rc1`. Pendentes: ensaio da apresentação (#53), merge em `main` e `v3.0.0`. |

“Fora do MVP” nos trechos da Fase 1 significa fora do escopo **original**, não ausente do código atual. As seções de estado de 08/10/2026 foram substituídas por esta; o histórico permanece no Git.

## Regras da Fase 3

Detalhamento, decisões D1–D5 e evidências em [SGA-12](SGA-12-ESPECIFICACAO-FASE-3.md).

| ID | Regra |
| --- | --- |
| **RN18** | Uma `Disciplina` pode exigir outras disciplinas ativas **do mesmo curso** como pré-requisito. Autorreferência e ciclos (diretos ou indiretos) são recusados. Somente a Coordenação mantém pré-requisitos. |
| **RN19** | A matrícula exige, para cada pré-requisito, uma matrícula anterior não cancelada com resultado `Aprovado Direto` ou `Aprovado após Exame`, ou um aproveitamento `DEFERIDO`. Em andamento, reprovação por nota e por falta não cumprem o pré-requisito. Pré-requisitos de disciplinas inativas não são exigidos. |
| **RN20** | Aproveitamento é registrado pela Secretaria e analisado pela Coordenação com justificativa obrigatória. O deferimento exige carga horária de origem ≥ 75% da disciplina (D1). Há no máximo um aproveitamento pendente ou deferido por Aluno + Disciplina. |
| **RN21** | Declaração de matrícula e histórico escolar são registrados em `DocumentoEmitido` com código de verificação único; o conteúdo é congelado na emissão e o registro é imutável. |
| **RN22** | O Aluno emite somente os próprios documentos; a Secretaria emite para qualquer aluno. O histórico lista apenas resultados finais e aproveitamentos deferidos; a declaração exige matrícula ativa. |
| **RN23** | A verificação pública recebe só o código e exibe tipo, data e nome mascarado, sem notas ou e-mail, com limite de tentativas por IP e mensagem neutra para código inválido. |
| **RN24** | A Secretaria lança cobranças por aluno e competência (`AAAA-MM`) com valor positivo e vencimento; não há duplicidade não cancelada por Aluno + competência + descrição. Baixa e cancelamento só a partir de `ABERTA`; cancelamento exige justificativa; atraso é derivado. |
| **RN25** | O Aluno consulta só as próprias cobranças. A situação financeira não bloqueia matrícula, notas, frequência nem documentos (D2). Não há meio de pagamento, juros ou multa. |
| **RN26** | O painel gerencial é somente leitura, para Coordenação e Secretaria (D3), com indicadores agregados por curso e período, sem nomes de alunos, reutilizando o selector dos Relatórios Acadêmicos. |
| **RN27** | Criação e mudanças de estado de `PreRequisito`, `Aproveitamento`, `DocumentoEmitido` e `Cobranca` registram `AuditoriaLog`, estendendo RN15. |
