'use strict';
const botaoImprimir = document.getElementById('imprimir-relatorio');
if (botaoImprimir) {
    botaoImprimir.addEventListener('click', () => window.print());
}
