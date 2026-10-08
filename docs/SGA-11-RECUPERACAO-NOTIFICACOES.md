# SGA — Recuperação de senha e notificações (Semana 4)

## Estado e rastreabilidade

Entrega implementada na branch `feat/35-recuperacao-senha-notificacoes`, baseada em
`08d440795a643a8ed541f9044e79ef273084eb98`. Aguarda revisão de João Luiz e integração;
não declara merge, fechamento de issues ou CI remoto desta branch.

| Issue | Entrega nesta implementação | Evidência |
| --- | --- | --- |
| #35 | Concluída no código; revisão pendente | Fluxos abaixo e testes HTTP/integrados |
| #47 | Solicitação de recuperação concluída | `accounts.forms.RecoveryForm`, `accounts.services.solicitar_recuperacao` |
| #59 | Redefinição/token concluídos | `accounts.services.redefinir_senha`, `accounts.recovery.RecoveryConfirmView` |
| #48 | Central pessoal concluída | App `notifications`, navbar e templates |
| #60 | Leitura/testes de notificações concluídos | Services, selectors e `tests/test_notifications/` |

Testes de tokens pertencem a #47/#59; #60 permanece dedicada a notificações.

**Registro histórico da revisão após PR #70:** a Semana 4 ainda não estava
implementada. A preparação em SGA-08 e as evidências da Semana 5 são registros
anteriores e não são reescritos como se esta implementação já existisse.

## Recuperação segura

- Login oferece **Esqueci minha senha** (`accounts:password_reset`).
- E-mails válidos existentes, inexistentes, inativos ou com senha inutilizável
  recebem o mesmo redirecionamento/mensagem pública. Apenas contas ativas com
  senha utilizável recebem mensagem. A resposta não confirma entrega de e-mail.
- Usa `default_token_generator`, instância nativa de `PasswordResetTokenGenerator`;
  não cria tabela de tokens nem criptografia própria.
- `PASSWORD_RESET_TIMEOUT` configura a validade em segundos (padrão: 3600).
  O token é vinculado ao usuário e ao estado da senha; a mudança invalida seu reuso.
- O fluxo nativo troca o token da URL por um marcador de sessão (`set-password`).
  A confirmação reconsulta o usuário com `select_for_update()` e revalida o token
  dentro da transação. Dois POSTs concorrentes no PostgreSQL não podem efetivá-lo
  duas vezes. SQLite suporta o fluxo, mas não fornece esse bloqueio por linha.
- Mantém os validadores existentes do Django, grava somente hash e limpa
  `must_change_password` após sucesso. Não faz login automático; sessões antigas
  ficam inválidas pela alteração do hash de autenticação.
- Auditoria registra somente “Senha redefinida por recuperação.”, usuário e ação;
  nunca senha, hash ou token. Logs Django de requisição/servidor ocultam o link;
  falhas de e-mail têm mensagem genérica sem exceção/conteúdo. Formulários usam CSRF;
  páginas de confirmação não usam cache e enviam `Referrer-Policy: no-referrer`.

### Configuração de e-mail por ambiente

As variáveis estão em `.env.example` e são lidas em `config.settings.local`.

| Variável | Finalidade / padrão |
| --- | --- |
| `EMAIL_BACKEND` | `django.core.mail.backends.locmem.EmailBackend` por padrão |
| `EMAIL_HOST`, `EMAIL_PORT` | SMTP; localhost / 587 |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Credenciais externas, vazias no exemplo |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | TLS True / SSL False; escolher conforme servidor |
| `EMAIL_TIMEOUT` | Timeout SMTP de 10 segundos |
| `DEFAULT_FROM_EMAIL` | Remetente institucional configurável |
| `PASSWORD_RESET_DOMAIN` | Origem confiável; localhost:8000 em desenvolvimento |
| `PASSWORD_RESET_USE_HTTPS` | False local; configurar True com HTTPS |
| `PASSWORD_RESET_TIMEOUT` | Expiração do token: 3600 segundos |
| `PASSWORD_RESET_EMAIL_COOLDOWN`, `PASSWORD_RESET_IP_COOLDOWN` | 60 / 10 segundos |

Para envio real, selecionar `django.core.mail.backends.smtp.EmailBackend` e
configurar domínio, HTTPS, remetente e credenciais no ambiente. O padrão em memória
é intencional: não envia e-mails reais nem imprime links. Console e arquivo são
bloqueados para recuperação. Testes inspecionam `django.core.mail.outbox`.
O domínio não é derivado do cabeçalho Host recebido. Os cooldowns usam chaves HMAC
no cache, sem e-mail/IP em claro; com cache local, sua abrangência é por processo.
O envio SMTP é síncrono; equivalência testada é de status, redirecionamento e conteúdo,
não uma garantia de tempo de resposta idêntico. Logs de proxy/infraestrutura externos
à aplicação também devem evitar URLs de recuperação e corpos de formulários.

## Notificações pessoais

`Notificacao` possui destinatário, título, mensagem, categoria (`COMUNICADO`, `NOTA`
ou `FREQUENCIA`), criação, `lida_em` opcional e referência opcional ao comunicado.
Unicidade Comunicado+destinatário evita duplicação; índice apoia consulta por
usuário/leitura/criação. Migration: `notifications/0001_initial.py`.

- Central `notifications:central`: 20 itens por página, mais recentes primeiro.
- Detalhe é somente leitura via GET; botão **Marcar como lida** usa POST + CSRF.
- **Marcar todas como lidas** também usa POST + CSRF, somente nas notificações
  visíveis do próprio usuário. Marcação repetida preserva o primeiro horário.
- Navbar mostra contador de não lidas. Toda consulta, detalhe e atualização da
  central pessoal usa o destinatário autenticado; outro ID retorna 404.
- Aluno, Professor, Secretaria, Coordenação e superusuário usam a mesma regra
  pessoal. Não há consulta por usuário arbitrário nem bypass de superusuário.

### Integrações e transações

- `publicar_comunicado` e alterações efetivas de `atualizar_comunicado` notificam
  os destinatários ativos permitidos pelo selector existente do mural. A central
  reaplica essa visibilidade: inativação, expiração ou mudança de escopo/vínculo
  ocultam as notificações que deixaram de ser permitidas, inclusive no contador.
- Comunicados agendados não notificam antes da publicação. Na próxima visita
  autenticada, um service sincroniza os comunicados vigentes ainda sem notificação
  para aquele usuário. Isso inclui comunicados vigentes anteriores à implantação.
  Não há worker, entrega em horário exato nem envio externo de notificações.
- `_salvar_nota` notifica o aluno somente quando cria ou altera de fato uma nota.
- `registrar_chamada` notifica o aluno somente para registros criados/alterados;
  repetir o mesmo lançamento não gera novo aviso.
- Evento, auditoria e notificação são persistidos na mesma transação de banco;
  qualquer rollback desfaz todos. Não há efeito externo que exija `on_commit`.
- Permissões, cálculos, elegibilidade ao exame e regras acadêmicas anteriores são
  mantidos. Links levam ao comunicado ou ao boletim existente do usuário.

## Verificação e demonstração

`tests/test_accounts/test_recovery.py` cobre o fluxo HTTP completo, respostas
neutras, contas inelegíveis, senha válida/inválida, CSRF, token expirado/manipulado,
vínculo a outro usuário, reuso entre sessões, concorrência PostgreSQL, auditoria,
falha de entrega e proteção de logs. `tests/test_notifications/` cobre os quatro
papéis/superusuário, isolamento, acesso por ID, leitura individual/todas, paginação,
contador, CSRF, visibilidade e os três eventos por services e HTTP, com rollback e
operações sem alteração efetiva.

Para demonstrar, seguir o roteiro em [SGA-07](SGA-07-ROTEIRO-DEMO-E-ENTREGA.md).
A caixa em memória serve à validação automatizada; uma demonstração com recebimento
real exige SMTP configurado. CI existente mantém SQLite com cobertura mínima 85%
e PostgreSQL 16 sem cobertura; não houve redução do threshold.

## Evidências da validação desta entrega — 08/10/2026

| Execução | Resultado |
| --- | --- |
| Docker, Python 3.12.14, suíte completa SQLite com cobertura | 424 aprovados, 3 skips; cobertura 89.67% |
| Ambiente virtual Python 3.14, suíte completa PostgreSQL 16 via Docker | 427 aprovados, nenhum skip |
| Docker/Python 3.12, testes novos no PostgreSQL 16 | 45 aprovados, incluindo concorrência de token |
| Testes novos SQLite, ambiente virtual | 44 aprovados, 1 skip exclusivo de PostgreSQL |
| `manage.py check` e `makemigrations --check --dry-run` | Aprovados em SQLite e PostgreSQL |
| Aplicação real das migrations em bancos descartáveis | Aprovada em SQLite e PostgreSQL |
| `git diff --check` e links locais/fences Markdown | Aprovados |

Os três skips SQLite são os dois testes concorrentes anteriores de transferências
mais o teste concorrente de recuperação. Todos foram exercitados no PostgreSQL.
O threshold permanece 85%. A execução Docker final ocorreu com o código congelado;
uma rodada anterior foi reiniciada após o ajuste final de logs. Os números são
registro desta validação, não promessa de contagem/cobertura permanente.
Há um aviso de depreciação do Django sobre o esquema padrão de URL no Django 6.0;
esta entrega mantém o comportamento existente no Django 5.1.

O workflow CI continua inalterado. **CI remoto desta branch ainda não executado ou
verificado**, pois não houve push/PR nesta tarefa. Envio SMTP real e revisão visual
manual também ficam para o ambiente de revisão; os fluxos HTTP, incluindo CSRF,
foram testados automaticamente. Não houve fechamento de issues ou merge na develop.
