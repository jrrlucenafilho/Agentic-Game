# Relatório: Desenvolvimento de Jogos com Agentes de Programação

# Seção 1: Experiência Prévia

## Nome: José Ricardo Rodrigues de Lucena Filho
Possuo experiência no domínio de desenvolvimento de jogos em C++, tendo feito alguns jogos nessa
linguagem com frameworks custom. Possuo pouca experiência com HMTL/Javascript/Typescript, tendo feito
apenas sites simples com essas tecnologias.

## Nome: João Viana+
**

# Seção 2: Desenvolvimento do Jogo

## Relatório referente ao processo de programação desse jogo, utilizando agentes

---

O modelo utilizado nesse momento é o `Qwen3.6 Plus` pelo `OpenCode` com reasoning set no `High`
Iniciei com um prompt detalhando como deve ser o loop de gameplay do jogo, especificando os comportamento possíveis
e as informações necessárias para construir uma forma simples do jogo, inspirado em jogos `Party` de múltiplos
jogadores, em especial `Super Smash Bros.` e `Bopl Battle`, mas com nossas personalizações a fim de trazer originalidade
De início o agente terminou o processamento produzindo uma versão que leva diretamente para uma partida, sem bugs aparentes, mas em HTML+JS. A fim de testes pedi para ele mudar a implementação para Python utilizando pygame e ele produziu uma versão que iniciava com um bug devido a um valor negativo na altura inicial da água. Mas após a ocrreção desse bug simples, ao testar o jogo escobrimos que ele permitia ignorar colisão com plataformas em certos edge cases. Mas após essa correção o jogo estava perfeitamente jogável e sem mais bugs aparentes
Depois de algumas correções tanto usando agentes quanto manuais no código. Os bugs relacionados às colisões foram corrigidos
Adicionado uma tela de vitória com prompt para restart

---
Mudamos o modelo para o `deepseek-v4-flash` a separamos as features a serem adicionadas:
- Substituir plataformas por planetoides com gravidade própria
- Modificar a mecânica de tiro para permitir mirar cada tiro
- Adicionar mais hazards à arena

## Feat 1
De início pedimos para o agente substituir as plataformas com planetoides que possuem sua próŕia gravidade.

Prompt:
```
The platforms should be circle-shaped with their own gravity (like planets), and they should pull in nearby 
player characters towards themselves
```

Isso modificou corretamente as plataformas, mas a gravidade ainda não estava correta, a gravidade dos
planetoides só fazia efeito

## Feat 2

## Feat 3

# Seção 3: Conclusões
