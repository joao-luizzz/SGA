# SGA — Preparação técnica da Fase 2

| Metadado | Valor |
| --- | --- |
| Issues | `#32`, `#38`, `#39`, `#40` e `#54` |
| Base revisada | `origin/develop` em `d4678e9` |
| Data do levantamento | 10 de setembro de 2026 |
| Estado | Proposta técnica; nenhuma funcionalidade da Fase 2 implementada |

Este documento registra a validação da base, o mapa da arquitetura atual, a proposta de extensão e a revisão do backlog. Ele não altera o contrato da Fase 1: as oito entidades e as regras descritas em [SGA-04](SGA-04-MODELAGEM-DADOS.md) continuam sendo a fonte da verdade do que está implementado.

## Validação da base

A revisão foi feita em worktree isolado, porque o checkout local de `develop` continha alterações não relacionadas. A referência remota foi atualizada e a branch de trabalho nasceu do commit `d4678e9`, que inclui o fechamento do MVP e as PRs `#28` a `#31`.

| Verificação | Resultado |
| --- | --- |
| `USE_SQLITE=True ... manage.py check` | Sem issues (`0 silenced`) |
| `USE_SQLITE=True ... manage.py makemigrations --check --dry-run` | `No changes detected` |
| `USE_SQLITE=True ... pytest` | **196 passed**, 6 avisos de depreciação, em 261,26 s |
| CI de `develop` | Execução `33449508563`, commit `d4678e9`, concluída com sucesso nos jobs SQLite e PostgreSQL |

Os avisos locais vêm do Django 5.1.15 executado em Python 3.14.6 e referem-se a `asyncio.iscoroutinefunction`, previsto para remoção no Python 3.16. Não houve falha funcional. O Docker Compose local não tinha serviços em execução; a cobertura PostgreSQL desta base foi confirmada pelo job de CI.

## Mapa da arquitetura atual

### Aplicações, dados e camadas

| App | Entidades | Serviços e selectors | Views, forms e URLs |
| --- | --- | --- | --- |
| `accounts` | `CustomUser`, `AuditoriaLog` | autenticação/senha, criação administrativa, ativação e auditoria; busca por e-mail, painel por papel e usuários gerenciáveis | login, logout POST, troca de senha, quatro dashboards e gestão de Aluno/Professor |
| `academics` | `Curso`, `Disciplina`, `Turma` | não possui `services.py` nem `selectors.py`; validações atuais de horário e conflito ficam no model/form | CRUD da Coordenação para curso, disciplina e turma |
| `enrollment` | `Matricula` | matrícula/status com transações e locks; consultas de matrícula e vagas | consulta do Aluno e gestão administrativa da Secretaria |
| `attendance` | `Falta` | chamada atômica e auditada; consultas e cálculo de frequência | chamada/frequência do Professor e boletim próprio do Aluno |
| `assessments` | `Nota` | lançamento atômico e auditado; MP, MF, situação, elegibilidade e boletim | notas da turma para Professor e boletim próprio do Aluno |

O banco atual possui oito migrations versionadas: duas em `accounts`, duas em `academics`, duas em `enrollment`, uma em `attendance` e uma em `assessments`. `Nota` pertence à tentativa (`Matricula`); `Falta` usa Aluno + Turma + data. Média, situação, frequência e vagas são calculadas, não persistidas.

### Interface, middleware e segurança

- `base.html` compõe `includes/navbar.html`, `includes/sidebar.html` e mensagens; os novos atalhos devem estender esses componentes Bootstrap, sem criar outro layout.
- A navegação lateral já é segmentada pelos quatro papéis. A navbar contém o ponto natural para um contador de notificações.
- O middleware próprio `MandatoryPasswordChangeMiddleware` bloqueia a navegação até a troca da senha inicial, excetuando troca, logout, estáticos e admin.
- A autenticação usa sessão Django e `CustomUser.email`; logout e demais mudanças de estado relevantes usam POST com CSRF.
- O redirecionamento `next` do login usa `url_has_allowed_host_and_scheme`, evitando open redirect.
- `role_required`/`RoleRequiredMixin` protegem por papel; services e selectors reforçam vínculo de turma, matrícula e destinatário. Novos módulos devem manter as duas camadas de proteção.
- Há templates próprios para 403 e 404. A suíte cobre models, forms, services, selectors, views, RBAC, navegação e fluxo integrado do MVP.

### Pontos de extensão

| Capacidade | Encaixe proposto | Dependências atuais |
| --- | --- | --- |
| Materiais | novo app `materials`, com service de publicação e selectors por turma/matrícula | `Turma`, `Matricula`, Professor responsável e armazenamento de mídia |
| Comunicados | novo app `communications`, com segmentação resolvida em selectors | `CustomUser`; `Curso`/`Turma` conforme decisão de público |
| Calendário e grade | novo app `scheduling` ou extensão coesa de `academics`; migrar horários textuais somente com plano de dados | `Turma.horarios`, período, Professor, Disciplina e matrículas |
| Notificações | novo app `notifications`, service único de criação e contador via context processor | `CustomUser`; eventos já estáveis de comunicado, nota e frequência |
| Recuperação de senha | extensão de `accounts` com views/forms/tokens nativos do Django | `CustomUser`, backend de e-mail e configuração de timeout |
| Transferências | novo app `transfers`, sem alterar/apagar `Matricula`, `Nota` ou `Falta` | Aluno (`CustomUser`) e definição pendente do vínculo acadêmico com Curso |
| Relatórios | selectors de leitura no domínio proprietário e camada de apresentação própria | models existentes e, depois, módulos já integrados; não exige entidade |

## Modelagem proposta para a Fase 2

As entidades abaixo são propostas para orientar as issues dos responsáveis. Nenhuma deve ser criada nesta etapa.

### Materiais acadêmicos

`MaterialAcademico`: `turma` (FK obrigatória), `autor` (FK obrigatória para `CustomUser`), `titulo`, `descricao`, `arquivo` opcional, `link` opcional, `publicado_em` e `atualizado_em`.

- Exigir exatamente um entre arquivo e link; título não vazio; arquivo de até 20 MB e tipos permitidos validados em form/service, sem confiar apenas na extensão enviada.
- Não duplicar `disciplina` ou `professor`: a turma identifica a disciplina e o service valida que o autor é o Professor atualmente responsável.
- Aluno acessa somente material de turma em que possui matrícula autorizada; Professor só gerencia material das próprias turmas. Remoção deve preservar a consistência entre registro e arquivo físico.

### Comunicados

`Comunicado`: `autor`, `titulo`, `conteudo`, `escopo`, `papel_destino` opcional, `curso` opcional, `turma` opcional, `publicar_em`, `expirar_em` opcional, `ativo` e `criado_em`.

- `escopo` deve escolher uma segmentação (`GERAL`, `PAPEL`, `CURSO` ou `TURMA`) e constraints devem exigir somente o campo-alvo correspondente.
- A visibilidade deve ser resolvida em selector, combinando papel e vínculo acadêmico, nunca apenas ocultando elementos no template.
- O ator publicador permanece pendente de decisão: a documentação anterior reserva a ação à Coordenação, enquanto a issue `#34` inclui Secretaria e a `#56` ainda pede que isso seja definido.
- Segmentação por Curso depende de existir uma relação confiável entre Aluno e Curso, ausente no modelo atual.

### Calendário e grade

`HorarioTurma`: `turma`, `dia_semana`, `hora_inicio` e `hora_fim`; unicidade por turma + dia + início + fim. Regras em service devem rejeitar início maior ou igual ao fim e sobreposição de Professor, Turma e sala no mesmo período.

`EventoCalendario`: `titulo`, `descricao`, `tipo`, `inicio`, `fim`, `escopo`, alvos opcionais (`papel`, `curso`, `turma`), `autor`, `ativo` e timestamps.

- A migração de `Turma.horarios` textual precisa analisar os registros existentes, converter todos de forma reversível e só remover o campo antigo em etapa posterior. Manter simultaneamente duas fontes editáveis geraria divergência.
- Eventos de dia inteiro e com horário devem ter representação explícita; `fim` não pode anteceder `inicio`.
- Janela de auto-matrícula não deve ser acoplada agora: autoatendimento permanece fora das entregas atuais.

### Notificações internas

`Notificacao`: `destinatario` (FK obrigatória), `titulo`, `descricao`, `tipo`, `url_interna` opcional, `criada_em` e `lida_em` opcional. O estado não lida é derivado de `lida_em IS NULL`; ordenação padrão por `-criada_em, -id` e índice em destinatário + leitura + criação.

- Toda criação passa por uma API de service; integrações não devem instanciar o model diretamente.
- Listagem, contador, leitura individual e leitura em lote sempre filtram primeiro pelo usuário autenticado. Marcar como lida é POST e idempotente.
- `url_interna`, se usada, deve ser gerada por nomes de URL conhecidos ou validada como caminho local. Evitar relação genérica nesta primeira versão reduz acoplamento com módulos instáveis.
- Eventos iniciais seguros: nota e chamada já existem. Comunicado só entra após o módulo da Semana 2 estabilizar.

### Recuperação de senha

Não criar `TokenRecuperacaoSenha`. Usar `PasswordResetView`, `PasswordResetConfirmView`, `PasswordResetTokenGenerator` e formulários do Django, cujo token assinado é invalidado pela alteração da senha e pelo timeout.

- Configurar `PASSWORD_RESET_TIMEOUT`, assunto/remetente e backend por ambiente; desenvolvimento e testes usam backends do Django, sem provedor externo.
- A resposta à solicitação é sempre neutra. Templates de e-mail não expõem dados além do necessário e os redirecionamentos permanecem locais.
- Cobrir token válido, inválido, expirado e reutilizado, validadores de senha e usuários autenticados/não autenticados.

### Transferências e relatórios

`SolicitacaoTransferencia`: `aluno`, `tipo` (`ENTRADA`/`SAIDA`), instituições e cursos de origem/destino conforme o tipo, `status` (`PENDENTE`/`APROVADA`/`RECUSADA`), `solicitada_em`, `analisada_em`, `analisada_por` e `justificativa`.

- Constraints condicionais exigem os dados do tipo escolhido; somente uma solicitação pendente equivalente por aluno; análise é transacional e não apaga histórico acadêmico.
- A issue precisa decidir se é simples registro administrativo ou solicitação sujeita a aprovação, pois as duas descrições divergem.
- Relatórios não precisam de model. Devem partir de selectors com `select_related`/`prefetch_related`, filtros explícitos, RBAC no backend e valores calculados pelas regras existentes, evitando reimplementar médias e frequência.

## Riscos de migração e integridade

1. Aluno é apenas um papel de `CustomUser` e não possui vínculo com `Curso`; públicos por curso, transferências e relatórios por curso não podem presumir esse dado.
2. `Turma.horarios` é texto validado. A normalização para `HorarioTurma` exige migração de dados e estratégia de compatibilidade/reversão.
3. `Curso → Disciplina → Turma` usa exclusões em cascata. Novas FKs históricas precisam definir se acompanham esse comportamento ou usam `PROTECT`; inativação deve continuar preferida à exclusão.
4. Arquivos introduzem configuração de `MEDIA_ROOT`, limpeza, limite, inspeção de conteúdo e risco de referências órfãs; não devem entrar junto de uma migração puramente estrutural sem testes.
5. Constraints condicionais precisam ser testadas em SQLite e PostgreSQL. Locks e consultas críticas devem preservar a compatibilidade entre ambos.
6. Notificações não devem ser produzidas antes do commit da transação acadêmica (`transaction.on_commit` quando necessário), para evitar avisos de operações revertidas.

## Revisão do backlog `#33` a `#37`

| Bloco | Coerência e dependências | Ajustes necessários antes da execução |
| --- | --- | --- |
| `#33`, `#44–#46`, `#57–#58` — Alexandre | Depende de `#32` e do catálogo/turmas; está no domínio acadêmico. | O título promete calendário, mas as sub-issues cobrem apenas grade. Criar aceite para eventos/calendário. Incluir conflito de sala, citado na principal e ausente nos testes filhos. Definir migração de `Turma.horarios`. |
| `#34`, `#41–#43`, `#55–#56` — Vitor | Depende de `#32` e de turmas/matrículas; responsáveis coerentes. | Resolver quem publica comunicado; alinhar públicos geral/perfil/curso/turma; remover redundância de disciplina/professor no material ou justificar; explicitar segurança e ciclo de vida de upload. |
| `#35`, `#47–#48`, `#59–#60` — João | Depende de `#32`, autenticação e, para comunicado, Semana 2. Nota/frequência já são eventos estáveis. | A `#60` mistura testes de token de senha com leitura de notificações; mover esses critérios para `#59` ou separar testes por módulo. Definir timeout e eventos iniciais. |
| `#36`, `#49–#51`, `#61–#62` — Andrey/Max | Depende de matrícula, avaliações e frequência; divisão geral está correta. | Resolver registro simples versus solicitação/aprovação; definir vínculo Aluno–Curso; transformar “N+1 evidente”, filtros, impressão e CSV em critérios mensuráveis. |
| `#37`, `#52–#53`, `#63` — equipe | Deve iniciar somente após Semanas 1–5. As responsabilidades de João são documentação, segurança compartilhada e estudos. | `#52` chama a Semana 6 de integração da Fase 3, embora primeiro deva consolidar a Fase 2. Faltam sub-issues explícitas para estudo de API e documentação técnica de João; `#53` concentra documentação na Semana 8, divergindo da Semana 6 da principal. |

### Ordem recomendada de integração

1. Aprovar este desenho e corrigir os critérios/dependências do backlog.
2. Semana 2: materiais e comunicados, com decisões de público e upload fechadas.
3. Semana 3: normalização da grade e calendário, em migração isolada.
4. Semana 4: recuperação de senha separada de notificações; integrar somente eventos já estáveis.
5. Semana 5: transferências e relatórios após decidir vínculo acadêmico do Aluno.
6. Semanas 6–8: integrar, auditar, documentar e estudar evoluções; não implementar API pública automaticamente.

## Decisões e pendências para aprovação da equipe

- Manter os documentos da Fase 1 descrevendo apenas o implementado; usar este arquivo como proposta da Fase 2 até cada módulo entrar em `develop`.
- Reutilizar tokens nativos do Django e não persistir token próprio de recuperação.
- Derivar estado de leitura de `lida_em` e centralizar criação de notificações em service.
- Normalizar horários somente mediante migração de dados separada e reversível.
- Decidir antes da implementação: vínculo Aluno–Curso, autores/públicos de comunicados, fluxo de transferência e escopo real do calendário.
- Nenhuma issue autoriza React, SPA, API REST/JWT ou provedor externo de e-mail.
