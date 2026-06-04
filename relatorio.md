# Relatório: Desenvolvimento de Jogos com Agentes de Programação

# Seção 1: Experiência Prévia

## Nome: José Ricardo Rodrigues de Lucena Filho

Possuo experiência no domínio de desenvolvimento de jogos em C++, tendo feito alguns jogos nessa
linguagem com frameworks custom. Possuo pouca experiência com HMTL/Javascript/Typescript, tendo feito
apenas sites simples com essas tecnologias. Já com a biblioteca pygame utilizada aqui, tenho
pouca experiência, apenas em tutoriais.

## Nome: João Viana+

\*\*

# Seção 2: Desenvolvimento do Jogo

## Relatório referente ao processo de programação desse jogo, utilizando agentes

---

O modelo utilizado nesse momento é o `Qwen3.6 Plus` pelo `OpenCode` com reasoning set no `High` e utilizando as skills `andrej-karpathy-skills`.
Iniciei com um prompt detalhando como deve ser o loop de gameplay do jogo, especificando os comportamento possíveis
e as informações necessárias para construir uma forma simples do jogo, inspirado em jogos `Party` de múltiplos
jogadores, em especial `Super Smash Bros.` e `Bopl Battle` e `DDTank`, mas com nossas personalizações a fim de trazer originalidade
De início o agente terminou o processamento produzindo uma versão que leva diretamente para uma partida, sem bugs aparentes, mas em HTML+JS. A fim de testes pedi para ele mudar a implementação para Python utilizando pygame e ele produziu uma versão que iniciava com um bug devido a um valor negativo na altura inicial da água (`ae14cae`). Mas após a ocrreção desse bug simples, ao testar o jogo escobrimos que ele permitia ignorar colisão com plataformas em certos edge cases. Mas após essa correção o jogo estava perfeitamente jogável e sem mais bugs aparentes
Depois de algumas correções tanto usando agentes quanto manuais no código. Os bugs relacionados às colisões foram corrigidos
Adicionado uma tela de vitória com prompt para restart (`e6ade37`)

Prompt Inicial (`f729fb2`):

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

Inicialmente o agente produziu o jogo em HTML+JS (`f729fb2`). Pedi então para converter para Python com pygame:

---

Mudamos o modelo para o `deepseek-v4-flash` a separamos as features a serem adicionadas (`a557c25`):

- Feat 1: Substituir plataformas por planetoides com gravidade própria
- Feat 2: Modificar a mecânica de tiro para permitir mirar cada tiro
- Feat 3: Substituir hazard de água subindo para uma chuva de meteoros
- Feat 4: Adicionar um background de espaço
- Feat 5: Adicionar hazard extra (UFO que ataca ambos os jogadores)
- Feat 6: Adicionar pontuação, ignorando mortes acidentais
- Feat 7: Adicionar clashes em swings de sabres de luz
- Feat 8: Adicionar Colisões de tiros
- Feat 9: Adicionar chance de planetoides em movimento horizontal
- Feat 10: Melhoras na HUD para tornar os dados de cada jogador mais destacados

## Feat 1: Planetoides com Gravidade Própria (`9ce53f9`, `e261319`)

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

## Feat 2: Mecânica de Tiro com Mira (`718900e`)

Pedimos para o agente modificar a mecânica de tiro, antes um tiro instantâneo em linha reta, para um sistema de
carregamento com mira direcional.

Prompt:

```
Implement an arrow charge mechanic for shooting. The player should be able to hold the shoot button to charge,
and an aim arc should be shown indicating the trajectory. Release to fire in the aimed direction. Also add a
hover state when the player is within 2+ gravity fields without touching ground, allowing movement
in any direction with friction.
```

Foram necssários alguns prompts extras, pois inicialmente o arco de indicador de mira estava eguindo uma orientação contrária, devido à forma como o pygame
escolhe qual ãngulo desenhar (sempre o menor). Foi necessário pedir para ele remover o arco e depois reimplementar levando em conta esse comportamento da biblioteca pygame

## Feat 3: Chuva de Meteoros (`249169e`)

Pedimos para substituir o hazard de água subindo por uma chuva de meteoros constante.

Prompt:

```
Replace the water rising mechanic with a meteor spawning system. Meteors should fall from the sky,
deal damage on collision, and create particle effects. Also adjust gravity and jump force to feel
better with the new hazard.
```

Esse prompt funcionou mais diretamente, os prompts adicionais foram apenas uma mudança que fez o UFO escolher um player para atirar em vez de atirar nos dois jogadores de uma
só vez. Fora isso o agente implementou como esperado

## Feat 4: Background Espacial (`249169e`)

Pedimos para adicionar um fundo de espaço estrelado, que veio junto com a feat 3.

Prompt:

```
Add a space background with a procedural starfield and a Saturn-like planet decoration.
Use a dark color scheme to fit the space theme.
```

A ideia seria que a gravidade fora dos planetoides vem do planeta maior abaixo, portanto foi adicionado essa mudança no background.
Essa ideia precisou de mais alguns prompts adicionais. pois o agente insistia em, inicialmente, adicionar uma camada monstrando explicitamente
a gravidade no desenho, e isso acabou fazendo com que o semicírculo do planeta ficasse incompleto. Portanto as próximas prompts adicionais só corrigiram esse erro.

## Feat 5: UFO como Hazard Extra (`40d9a4e`)

Pedimos para adicionar um UFO que ataca ambos os jogadores como um hazard extra.

Prompt:

```
Add a UFO that spawns periodically and attacks both players with laser beams. It should have
entering, attacking, and leaving states. The UFO beams should deal damage to players on hit.
```

Esse prompt funcionou mais diretamente, os prompts adicionais foram apenas uma mudança que fez o UFO escolher um player para atirar em vez de atirar nos dois jogadores de uma
só vez. Fora essa mudança de comportamento do UFO o agente implementou como esperado

## Feat 6: Sistema de Pontuação (`ab0518a`)

Pedimos para adicionar um sistema de pontuação, contabilizando mortes causadas por hazards/oponentes mas ignorando
mortes acidentais (como sair da tela).

Prompt:

```
Add a scoring system that tracks kills for P1 and P2. Only count deaths caused opponent attacks,
not accidental deaths like falling off the screen or from any hazard. Display the score on screen
during the game and reset it when starting a new round.
```

O prompt funcionaou diretamente, sem prompts extras necessários

## Feat 7: Clashes de Sabres de Luz (`98496ea`, `ab8fc30`)

Pedimos para adicionar clashes (colisão) entre swings de sabres de luz, com partículas e recuo.

Prompt:

```
Add collision detection between lightsaber swipes. When two swipes collide, they should produce
particle effects at the collision point, apply knockback force to both owners, and mark both
swipes as completed.
```

## Refactor (`314f212`)

Após as features, o código acabou desorganizado e monolítico em apenas um arquivo.
Portanto, pedimos para refatorar o código monolítico em uma estrutura modular de pacotes.

Prompt:

```
Refactor the monolithic game.py into a modular package structure. Create separate modules for
config, core game loop, entities (player, platform, meteor, UFO, projectiles, particles),
rendering (background, HUD), and systems (spawner). Keep main.py as the entry point.
```

## Melhorias Pós-Refactor

Após a refatoração, continuamos refinando a mecânica com prompts adicionais:

### Movimento omnidirecional com pulo em qualquer direção (`350186c`)

Prompt:

```
Implement omnidirectional movement so the player can jump in any direction (up, down, left, right)
based on the ground normal. Simplify the gravity field movement logic to use direct X and Y axes
instead of complex coordinate transformations.
```

Melhorou a navegação que antes era baseada na gravidade para uma navegação onde as direções são globais e sempre as mesmas (Setas sempre
vão nas direções esperadas), diferente de como era antes, onde direita/esquerda mudava dependendo da gravidade dos planetoides.

Para tal, também colocamos que, quando sob o efeito da gravidade de 2 ou mais planetoides, as gravidades se cancelam.

### Suavização de transição gravitacional (`7c6227d`)

Prompt:

```
Add a smooth transition when the player switches between gravity fields. When moving from hover state
(shared gravity) to a single gravity field, blend the controls over a few frames to avoid abrupt
changes in movement.
```

Devido ao comportamento especial do caso de 2 ou mais gravidades do prompt anterior, a transição entre "modo-apenas-1-gravidade"
"modo-2-ou-mais-gravidades" estava muito abrupta e confusa para os jogadores. Esse prompt (e alguns mais após esse) foram feitos para
corrigir essa transição, fazneo uma suavização na transição entre esses 2 modos.

### Textura pixelada de asteroide e fundo planetário (`6fda259`)

Prompt:

```
Replace the simple circle/ellipse platform drawing with pixelated asteroid textures with irregular
borders and craters. Add procedural noise for visual variation. Also add a pixelated planetary
surface background with earthy colors and craters.
```

Adiciona texturas com crateras aos planetoides, fazendo-os mais cabíveis ao tema espacial.
Foram necessários alguns prompts a mais para corrigir erros nas texturas, pois o agente quiz incluir sombras, o que causava
transparência indesejada devido a erros do uso do canal alpha do pygame.

### Melhoria na visualização do arco de mira (`f3640c9`)

O arco de mira, antes desenhado com `pygame.draw.arc`, foi substituído por uma renderização manual
com segmentos de linha que conectam pontos ao longo do arco, formando um leque mais visível e
estilizado. A linha central de direção também foi ajustada para usar o raio do arco como
comprimento, resultando em um visual mais coerente e legível.

Prompt:

```
Replace the aim arc drawn with pygame.draw.arc with a manual line-segment
fan visualization. Draw multiple lines from the center outward along the arc
angle range to form a more visible fan shape. Also make the central aim
direction line length match the arc radius for visual consistency.
```

Foram necessários mais 2 prompts para normalizar o tamanho do arco com o dos outros elementos de mira, mas apenas isso e ele funcionou como esperado

### Melhoria de UX ao atirar, manter posição pós-tiro

Prompt:

```
In the game, after taking a shot my player character immediately starts goin in the shot's direction.
Make it so that it stays still just after taking a shot so it doesn't immediately goes in the direction of the shot
```

Após um prompt a mais para tornar mais específico o que queremos, a implementação foi feita

Prompt:

```
Still, when i do a shot and keep holding the button (as is the expected behavior) the player immediately follows the shot's direction,
make it wait for another movement from the player (that's not a shot being aimed) for it to actually move the character

```

Após essa especificação melhor, o problema foi corrigido.

## Feat 8: Tiros se quebram ao colidir entre si

Adicionamos detecção de colisão entre os tiros dos jogadores. Quando dois tiros se encontram,
ambos são anulados com partículas brancas no ponto de colisão,
seguindo o mesmo padrão visual do clash de sabres de luz.

Prompt:

```
Make it so when player's shots collide with each other, it cancels (causes collision)
between the shots with a few particles flying out
```

Não foram necessários prompts extras para essa feature.

## Feat 9: Adicionar planetoides com movimento horizontal

Prompt:

```
Make it so that some planetoids have a chance of moving horizontally.
They should collide with other planetoids on their way in a physics-sensible way.
And also these select planetoids (just a chance for they to appear per stage/round) should
continuously move from left to right, and once they reach the end of the screen they should
turn back around and do it again continuously
```

Precisamos de alguns prompts extras, pois o agente estava tratando os planetoides em movimento como
meteoros. E além disso a colisão entre meteoros Não estava funcionando como esperado de elementos no
espaço (um pequeno hover ao mínimo, pós-colisão). E o agente também tinha esquecido de adicionar o círculo
de gravidade ao redor dos planetoides em movimento.

## Feat 10: Melhoras na HUD para tornar os dados de cada jogador mais destacados

Prompt:

```
Change the HUD so that the buttons and scores are all unified in a rounded-corner
square at the top-left and top-rightfor each player, the HUD color should match the
respective player's color and should have a slightly translucent background
```

Não foram necessários prompts extras, apenas modificamos a aparência levemente para adicionar bordas
e fazer a explicação do que cada tecla faz

## Segundo Refactor

Após todas as mudanças das features, pedimos por mais refactors (além de refactors não feitos pelo agente)
a fim de diminuir "recriações da roda" que estavam sendo feitas, algo comum que acontece mesmo com desenvolvimento
com human-in-the-loop.

Prompt:

```
Check the codebase file structure and individual files.
Is the code clean? Can it be refactored any better? Evaluate it's formatting
```

# Seção 3: Conclusões e Comentários

## Para quem não tinha experiência prévia com as tecnologias usadas e/ou o desenvolvimento
## de jogos, vocês acham que essa falta de experiência teve impacto no desenvolvimento do
## projeto? Caso fossem continuar esse projeto, pensam que seria necessário estudar mais
## sobre as tecnologias e/ou sobre desenvolvimento de jogos em geral?

Tendo alguma experiência prévia com pygame, consigo ver os padrões do game loop. Mas em detalhes específicos
como a forma que o agente decidiu implementar a dinâmica de gravidades e como elas interagem entre si através da biblioteca.
Coisas como colisões e geração de partículas utilizando pygame, e não saber como essas coisas podem ser feitas certamente afetou na qualidade do
código e nos algoritmos usados, já que o agente não pensa profundamente nos pros/cons de cada abordagem para essas coisas sempre, apenas se for
explicitamente pedido a fazer isso.

Caso continuássemos o projeto, seria importantíssimo diminuir a dívida técnica. o que significa olhar a documentação da biblioteca pygame
e revisar os algoritmos ustilizados pelo agente. Mas, ao chegar nesse ponto, seria viável continuar o desenvolvimento do projeto
de forma mais manual.

## O que aprenderam durante o desenvolvimento do projeto? Conseguiriam fazer um projeto
## similar sem o uso de agentes de codificação?

Um aprendizado importante foi a seriedade da dívida técnica, pois deixar que o agente faça certas partes do código e não revisar
desde que a parte delegada ao agente funcione corretamente deixa todas essas partes como uma black box, o que não é de forma alguma escalável para
projetos maiores.
Outro comportamento aprendido é que os agentes, mesmo com `thinking` alto, tendem a ser bem orientados a objetivos, como se sue approach fosse
"Desde que funcione está correto", e isso é péssimo para a qualidade e manutenabilidade do código aolongo prazo. Mas algo que têm ajudado é
espcificar a estrutura desejada e perguntar periodicamente sobre o estado do código e sore possíveis refatorações, não parece ser tão efetivo
para a manutenabilidade do código quanto em uma programação manual. Mas fazer isso ajudou bastante na manutenabilidade.
Como projeto de disciplina, é plausível, sim, fazer um projeto similar (acabando até provavelmente com menos refatorações necessárias). Mas
seria necssário aprender sobre as bibliotecas usadas juntamente. Portanto é inegável que os agentes podem acelerar esse processo.

## Olhando o código da versão final, acham que o resultado é legível? Seria fácil de manter
## no futuro? Acham que seria necessário refatorar o código?

Devido aos prompts periódicos, o código até que ficou mais bem estrututrado do que no início.
Mas é necessaŕio fazer esses pedidos constantemente á medida que vai se adicionando novas features, pois o agente é tende a só fazer
o que é pedido e acaba ignorando as boas práticas se não for direcionado a seguí-las.
Por exemplo, antes da primeira refatoração o código estava inteiramente monolítico em um arquivo só, com lógica misturada, não isolada em classes,
sem separação de responsabilidades e com números mágicos, ou seja, menos que ideal no quesito de manutenabilidade.
Mas com refatorações periódicas (e as vezes manuais), foi possível sanar boa parte desses problemas.

## Já comentamos sobre o conceito de déficit de compreensão (comprehension debt). Sentem que
## entendem o projeto que foi gerado? Se fosse necessário fazer mais modificações, conse
## guiriam fazer alterações sem usar agentes? Como conseguem julgar se uma modificação
## pedida ao agente foi bem sucedida?

Como disse antes, partes do projetos que funcionaram "de primeira" viram blackboxes se não forem verificadas, e o déficit de compreensão se aloja principalmente
nessas partes. Após pedir por refatorações do código é possível compreender as partes que foram mais abordadas (principalmente as que mais precisaram ser refeitas e
que precisaram de prompts adicionais, pois simplesmente foram mais visitadas). Portanto, nessas partes que necessitaram de maior interenção seria possível, sim, fazer mais modificações.
Já em partes em qua isso não ocorreu, modificações só seriam viáveis após checar os algoritmos e como eles se integram com outra spartes do código.
Mas com certeza os periódicos prompts de refatoração e code cleanliness foram de imensa ajuda, pois a divisão do cóigo em partes com responsabilididades únicas
(ou pelo menos em partes com o mínimo sensível de responsabilidades) ajudaria muito em modificações futuras, pois com o código mais modularizado fica muito mais fácil saber
onde deverão ser feitas mudanças futuras, tanto para features quanto para correções ou modificações. Isso mostra que diretamente se preocupar com o refatoramento
do código de forma periódica ajuda bastante na compreensão e manutenabilidade futura, podendo ser uma maneira de facilitar a revisão do código e atenua o déficit de compreensão.

Nas partes que conhecemos é possível apenas checando o código. Mas em partes do código que envolvem funções que desconhecemos, só há saídas como perguntar ao
agente os motivos de cada mudança no código, e as motivações de cada escolha, mas isso é bem sensível a alucinações, principalmente em sessões distantes uma da outra e
em modelos com janela de contexto pequenas.
Portanto, para atenuar isso em partes do código que não conhecemos, foi pensado, por exemplo, permitir que o agente busque online, tanto em pesquisas
na internet quanto especificamente entregando documentação, seja em sites ou documentos (claro que sendo o mais específico possível para lidar com
as limitações da janela de contexto), isso ajuda o modelo a explicar suas escolhar, e muitas vezes até a se corrigir em decisões passadas.
Claro que isso não é uma garantia de que uma mudança foi bem sucedida, mas é uma solução relativamente útil, que ao juntarmos com a aplicação de testes
pelo modelo, diminui a surface area de erros significativamente. Ou seja, no melhor caso (conhecemos as tecnologias) revisamos o código. Mas em casos em
que isso não é verdade, oferecer documentação das tecnologias ao agente + pedir para rever suas escolhas + refatoração periódica + fazer testes para
cada nova adição/modificação + revisão por outro agente têm sido uma maneira razoável de verificar se as mudanças foram bem sucedidas, claro que mesmo assim ainda não se compara
à revisão manual, mas considerando os pros/cons, esse têm sido um workflow sólido para esse tipo de trabalho.
