# Semana 5 — conclusão dos relatórios e validação integrada

Escopo: #62 e #51, dentro da issue mãe #36. Andrey assumiu a entrega em 24/09/2026.
Base: `a41e42b5e467df9e6395060440c3a418c64f9ff3` (`develop`, após merge do PR #69).

## Levantamento

- #49 e #61 encerradas; transferência administrativa integrada no PR #69.
- #50 encerrada; notas, resultados, frequência, filtros e CSV já vieram no PR #68.
- #62 ainda aberta: faltavam identificação explícita de risco e impressão preparada.
- #51 ainda aberta: exige verificação conjunta de permissões, filtros e histórico.
- A #36 afirma que entregas individuais terminaram, mas a #62 permanece aberta:
  este documento e o novo PR explicitam essa pendência sem fechar issues antes da revisão.

## Regra de risco adotada para revisão

Indicador de acompanhamento por matrícula ativa, calculado sem persistência ou
mudança de nota, frequência, matrícula ou resultado oficial. Usa limites do
AGENTS.md e das regras acadêmicas existentes: média 6 e frequência mínima 75%.

- Frequência registrada abaixo de 75% gera alerta, mesmo com notas incompletas.
- Se houver média final, ela prevalece: abaixo de 6 gera alerta por nota.
- Sem média final, média parcial abaixo de 6 gera alerta; inclui elegíveis a exame
  e situações já reprovadas. O resultado oficial continua em coluna separada.
- Com avaliações incompletas, média simples das notas já lançadas abaixo de 6
  gera alerta **provisório**, identificado como avaliações incompletas. Notas
  ausentes não viram zero; não se apresenta essa média como média parcial oficial.
- Sem alerta, mas sem todas as notas ou sem aulas, mostrar “Dados insuficientes”.
- “Sem alerta nos dados disponíveis” não garante aprovação futura.
- A sinalização é descritiva dos dados atuais; não usa previsão estatística nem
  novos limiares preventivos arbitrários. João revisa essa regra no PR.

## Divisão dos cinco commits

1. Regra de risco e testes de limites; 2. filtros e CSV; 3. tela e impressão;
4. testes de integração com demonstração; 5. documentação e evidências finais.
