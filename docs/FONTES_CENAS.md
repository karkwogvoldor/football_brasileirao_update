# Fontes e premissas das cenas do laboratório

As cenas novas foram desenhadas a partir de princípios táticos descritos em material de
treinamento, para reduzir rodadas de revisão. Fontes consultadas (pesquisa web, nov/2026):

- **Cruzamento** (`ball-cross-far-post`): corredor do primeiro pau puxa o goleiro e a marcação,
  corredor do segundo pau ocupa o espaço até cerca de 10 jardas além do poste, um terceiro
  ocupa a área de trás; as corridas começam pouco antes do toque do cruzador.
  [Cross (association football) — Wikipedia](https://en.wikipedia.org/wiki/Cross_(association_football)),
  [Elite Soccer Coaching — crosses from danger zones](https://elitesoccercoaching.net/attacking/crosses-from-danger-zones),
  [FIFA Training Centre — using wide areas](https://www.fifatrainingcentre.com/en/game/game-insights/using-wide-areas.php).
- **Linha de impedimento** (`movement-offside-trap`): a zaga sobe junta, em linha reta, no
  momento do passe em profundidade; é uma ferramenta, não a única solução defensiva.
  [Total Football Analysis — offside trap and high line](https://totalfootballanalysis.com/article/how-to-coach-the-offside-trap-and-the-high-line-tactical-analysis-training-analysis-tactics),
  [Coaching American Soccer — The Offside Trap](https://coachingamericansoccer.com/?p=5179).
- **Tiro de meta curto** (`ball-goal-kick-short`): desde 2019/20 o tiro de meta pode ser
  recebido dentro da área; o goleiro entra na construção, os zagueiros abrem na área e os
  laterais sobem altos e largos (formação 3-2), atraindo a pressão.
  [FIFA Training Centre — building from goal kicks](https://www.fifatrainingcentre.com/en/game/game-insights/building-from-goal-kicks.php),
  [Breaking The Lines — goal kick setups](https://breakingthelines.com/tactical-analysis/variation-of-goal-kick-setups).
- **Escanteio/ocupação da área** (referência de posicionamento defensivo dentro da área):
  [FIFA Training Centre — set plays](https://www.fifatrainingcentre.com/en/game/game-analysis/set-plays/corners/targeting-the-front-post.php).

As fontes são sites de treinamento, não uma referência única; os números (coordenadas)
são uma tradução visual dos princípios, não medições.

## Premissas geométricas

Coordenadas em % do campo (105 m × 68 m): 1% em x ≈ 1,05 m; 1% em y ≈ 0,68 m. Gol: y 45–55;
grande área: x ≥ 84 (e ≤ 16 para o outro lado), y 20–80; pequena área: x ≥ 95.

## Critérios automáticos (testes)

- Nenhum jogador das cenas novas excede 8,5 m/s (velocidade humana de corrida).
- Goleiros fora da linha do gol; zaga em linha única; sem teletransporte da bola.
- Zaga só entra na área quando a cena libera `defender_min_x` (cruzamento, tiro de meta).
