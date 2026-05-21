# Relatório referente ao processo de programação desse jogo, utilizando agentes

## Sessão 1
O modelo utilizado nesse momento é o `Qwen3.6 Plus` pelo `OpenCode` com reasoning set no `High`

Iniciei com um prompt detalhando como deve ser o loop de gameplay do jogo, especificando os comportamento possíveis
e as informações necessárias para construir uma forma simples do jogo, inspirado em jogos `Party` de múltiplos
jogadores, em especial o `Bopl Battle`, mas com nossas personalizações a fim de trazer origginalidade

De início o agente terminou o processamento produzindo uma versão que leva diretamente para uma partida, sem bugs aparentes, mas em HTML+JS. A fim de testes pedi para ele mudar a implementação para Python utilizando pygame e ele produziu uma versão que iniciava com um bug devido a um valor negativo na altura inicial da água. Mas após a ocrreção desse bug simples, ao testar o jogo escobrimos que ele permitia ignorar colisão com plataformas em certos edge cases. Mas após essa correção o jogo estava perfeitamente jogável e sem mais bugs aparentes

Depois de algumas correções tanto usando agentes quanto manuais no código. Os bugs relacionados às colisões foram corrigidos

Adicionado uma tela de vitório com prompt para restart
