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
