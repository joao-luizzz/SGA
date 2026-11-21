# SGA — Estudo técnico: aplicativo mobile e IA

| Metadado | Valor |
| --- | --- |
| Versão | **1.0 — estudo para decisão da equipe** |
| Data | **20 de novembro de 2026** |
| Issue | #37 — Semana 8: estudo técnico de app mobile e IA |
| Natureza | **Estudo.** Nada aqui autoriza implementação (#5, #37). |

## Pergunta

Vale construir um aplicativo mobile ou recursos de IA para o SGA nesta evolução? Se não, o que seria necessário para fazê-lo depois sem retrabalho?

## Aplicativo mobile

### Situação atual

A interface usa Django Templates + Bootstrap 5, que já é responsiva: as telas são utilizáveis no navegador do celular, com sidebar recolhível, tabelas com rolagem horizontal e formulários em coluna única. Não há API para um cliente nativo ([SGA-13](SGA-13-ESTUDO-API-INTEGRACOES.md) recomendou não expor API nesta evolução).

### Opções avaliadas

| Opção | Descrição | Prós | Contras | Esforço |
| --- | --- | --- | --- | --- |
| **A. Web responsiva** (atual) | Usar o SGA pelo navegador do celular | Zero código novo; RBAC e regras já testados | Sem notificação push nem uso offline | Nenhum |
| **B. PWA** | Manifesto + service worker sobre as páginas atuais; ícone na tela inicial | Pouco código, sem loja de apps, mesma stack | Push exige serviço adicional; offline limitado a páginas estáticas | Baixo |
| **C. App nativo/híbrido** (Flutter, React Native) | Cliente separado consumindo API | Experiência nativa, push, offline | Exige API autenticada (opção C/D da SGA-13), nova stack fora do AGENTS.md, duas bases de código, publicação em lojas | Alto |

### Recomendação

1. **Manter a opção A nesta entrega.** Os papéis mais móveis (Aluno consultando notas, frequência, notificações, documentos e extrato) já são atendidos pelo navegador.
2. Se houver demanda real de uso no celular, começar pela **opção B (PWA)**, que não muda a arquitetura.
3. A **opção C** só faz sentido depois de uma API aprovada (SGA-13) e com público e casos de uso definidos.

## Inteligência artificial

### Casos de uso possíveis

| Caso | Valor | Dados envolvidos | Risco |
| --- | --- | --- | --- |
| Alerta precoce de risco acadêmico (previsão) | Médio | notas, frequência, histórico | Viés e falso positivo afetando alunos; exige base histórica que o SGA ainda não tem |
| Assistente para dúvidas de regras (FAQ) | Baixo/médio | documentação pública do SGA | Respostas erradas sobre regras acadêmicas; envio de texto a provedor externo |
| Resumo de comunicados | Baixo | comunicados | Baixo, mas o volume atual não justifica |
| Análise de ementas para aproveitamento | Médio | ementas externas | Decisão acadêmica continua humana (RN20); exige ementas digitalizadas, inexistentes hoje |

### Situação atual

O SGA já tem uma **sinalização de risco determinística** (`identificar_risco_academico`): regras explícitas sobre frequência e médias, explicáveis e auditáveis, exibidas nos relatórios e no painel gerencial. Ela atende ao principal caso de uso sem modelo estatístico.

### Riscos

- **Dados pessoais (LGPD):** notas, frequência e dados financeiros são dados de alunos; enviá-los a um provedor externo de IA exige base legal, contrato e minimização.
- **Decisões acadêmicas:** aprovação, reprovação e deferimento são regras normativas (RN11–RN14, RN20) e não podem depender de saída probabilística.
- **Stack:** um provedor de IA é dependência externa nova, fora da stack aprovada no AGENTS.md.
- **Base de dados:** previsões exigem histórico de vários períodos; o SGA ainda tem poucos períodos registrados.

### Recomendação

1. **Não implementar IA nesta entrega.** O risco acadêmico já é atendido por regras determinísticas e explicáveis.
2. Se a equipe quiser evoluir: começar por um **assistente de FAQ sobre a documentação pública**, sem acesso a dados de alunos, e só depois de definir provedor, custo e política de privacidade.
3. Qualquer uso com dados de alunos exige avaliação LGPD prévia e mantém a decisão final com humanos.

## Decisão solicitada

| ID | Pergunta | Proposta |
| --- | --- | --- |
| D8 | Construir app mobile nesta evolução? | Não; web responsiva (opção A); PWA como próximo passo, se houver demanda |
| D9 | Implementar IA nesta evolução? | Não; manter a sinalização de risco determinística |

## Referências

- [Estudo de API pública e integrações](SGA-13-ESTUDO-API-INTEGRACOES.md)
- [Especificação da Fase 3](SGA-12-ESPECIFICACAO-FASE-3.md)
- [Relatórios e integração](SGA-10-RELATORIOS-INTEGRACAO.md)
