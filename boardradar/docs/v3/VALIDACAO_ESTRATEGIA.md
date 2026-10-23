# Validação do projeto contra a estratégia v3.0

Data: 21/10/2026. Referência: `BoardRadar_Estrategia_Negocio_Produto_v3.0.docx` fornecido pelo usuário. O documento foi analisado como especificação de destino; suas afirmações sobre implementação não foram tomadas como evidência do sistema atual.

## Resultado da redução do catálogo

O catálogo público anterior reunia 182.259 registros: rankings de 2026 e 1.000 fichas históricas. Foi substituído pelos **100 jogos dos 11 JSONs fornecidos**. As fontes ficam em `data/`, preservadas byte a byte, com hashes em `source-hashes.json`.

| Entidade | Previsto | Validado |
| --- | ---: | ---: |
| Jogos | 100 | 100 |
| Edições | 124 | 124 |
| Lojas fictícias | 10 | 10 |
| Ofertas de lojas | 300 | 300 |
| Anúncios simulados | 100 | 100 |
| Vendedores fictícios | 100 | 100 |
| Temas | 61 | 61 |
| Experiências | 27 | 27 |
| Franquias | 30 | 30 |

Os adaptadores TypeScript/Python calculam as estruturas de compatibilidade em memória. Não existe outro catálogo ativo, histórico de preços artificial ou enriquecimento com a base anterior. `src/config/policy.json` contém configuração do algoritmo, não fatos adicionais de jogos. Os arquivos antigos foram retirados de `src/data` e preservados em `.local/retired-src-data-v3`; existe também a cópia inicial `.local/catalog-before-v3-20261021`. Esses diretórios locais não entram no build nem são fontes das rotas públicas.

## Comparação com o produto proposto

| Requisito | Situação após esta alteração |
| --- | --- |
| Catálogo limitado aos JSONs, filtros, ficha e comparação | Implementado para os 100 jogos. Identidades `game_…` e `bgg-…` apontam para o mesmo registro. Links para jogos retirados deixam de resolver. |
| 300 ofertas e 100 anúncios diferenciados e fictícios | Implementado nas rotas públicas e fichas. Preços, edição e condição são apresentados com aviso de simulação; frete não é presumido. |
| Radar sem IA externa, até três jogos e “mostrar mais” | Motor determinístico usa os novos arquivos; paginação da conversa evita repetir os primeiros jogos. |
| Orçamento, jogadores, duração, complexidade, temas e franquias | Filtros e afinidades usam apenas os atributos fornecidos. Afinidade com franquia é editorial e não comprova licença. O reconhecimento de linguagem livre é limitado aos padrões implementados. |
| Rejeições explícitas | Temas reconhecidos em expressões como “não gosto de terror” são excluídos e preservados na continuidade. Isso não representa cobertura irrestrita de português natural. |
| Catálogo e marketplace sem Python | Verificado com executável Python inexistente: navegação pública funciona; chat retorna indisponibilidade. |
| Perfil, cadastro e anúncios em localStorage | **Pendente.** A implementação anterior de contas e gestão privada ainda usa Python e SQLite; não foi convertida nesta migração de catálogo. |
| Pelo menos uma preferência no fluxo demonstrativo | **Pendente** no cadastro/perfil antigo. O arquivo `perfil_exemplo.json` é referência, não é aplicado automaticamente ao usuário. |
| Confirmar preferências do chat antes de salvar no perfil | O novo motor mantém contexto temporário e não salva preferências no perfil. A experiência de confirmação ainda não foi implementada. |
| Publicação imediata, edição “Outra / Não sei”, exemplar distinto, 1–8 fotos | **Pendente** na gestão antiga, que ainda tem rascunhos/revisão e limite de seis fotos. |
| Contato apenas demonstrativo | Implementado para os 100 anúncios importados: botão informa a simulação e não envia mensagem. Fluxos antigos de mensagens e moderação continuam presentes em outras rotas. |
| Custo operacional zero e publicação gratuita | Não validado. Nenhum serviço foi contratado ou publicado nesta tarefa. |

**Conclusão:** a base pública de catálogo e comércio simulado foi reduzida ao escopo v3. A aplicação completa ainda não cumpre toda a estratégia. Em particular, “apenas os JSONs” descreve as fontes do catálogo; a persistência privada antiga em SQLite continua existindo, preservada sem apagar contas, sessões ou registros do usuário.

## Ressalvas encontradas nos arquivos

- Os 100 anúncios têm `imagens_anuncio` vazio. A imagem de referência do jogo não é uma foto do exemplar. Não foram fabricadas fotos para preencher esse requisito.
- As 124 edições são simuladas e não verificadas. Os tipos `premium`, `importada` e `colecionador` são variantes comerciais da POC, não expansões verificadas.
- Os 100 resumos estão em `descricao_pt`, mas `status_traducao_descricao` continua `pendente`. O aviso de tradução em `metadata.json` também menciona textos ingleses preservados, enquanto a nota de descrições diz que foram removidos. As fontes foram preservadas e essa inconsistência foi registrada.
- Notas BGG e complexidade são de 2019. `ordem_original` não é ranking atual; as telas não apresentam ranking de 2026.
- URLs de imagens não foram verificadas remotamente. O fallback visual existente continua necessário.

## Verificação reproduzível

`npm run validate-data` verifica hashes, contagens, unicidade, referências, escala de complexidade, preços positivos e vínculos jogo/edição.

`npm run test:v3` executa essa validação, testes dos adaptadores TypeScript e testes Python do novo catálogo/Radar. `npm run typecheck` e `npm run build` verificam compilação e rotas.

Após o build, `node scripts/smoke-v3.mjs` verifica catálogo, filtros, ficha, ofertas, anúncio público e chat. `node scripts/smoke-v3.mjs --without-python` repete a navegação com Python indisponível.

A suíte histórica `npm test` e scripts de auditoria v2 ainda contêm expectativas sobre IDs antigos, volumes antigos, fontes retiradas e fluxos SQLite. Não foram declarados aprovados para v3. A atualização completa dessa suíte acompanha a futura conversão dos fluxos privados; os testes v3 são identificados separadamente.
