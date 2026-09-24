# Transferências simplificadas — Fase 2

Escopo: #36 (transferências), #49 e #61; contribuição para #51.
Base inicial: `49987815235f6661bfc578e133d4a5bb9371afd1`.

## Decisões de implementação

Andrey autorizou escolher as regras pendentes durante a implementação, em
20/09/2026. As escolhas abaixo deverão ser revisadas no PR pelo João.

| Tema | Contrato adotado | Origem |
| --- | --- | --- |
| Fluxo | Solicitação pendente, aprovada ou recusada | #49 e #61 |
| Perfis | Secretaria registra; Coordenação decide; ambas consultam; Aluno consulta somente seus registros; Professor não acessa | Decisão delegada por Andrey; separação administrativa/pedagógica |
| Superusuário | Conta ativa de superusuário pode registrar, consultar e decidir, como nos decorators existentes | Convenção do projeto |
| Tipos | Entrada de instituição externa ou saída para instituição externa | SGA-08, proposta de transferências |
| Curso | FK protegida ao curso interno; instituição e curso externos como texto | SGA-08: não existe vínculo Aluno–Curso independente de matrícula |
| Efeito da aprovação | Registro administrativo aprovado e auditado; não cria, cancela, transfere nem reativa matrículas; não modifica conta, notas ou faltas | Decisão delegada; SGA-08 propõe transfers sem alterar Matricula/Nota/Falta |
| Duplicidade | No máximo uma pendente para aluno + tipo + curso interno + instituição/curso externos normalizados; a data não permite contornar a duplicidade | SGA-08: solicitação pendente equivalente |
| Nova solicitação | Permitida depois de decisão anterior; registro anterior permanece intacto | Decisão de implementação |
| Documentos | Registro textual obrigatório da documentação apresentada ou de sua dispensa justificada; sem upload nesta etapa | #49 permite anexar **ou registrar** |
| Datas | Data de referência informada no registro; criação e decisão com timestamps do servidor; sem execução agendada | #36 e rastreabilidade da #61 |

A aprovação **não efetiva matrícula acadêmica nem encerra matrículas existentes**.
Essas ações permanecem nos serviços administrativos já existentes e não são
disparadas automaticamente. Nenhum vínculo acadêmico novo é inferido da
transferência. A interface deve explicar esse limite antes de registrar e decidir.

## Integridade

- Aluno precisa ter papel ALUNO; no cadastro deve estar ativo, assim como o curso.
- Inativação posterior não apaga a solicitação nem impede a decisão administrativa.
- Origem/destino internos são representados pela instituição atual e pelo curso
  protegido; os externos são obrigatórios. Entrada e saída invertem sua direção.
- Equivalência textual usa normalização Unicode, espaços e casefold. A chave
  derivada é protegida por unicidade condicional no banco.
- Decisões finais são irreversíveis neste fluxo e exigem justificativa.
- Criação/decisão e auditoria são atômicas. Decisão usa lock e atualização
  condicional para impedir reprocessamento.
- Relações históricas usam PROTECT; nenhuma tela oferece edição ou exclusão.

## Plano dos nove commits

1. Escopo e decisões; 2. modelo/migration; 3. solicitação; 4. decisão;
5. consultas/permissões; 6. interface; 7. testes de regras;
8. integração/concorrência; 9. documentação de entrega e validação.

A #36 e a #51 continuam dependentes das demais entregas da equipe.

## Rastreabilidade da entrega

| Issue/requisito | Implementação | Evidência automatizada |
| --- | --- | --- |
| #36: origem, destino, curso, situação | Modelo com tipo entrada/saída, curso interno protegido, instituição/curso externos; detalhe exibe direção | `test_solicitacao_pendente_origem_destino_e_auditoria` nos dois tipos |
| #36: obrigatórios e duplicidade | Formulário e validação no serviço; normalização Unicode/caixa/espaços; constraint condicional | `test_rejeita_dados_invalidos_sem_gravar`, `test_duplicidade_normaliza_caixa_espacos_unicode_e_ignora_data`, `test_constraint_impede_duplicata_sem_servico` |
| #36: histórico preservado | Serviços não alteram dados acadêmicos; FKs protegidas | `test_fluxo_preserva_historico_e_relatorios` nos dois tipos e decisões; `test_vinculos_historicos_protegidos` |
| #49: solicitação e documentos | Secretaria cria pendente; data e registro textual documental obrigatórios | `test_secretaria_cria_e_consulta_pela_interface`, `test_formulario_obrigatorio_e_duplicidade_exibem_erros` |
| #61: análise autorizada e rastreável | Coordenação decide com justificativa, responsável, horário e auditoria | `test_decisao_tem_autor_data_justificativa_e_nao_se_repete`, `test_somente_coordenacao_decide` |
| #61: alterações somente após aprovação | Sem efeitos acadêmicos automáticos; aprovação/recusa alteram exclusivamente estado administrativo e trilha da decisão | `test_fluxo_preserva_historico_e_relatorios`; contrato de efeito administrativo a ser revisado por João |
| #61: integridade da decisão | Transação, lock de linha, atualização condicional, auditoria na mesma transação | `test_falha_auditoria_reverte_decisao`, `test_concorrencia_real_postgresql` |
| #51: integração e RBAC | URLs, menu, templates; aluno limitado aos próprios registros; CSV existente preservado | `test_aluno_so_consulta_propria_solicitacao`, `test_acesso_direto_criacao_proibido`, `test_post_decisao_sem_permissao`, `test_fluxo_preserva_historico_e_relatorios` |
| #36/#51: consultas, filtros e navegação | `select_related`, paginação de 20 registros, filtros validados por situação/tipo/curso | `test_consultas_relacionadas_nao_crescem_por_linha`, `test_paginacao_e_filtros_preservados`, `test_filtros_invalidos_e_lista_vazia` |

Arquivos centrais: `apps/transfers/` (modelo, migration, permissões, serviços,
consultas, formulários, views e URLs), `templates/transfers/`, menu compartilhado,
registro do app/URLs em `config/` e `tests/test_transfers/`.

## Executar e revisar

1. Atualize a branch da entrega e instale as dependências de `requirements/local.txt`.
2. Configure o banco conforme o README e execute `python manage.py migrate`.
   A migration nova é `transfers.0001_initial`; nenhuma migration compartilhada
   foi reescrita. Ela cria uma tabela e constraints, sem migrar registros acadêmicos.
3. Use contas de demonstração com papéis Secretaria, Coordenação e Aluno,
   um aluno ativo e um curso ativo. O seed existente pode fornecer esses cadastros.
4. Como Secretaria, abra **Transferências → Registrar transferência**. Selecione
   entrada ou saída e informe aluno, curso interno, instituição/curso externos,
   data e documentos. Confirme que surge uma solicitação pendente.
5. Tente cadastrar a mesma pendente com letras/ espaços diferentes e confira o
   bloqueio. Tente enviar campos vazios e confira as mensagens.
6. Como Coordenação, consulte o detalhe e aprove com justificativa. Confira
   autor, data e situação; a tela não permite nova decisão. Em outra solicitação,
   teste a recusa com justificativa e a rejeição de justificativa vazia.
7. Como Aluno, confira apenas suas solicitações; outro ID deve retornar 404.
   Professor não acessa o módulo. Secretaria não decide e Coordenação não cria,
   salvo superusuário ativo, conforme a convenção existente.
8. Confira filtros/paginação e compare matrículas, notas, frequência e relatórios
   antes/depois. Nenhum desses registros deve mudar pela transferência.

Comandos locais usados (Python 3.12, ambiente virtual):

```bash
USE_SQLITE=True python manage.py migrate --noinput
USE_SQLITE=True python manage.py check
USE_SQLITE=True python manage.py makemigrations --check --dry-run
USE_SQLITE=True pytest
USE_SQLITE=True pytest tests/test_transfers --no-cov
git diff --check
```

O CI existente também executa a suíte com PostgreSQL 16. Os dois casos de
concorrência usam conexões independentes e threads para disputar criação e
aprovação/recusa; são pulados explicitamente em SQLite, que não oferece os locks
de linha necessários. Não se deve apresentar execução SQLite como prova desses
locks. A reversão da migration remove a tabela de transferências: não a execute
em uma base com solicitações que precisam ser preservadas.

## Validação local em 20/09/2026

- Base inicial: 289 testes aprovados; cobertura 87,47%.
- Entrega: **349 testes aprovados, 2 pulados (concorrência PostgreSQL)**;
  cobertura total **88,55%**, acima do mínimo de 85%.
- 62 casos novos: 60 aprovados em SQLite e os 2 casos específicos de PostgreSQL.
- `check`: sem problemas; `makemigrations --check --dry-run`: sem alterações.
- Todas as migrations, incluindo a nova, aplicadas com sucesso em banco SQLite
  local novo. `git diff --check`: sem problemas.
- Um aviso de depreciação do Django sobre URLField já ocorria na base; nenhum
  teste foi removido nem requisito de cobertura reduzido.
- Revisão por leitura: requisitos, diff, permissões no servidor, estados,
  constraints, transações, relações históricas, consultas e templates.
- Testes automatizados: serviços, banco, HTTP/formulários/templates via cliente
  Django, acesso direto, CSRF, texto escapado, erros e integração com relatórios.
- **Navegador real: não validado localmente.** A instalação do Chromium não
  concluiu por indisponibilidade de download. Os testes HTTP não equivalem a
  inspeção visual/interação em navegador. O roteiro acima fica para a revisão.
- Docker e servidor PostgreSQL não estavam disponíveis localmente; a tentativa
  de instalar PostgreSQL foi impedida por permissões do ambiente. A confirmação
  no PostgreSQL depende do job correspondente do CI; consulte os checks do PR
  para seu resultado efetivo, posterior a este registro local.

## Revisão e pendências da equipe

- João: revisar código, regra de aprovação administrativa e decisões delegadas,
  executar roteiro visual e decidir o merge para `develop`.
- Max: continuar as pendências de relatórios da #62; não estão neste escopo.
- Equipe: concluir a validação conjunta da #51 e demais requisitos da #36.
- Não encerrar #36/#51 com esta entrega. #49/#61 devem ser avaliadas após revisão,
  integração e validação do contrato de negócio; o PR não as encerra automaticamente.
