# Fase 2 — motor de regras e recomendação

Data de referência: 19/10/2026. Diretriz: Python determinístico, sem LLM, inferência externa, GPU, chave de API ou novas dependências de runtime.

Status: **concluída e validada**. O verificador retornou `passed` em `phase2/summary.json`: 20 testes TypeScript e 53 testes Python aprovados, validação de dados, TypeScript, build, smoke HTTP e navegador. Os logs individuais estão na mesma pasta.

## Entrega

O chat continua usando `engine.respond(message, state)` e `POST /api/chat`. A interpretação de mensagens permanece no facade atual; a avaliação de catálogo, oferta, filtros, pontuação e explicação passou para módulos coesos em `chatbot/radar_ai`.

| Arquivo | Responsabilidade |
| --- | --- |
| `catalog.py` | Snapshot dos JSONs e validação de IDs, metadados e referências. |
| `policies.py` | Política versionada, validação de configuração, validade de ofertas e conversão monetária. |
| `rules.py` | Registro de regras, ordenação, dependências, exceções, efeitos atômicos, conflitos e trilha. |
| `offers.py` | Regras comerciais e seleção de oferta de uma única edição. |
| `recommendation.py` | Filtros obrigatórios e coordenação da avaliação de candidatos. |
| `scoring.py` | Pontuação e explicação pelos atributos reais do catálogo. |

Não foram criados placeholders de NLP/RAG/sessões para simular as fases seguintes. Os protótipos `knowledge.py` e `tools.py` continuam fora do fluxo HTTP do chat.

## Ordem de execução e falha segura

As camadas são: segurança/integridade → negócio obrigatório → restrições do usuário → compatibilidade → preferências → ranking. Regras podem declarar dependências apenas de sua camada ou de camadas anteriores. Ciclos, IDs repetidos e dependências inexistentes são erros de configuração.

Cada regra tem ID, versão, prioridade, condição, ação, dependências, exceções opcionais e incompatibilidades declaradas. Exceções de restrições opcionais são explícitas: por exemplo, não há filtro de orçamento quando o usuário não definiu um teto. Regras críticas de segurança, negócio e compatibilidade não admitem dispensa por exceção.

Ações retornam efeitos e não editam o resultado diretamente. Efeitos conflitantes são recusados antes de qualquer escrita desse conjunto. Duas regras ativas mutuamente exclusivas ou duas atribuições diferentes ao mesmo campo bloqueiam a decisão. Erro inesperado registra apenas o tipo da falha, rejeita o candidato e impede pontuação; não expõe dados de exceção ou ignora a restrição.

O catálogo é validado antes de consultar preços. IDs duplicados, referências órfãs e metadados estruturais inválidos bloqueiam recomendações comerciais. Uma oferta isolada com valor inválido é excluída; não é convertida para zero. Isso não confere confiabilidade editorial aos metadados preliminares.

## Correção do jogo nomeado

Antes, o caminho de jogo mencionado montava cards antes dos filtros. Agora todos os candidatos de recomendação, incluindo nomes explícitos e explicações de sugestões anteriores, passam pelo mesmo avaliador.

- `Recomende Gloomhaven para 8 pessoas até R$ 1`: nenhuma recomendação; rejeições incluem jogadores e orçamento/oferta.
- `Recomende Gloomhaven para 4 pessoas`: candidato aceito, com trilha das regras e componentes do score.
- `Fale sobre Gloomhaven para 8 pessoas até R$ 1`: ficha exclusivamente informativa em `game_details`, sem preço e com incompatibilidade indicada. `recommendations` e `ids` permanecem vazios.

A interface distingue a ficha informativa de uma recomendação e mostra que ela não atende à busca. Comparação aprofundada, interpretação de regras oficiais e classificação completa de intenções continuam nas fases 3–5. A distinção de intenção desta fase é limitada aos padrões já existentes e às consultas informativas explícitas; não representa compreensão irrestrita.

## Política e pesos preservados

`src/data/policy.json` é a configuração compartilhada, versão `2.0-phase2.1`. Pesos base: temas 25, estilo 25, videogames 25, complexidade 15, qualidade editorial 10. Somam 100 e são validados. O perfil de ranking `1.1-preserved` mantém as diferenças anteriores:

| Perfil | Comportamento preservado |
| --- | --- |
| Python | Prefere menor complexidade, aplica teto explícito, exige afinidade quando videogame é selecionado e preserva bônus de combate: tático +12, guerra +8, cooperativo +4; coleção −8. |
| TypeScript | Pontua proximidade da complexidade escolhida, usa afinidade padrão 0,5 sem preferência, não aplica bônus editorial de combate e mantém complexidade como preferência. |

Os dois perfis não passaram a ter resultados idênticos. Foram compartilhados os pesos e as invariantes comerciais/de quantidade/tempo. O empate mantém a ordenação por nome de cada implementação. Os scores não são porcentagem de confiança; o arredondamento Python e TypeScript também é preservado.

Mudança de coeficientes deve registrar nova versão e atualizar testes de ranking. O gerador `seed-v2.py` não sobrescreve mais a política da aplicação ao recriar conteúdo editorial.

## Preço, estoque e edição

Recomendação usa a primeira edição selecionada do jogo, que é a edição da ficha inicial; não agrega ofertas de outras edições ou expansões. A função de seleção aceita edição explícita somente se ela pertencer ao mesmo jogo.

Oferta elegível exige BRL, centavos inteiros positivos representáveis com segurança em JSON/JavaScript, loja demonstrativa existente, `is_demo=true`, disponibilidade `in_stock`, timestamp com timezone e idade entre zero e sete dias. Datas futuras, antigas ou inválidas não são atuais. Não há equivalência automática entre edições. Empate de preços não implica mesmo conteúdo.

`preferences.budget` continua em reais para preservar o contrato. Internamente, converte-se para centavos com Decimal no Python e conversão decimal explícita no TypeScript; fração inferior a um centavo é truncada, sem arredondar o teto para cima. Preço ausente é `null`, nunca zero. Um jogo sem oferta pode ser descoberto sem teto comercial, mas não é elegível quando existe orçamento máximo.

Frete segue fora do preço demonstrativo e nenhum botão permite compra real. `/out/{offerId}` continua retornando 403.

## Contrato e rastreabilidade

Campos existentes de resposta foram preservados. Metadados adicionais por recomendação: `eligible`, `is_demo`, `edition_id`, `offer_id`, `policy_version`, `rule_trace`, `offer_rule_trace` e `score_breakdown`. A trilha contém ID, versão, camada, prioridade, status e, quando necessário, motivo. Resultados rejeitados por nome retornam diagnóstico em `evaluation`, sem sugerir compra.

`game_details` contém apenas informação e incompatibilidades; não contém preço. A trilha é retornada no JSON para inspeção e não é persistida com o texto da conversa. O frontend não envia esses diagnósticos como estado de sessão nem precisa conhecer o motor de regras para funcionar.

## Verificações reproduzíveis

Na pasta `boardradar`:

```text
npm test
npm run typecheck
npm run validate-data
npm run build
node scripts/smoke.mjs
node scripts/check-chat-browser.mjs
```

Ou use o verificador desta fase:

```text
../.tools/python-3.13.7/python.exe scripts/verify-phase2.py --browser
```

Em outra máquina, use seu interpretador Python. O teste de navegador requer Chrome. O verificador grava logs, registro de regras, exemplos de respostas e hashes em `docs/v2/phase2`, sem sobrescrever o baseline histórico da Fase 1. Tempos de comandos não são benchmark de requisições.

Cobertura verificada: 20 testes TypeScript e 53 testes Python, incluindo os 23 originais. As nove fixtures de invariantes são consumidas pelos dois runtimes com relógio fixo. Os testes Python de ofertas usam snapshots independentes para criar expansão barata, referência órfã, ID duplicado, data inválida, preço inválido e catálogo corrompido. As contagens não significam que a meta final de 100 cenários distintos já foi atingida.

## Limitações e próxima fase

Os dados factuais e as edições continuam preliminares. Não há regra oficial fundamentada em manual autorizado, TTL de sessão, confiança heurística, comparação completa ou deploy serverless nesta entrega. “Tenho 200 reais” continua como lacuna de extração a tratar na Fase 3; não foi corrigida silenciosamente nesta refatoração.

Fase 3: modularização de NLP, entidades monetárias em centavos, intenções tipadas, sinônimos, nomes aproximados e ambiguidades. A base de regras desta fase será reutilizada; não substituir por inferência generativa.
