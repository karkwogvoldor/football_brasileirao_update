# Fluxo automatizado de revisão de cenas

Decisão: as revisões do laboratório (`/dev/cenas`) deixam de viver só no `localStorage`.

1. **Ida.** A página envia as revisões para `PUT /api/v1/dev/scene-reviews`, que grava
   `data/dev/scene-reviews.json` (ignorado pelo git; diretório configurável por
   `BRAFOOT_DEV_REVIEW_DIR`). O navegador é a fonte da verdade; o servidor só preenche
   revisões ausentes ao carregar.
2. **Processamento.** O agente lê `scene-reviews.json`, trata as cenas com status
   `changes_requested`, ajusta a cena e incrementa o `version` dela no catálogo.
3. **Retorno.** `scripts\devolver_ajuste_cena.py ID DE PARA "resumo"` grava
   `data/dev/scene-returns.json`.
4. **Azul.** Se a cena está na versão `to_version`, ainda sem nova avaliação, e a versão
   `from_version` estava em `changes_requested`, a página mostra "Pronta para nova
   revisão" (azul) com o resumo do ajuste. Aprovar ou pedir novo ajuste reinicia o ciclo.

Os endpoints são de desenvolvimento e não usam o banco da aplicação.
