# SGA — Estudo técnico: API pública e integrações

| Metadado | Valor |
| --- | --- |
| Versão | **0.1 — estudo para decisão da equipe** |
| Data | **29 de outubro de 2026** |
| Issue | #37 — Semana 8: estudo técnico de API pública e integrações (João Luiz) |
| Natureza | **Estudo.** Nada aqui autoriza implementação (#5, #37, SGA-08). |

## Pergunta

O SGA deve expor uma API pública ou integrar-se a sistemas externos nesta
evolução? Se sim, de que forma, respeitando a stack obrigatória (AGENTS.md:
sem Django REST Framework e sem JWT sem aprovação explícita)?

## Situação atual

| Aspecto | Estado na `develop` |
| --- | --- |
| Interface | Django Templates + Bootstrap 5 + HTMX, autenticação por sessão |
| Endpoints não HTML | Somente `academics:relatorios_csv` (CSV para Coordenação) |
| Dependências | Django 5.1, psycopg, python-dotenv |
| E-mail | Backend configurável por ambiente; SMTP real somente por configuração (PR #73) |
| Consumidores externos conhecidos | **Nenhum** |

Não há hoje cliente que precise de uma API: não existe app mobile, portal
terceiro nem sistema institucional integrando com o SGA.

## Opções avaliadas

| Opção | Descrição | Prós | Contras | Esforço |
| --- | --- | --- | --- | --- |
| **A. Não expor API** | Manter o monólito com HTML, CSV e impressão | Zero superfície nova; coerente com a stack | Integrações exigem exportação manual | Nenhum |
| **B. Endpoints JSON somente leitura com sessão** | Views Django com `JsonResponse`, mesmos decorators de papel e selectors | Sem dependências; reaproveita RBAC e selectors | Só serve para o próprio domínio (mesma sessão); não atende terceiros | Baixo |
| **C. API para terceiros com token próprio** | Endpoints JSON autenticados por token de serviço (`Authorization: Bearer`), hash do token no banco, escopos por recurso | Atende integrações reais | Exige gestão de chaves, rate limit, versionamento, CORS, documentação e testes de segurança; risco LGPD | Alto |
| **D. Django REST Framework (+ JWT)** | API completa com serializers, paginação e OpenAPI | Padrão de mercado, ecossistema | **Vetado pela stack sem aprovação**; duplica regras já em selectors | Alto |

## Integrações avaliadas

| Integração | Valor | Viabilidade com a stack atual | Recomendação |
| --- | --- | --- | --- |
| **SMTP institucional** | Entrega real da recuperação de senha | Já suportado por variáveis de ambiente (PR #73) | Configurar na implantação; não exige código |
| **Exportação iCalendar (`.ics`)** do calendário/grade | Aluno e Professor importam aulas no Google/Outlook | Texto gerado em view, sem dependência; link autenticado por sessão | **Candidata para depois da Fase 3**, baixo risco |
| **Exportações CSV adicionais** (matrículas, cobranças) | Entrega dados à secretaria/financeiro externo | Padrão já existe em `relatorios_csv_view` | Expandir sob demanda, mesmo padrão e RBAC |
| **Verificação pública de documento** | Terceiros validam declarações/históricos | Página HTML pública prevista em SGA-12 (RN23) | Resolver como página, não como API |
| **SSO/LDAP institucional** | Login único | Exige backend de autenticação e provedor real | Fora do escopo; sem provedor definido |
| **Gateway de pagamento / boleto** | Pagamento online | Exige contrato, webhooks e segredos | Fora do escopo; RN25 exclui meios de pagamento |
| **Webhooks de saída** | Avisar sistemas externos de eventos | Exige fila/worker inexistente | Fora do escopo |

## Riscos de uma API pública

- **Dados pessoais (LGPD):** notas, frequência, e-mail e dados financeiros de
  alunos. Toda resposta precisaria do mesmo isolamento por usuário já testado
  nas telas (IDOR é o principal risco).
- **Duplicação de regras:** a API não pode recalcular resultados; deveria
  reutilizar `calcular_resultado_academico` e os selectors existentes.
- **Superfície de autenticação nova:** token de serviço exige emissão,
  revogação, expiração, armazenamento em hash e limitação de tentativas.
- **CSRF/CORS:** endpoints com sessão herdam CSRF; endpoints com token exigem
  política de CORS explícita e nunca devem aceitar cookies de sessão.
- **Manutenção:** contrato versionado (`/api/v1/`) e testes de contrato
  aumentam o custo de cada mudança de modelo.

## Recomendação

1. **Adotar a opção A nesta evolução.** Não há consumidor externo que justifique
   o custo e o risco; o prazo de 08/11 deve ir para os módulos da Fase 3.
2. Atender integrações por **exportação** (CSV, `.ics`, páginas de impressão e
   verificação pública), todas dentro da stack atual e do RBAC existente.
3. Se surgir um consumidor real (ex.: app mobile — estudo da equipe), partir da
   **opção B** para leitura própria e só evoluir para **C** ou **D** mediante:
   - consumidor e casos de uso definidos;
   - aprovação explícita para DRF/JWT, se escolhidos;
   - modelo de ameaças e testes de isolamento antes do primeiro endpoint.

## Esboço caso a opção B/C seja aprovada no futuro

Mantido como referência, **não para implementar agora**.

| Recurso | Método | Papel | Fonte |
| --- | --- | --- | --- |
| `/api/v1/me/boletim/` | GET | Aluno | `assessments.selectors.get_boletim_do_aluno` |
| `/api/v1/me/frequencia/` | GET | Aluno | `attendance.selectors.get_boletim_frequencia_do_aluno` |
| `/api/v1/me/notificacoes/` | GET | Todos | `notifications.selectors.listar_notificacoes` (PR #73) |
| `/api/v1/me/calendario.ics` | GET | Aluno, Professor | calendário/grade |

Regras: somente leitura, sempre recursos do próprio usuário (`/me/`), paginação
de 20 itens, respostas de erro sem detalhes internos, mesmos testes 403/404.

## Decisão solicitada

| ID | Pergunta | Proposta |
| --- | --- | --- |
| D6 | Expor API pública nesta evolução? | Não (opção A) |
| D7 | Exportação `.ics` entra no backlog pós-Fase 3? | Sim, baixa prioridade |

## Referências

- [Especificação da Fase 3](SGA-12-ESPECIFICACAO-FASE-3.md)
- [Preparação da Fase 2](SGA-08-PREPARACAO-FASE-2.md)
- [Relatórios e integração](SGA-10-RELATORIOS-INTEGRACAO.md)
