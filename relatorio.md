# Relatório: Desenvolvimento de Jogos com Agentes de Programação

# Seção 1: Experiência Prévia

## Nome: José Ricardo Rodrigues de Lucena Filho

Possuo experiência no domínio de desenvolvimento de jogos em C++, tendo feito alguns jogos nessa
linguagem com frameworks custom. Possuo pouca experiência com HMTL/Javascript/Typescript, tendo feito
apenas sites simples com essas tecnologias.

## Nome: João Viana+

\*\*

# Seção 2: Desenvolvimento do Jogo

## Relatório referente ao processo de programação desse jogo, utilizando agentes

---

O modelo utilizado nesse momento é o `Qwen3.6 Plus` pelo `OpenCode` com reasoning set no `High`
Iniciei com um prompt detalhando como deve ser o loop de gameplay do jogo, especificando os comportamento possíveis
e as informações necessárias para construir uma forma simples do jogo, inspirado em jogos `Party` de múltiplos
jogadores, em especial `Super Smash Bros.` e `Bopl Battle` e `DDTank`, mas com nossas personalizações a fim de trazer originalidade
De início o agente terminou o processamento produzindo uma versão que leva diretamente para uma partida, sem bugs aparentes, mas em HTML+JS. A fim de testes pedi para ele mudar a implementação para Python utilizando pygame e ele produziu uma versão que iniciava com um bug devido a um valor negativo na altura inicial da água. Mas após a ocrreção desse bug simples, ao testar o jogo escobrimos que ele permitia ignorar colisão com plataformas em certos edge cases. Mas após essa correção o jogo estava perfeitamente jogável e sem mais bugs aparentes
Depois de algumas correções tanto usando agentes quanto manuais no código. Os bugs relacionados às colisões foram corrigidos
Adicionado uma tela de vitória com prompt para restart

Prompt Inicial:

```
Create a 2D party battle game for two players inspired by Super Smash Bros and Bopl Battle.
The game should have:
- Two player characters on a screen with platforms
- Players can move left/right, jump, and wall jump
- Players can shoot projectiles (arrows) at each other
- A water hazard that rises from the bottom over time, forcing players upward
- Players have 3 lives; when they die (fall off screen or touch water), they respawn
- The last player standing wins the round
- Use simple rectangle-based collision and platforming physics
- Controls: Player 1 uses WASD + F to shoot, Player 2 uses Arrow Keys + L to shoot
```

Inicialmente o agente produziu o jogo em HTML+JS. Pedi então para converter para Python com pygame:

---

Mudamos o modelo para o `deepseek-v4-flash` a separamos as features a serem adicionadas:

- Feat 1: Substituir plataformas por planetoides com gravidade própria
- Feat 2: Modificar a mecânica de tiro para permitir mirar cada tiro
- Feat 3: Substituir hazard de água subindo para uma chuva de meteoros
- Feat 4: Adicionar um background de espaço
- Feat 5: Adicionar hazard extra (UFO que ataca ambos os jogadores)
- Feat 6: Adicionar pontuação, ignorando mortes acidentais
- feat 7: Adicionar clashes em swings de sabres de luz

## Feat 1

De início pedimos para o agente substituir as plataformas com planetoides que possuem sua própria gravidade.

Prompt:

```
Make it so the platforms are roughly circle-shaped with their own gravity (like planets), and they should pull in nearby
player characters towards themselves, yet only the nearest one should pull the player the to it's own surface.
```

Isso modificou corretamente as plataformas, mas a gravidade ainda não estava correta, pois como estava, a gravidade dos
planetoides só fazia efeito quando o jogador fazia contato direto com o chão de cada planetoide, ou seja, não era o comportamento desejado.
O que demanda mais prompts de correção

Após uma quantidade considerável de prompts para corrigir tanto a rotação dos personagens quanto o controle
deles para navegação (para fazer sentido com as mudanças e interações das gravidades), a navegação foi melhorada
a ponto de alcançar o desejado

## Feat 2

Pedimos para o agente modificar a mecânica de tiro, antes um tiro instantâneo em linha reta, para um sistema de
carregamento com mira direcional.

Prompt:

```
Implement an arrow charge mechanic for shooting. The player should be able to hold the shoot button to charge,
and an aim arc should be shown indicating the trajectory. Release to fire in the aimed direction. Also add a
hover state when the player is within 2+ gravity fields without touching ground, allowing movement
in any direction with friction.
```

## Feat 3

Pedimos para substituir o hazard de água subindo por uma chuva de meteoros constante.

Prompt:

```
Replace the water rising mechanic with a meteor spawning system. Meteors should fall from the sky,
deal damage on collision, and create particle effects. Also adjust gravity and jump force to feel
better with the new hazard.
```

## Feat 4

Pedimos para adicionar um fundo de espaço estrelado, que veio junto com a feat 3.

Prompt:

```
Add a space background with a procedural starfield and a Saturn-like planet decoration.
Use a dark color scheme to fit the space theme.
```

## Feat 5

Pedimos para adicionar um UFO que ataca ambos os jogadores como um hazard extra.

Prompt:

```
Add a UFO that spawns periodically and attacks both players with laser beams. It should have
entering, attacking, and leaving states. The UFO beams should deal damage to players on hit.
```

## Feat 6

Pedimos para adicionar um sistema de pontuação, contabilizando mortes causadas por hazards/oponentes mas ignorando
mortes acidentais (como sair da tela).

Prompt:

```
Add a scoring system that tracks kills for P1 and P2. Only count deaths caused opponent attacks,
not accidental deaths like falling off the screen or from any hazard. Display the score on screen
during the game and reset it when starting a new round.
```

## Feat 7

Pedimos para adicionar clashes (colisão) entre swings de sabres de luz, com partículas e recuo.

Prompt:

```
Add collision detection between lightsaber swipes. When two swipes collide, they should produce
particle effects at the collision point, apply knockback force to both owners, and mark both
swipes as completed.
```

## Refactor

Após as features, pedimos para refatorar o código monolítico em uma estrutura modular de pacotes.

Prompt:

```
Refactor the monolithic game.py into a modular package structure. Create separate modules for
config, core game loop, entities (player, platform, meteor, UFO, projectiles, particles),
rendering (background, HUD), and systems (spawner). Keep main.py as the entry point.
```

## Melhorias Pós-Refactor

Após a refatoração, continuamos refinando a mecânica com prompts adicionais:

### Movimento omnidirecional com pulo em qualquer direção

Prompt:

```
Implement omnidirectional movement so the player can jump in any direction (up, down, left, right)
based on the ground normal. Simplify the gravity field movement logic to use direct X and Y axes
instead of complex coordinate transformations.
```

### Suavização de transição gravitacional

Prompt:

```
Add a smooth transition when the player switches between gravity fields. When moving from hover state
(shared gravity) to a single gravity field, blend the controls over a few frames to avoid abrupt
changes in movement.
```

### Textura pixelada de asteroide e fundo planetário

Prompt:

```
Replace the simple circle/ellipse platform drawing with pixelated asteroid textures with irregular
borders and craters. Add procedural noise for visual variation. Also add a pixelated planetary
surface background with earthy colors and craters.
```

# Seção 3: Conclusões
