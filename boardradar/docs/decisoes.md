# Decisões da POC

## Persistência e arquitetura

Next.js com App Router, TypeScript e JSONs estáticos. Repositórios concentram acesso aos dados; serviços de domínio concentram recomendação e interpretação de mensagens. O processo web não altera JSONs. Preferências e favoritos são locais ao navegador. Não há conta, banco, Docker nem segredos de integração.

## Comparação e demonstração

Oferta pertence a uma única edição interna. API rejeita edição que não pertence ao jogo consultado. Não há regra de equivalência entre edições: compara-se apenas a mesma edição. Centavos inteiros; frete não computado. Ofertas disponíveis e observadas há no máximo sete dias precedem as demais. Timestamps futuros são inválidos. Não há URLs comerciais nos dados. A rota de saída sempre retorna 403.

## Recomendação

Filtros obrigatórios por nome, jogadores, tempo, estilo e orçamento precedem qualquer score. Sem oferta recente, o jogo não satisfaz orçamento. Pesos base: temas 25%, estilo 25%, afinidade com videogames 25%, complexidade 15% e qualidade editorial 10%, configurados em `src/data/policy.json`. O TypeScript mantém proximidade da complexidade escolhida; o Python preserva preferência por menor complexidade, teto explícito e bônus editoriais de combate. Os perfis estão documentados na entrega da Fase 2 e não são apresentados como um algoritmo único. Empate por nome. Pontuação não é porcentagem de certeza. Não há anúncios ou pagamento por posicionamento.

## Assistente Radar

Expansão de escopo solicitada: assistente conversacional em Python 3.13, sem LLM ou dependências externas. O recomendador do chat lê os mesmos JSONs do catálogo e aplica filtros obrigatórios antes do ranking. Reconhece franquias, sinônimos, combate, modo cooperativo/competitivo, negações, jogadores, orçamento e tempo; perguntas pendentes permitem respostas curtas. Recomendações explicam cada correspondência. Entradas desconhecidas não disparam sugestões aleatórias.

O contexto fica em memória da interface; o serviço é stateless e valida o estado recebido. `npm start` e `npm run dev` iniciam Next.js e Python com ciclo de vida compartilhado. O serviço Python usa somente loopback, porta alocada pelo sistema e token efêmero transmitido no ambiente dos subprocessos. O navegador consulta `/api/chat`, e o proxy Next.js aplica esquema, limite de mensagem e timeout. Conversas não são gravadas em disco nem enviadas a terceiros. Falha do serviço aparece na interface, sem fallback silencioso para o motor antigo. Alterações Python exigem reiniciar o comando; o recarregamento automático é apenas do Next.js.

## Catálogo editorial

Nomes e categorias fornecidos pelo cliente. Demais metadados são provisórios. Não foram copiadas descrições ou imagens de catálogos externos. Foram usadas capas abstratas próprias e uma representação vetorial aproximada da marca. Edições demonstrativas carecem de confirmação editorial, idioma, editora, SKU e direitos de uso antes de qualquer comparação real. Não publicar como catálogo verificado.

## Lojas e histórico

Dez nomes de lojas fictícias, sem domínio ou checkout. Quatro ofertas por jogo com oferta; The Witcher: Old World exemplifica ausência de preço. Histórico sintético por oferta por 61 dias. Origem e modo demo estão nos dados e na interface. Não são preços históricos reais.

## Próximas etapas

Conferência editorial das 60 fichas e dos produtos colecionáveis; validação visual em navegador; auditoria de acessibilidade; definição de carga para desempenho; fontes autorizadas, associação de produtos, autorização administrativa e persistência antes de produção. Migração para LLM requer fundamentação no catálogo e orçamento separado.
