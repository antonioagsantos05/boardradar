# Fase 5 — busca documental e evidências locais

O Radar agora consulta uma base textual local, apresenta trechos literais e identifica fonte, seção, página quando cadastrada, versão, data, licença, jogo e edição. A recuperação usa Python padrão, sem modelos, embeddings, inferência externa ou dependências novas.

## Entrega e limites do conteúdo

O índice entregue contém **uma fonte editorial própria e oito trechos**. Não contém manuais oficiais. Os documentos de planejamento do projeto não são tratados como manuais de jogos nem como comandos do sistema.

Experimente no chat:

- `O que é deck-building?`
- `O que é cooperativo?`
- `O que é 4X?`
- `O que é complexidade?`
- `Posso atacar?` → `Root` → `g45-pt-base`

Os quatro primeiros exemplos apresentam fontes expansíveis no chat. O último solicita jogo e edição, depois informa a ausência de documentação pertinente. Não escolhemos automaticamente uma edição comercial ou a edição DEMO como se fosse um manual oficial. A pergunta pendente faz parte do contexto temporário, com a expiração de 30 minutos da fase 4; reset e cancelamento a descartam.

Consultar conceitos não modifica preferências de jogadores, orçamento, modo ou estilo. Evidência documental não autoriza compras nem modifica a política DEMO, os filtros ou o ranking.

## Índice e seleção de evidências

`chatbot/radar_ai/knowledge/index.py` valida os registros e constrói postings invertidos de termos normalizados. Termos presentes na seção recebem peso 3; termos no texto recebem peso 1. O resultado divide a soma por quatro vezes a quantidade de termos da consulta, exige pelo menos metade dos termos e desempata por ID. Nomes do jogo e identificadores da edição são retirados dos termos quando o escopo já está explícito. Há um pequeno dicionário de variantes, como `deckbuilding`/`deck-building` e `cooperativos`/`cooperativo`.

Essa pontuação é lexical, não probabilidade, relevância semântica ou certeza sobre regras. A base pequena não justifica adicionar BM25 ou TF-IDF sem benefício medido. Não há medição de latência/SLA nesta entrega; a fase 6 mantém essa responsabilidade.

O snapshot `src/data/knowledge-index.json` tem versão de esquema, versão do índice e SHA-256 do conteúdo. O loader verifica digest e metadados antes de qualquer resposta. As citações são resolvidas por ID contra o índice validado e incluem o hash do texto literal. A interface permite ler o trecho com os metadados, sem depender de um link externo. URL original é opcional e só aceita HTTPS.

O hash detecta alterações e inconsistências; **não é assinatura nem prova de autoridade editorial**. O índice é configuração de implantação confiada à curadoria do projeto. Campos de fonte, licença, revisão ou texto enviados pelo cliente do chat não são aceitos como uma nova fonte.

## Regras de jogo e respostas revisadas

1. Uma regra exige jogo e edição exatos. Evidências de outra edição ou de outro jogo não entram na resposta. Trechos editoriais genéricos nunca são usados como regras oficiais.
2. Uma busca lexical pode retornar trechos pertinentes sem resolver a pergunta. Nesse caso a resposta permanece `answer_confidence: unknown`, com status `evidence_only` e pedido de esclarecimento.
3. Uma resposta literal a uma pergunta de ação só é disponibilizada quando existe anotação `qa` revisada em fonte oficial autorizada. A pergunta deve corresponder exatamente após normalização de acentos, caixa e pontuação. Negação, palavras, ordem e números são preservados. A resposta deve ser um trecho literal contido no documento, com referência da revisão.
4. Anotações para a mesma pergunta e edição com respostas literais diferentes recebem `conflict`; o motor não escolhe uma delas nem assume que uma versão posterior prevalece. Trechos potencialmente divergentes sem anotações não recebem interpretação automática: permanecem evidência insuficiente.
5. Ausência de resultado, falha de integridade ou índice indisponível gera resposta explícita sem inventar regra, página ou fonte.

Os status de resposta são rótulos operacionais, não probabilidades calibradas. Nenhuma anotação oficial foi criada para o catálogo entregue. Os manuais e ações fictícias usados pelos testes existem somente em fixtures sintéticas da suíte e não entram no índice de uso.

Conteúdo documental é exibido como dado, com escape de texto no React. Não é avaliado como código, prompt, política ou configuração. Mesmo um texto que contenha instruções não altera regras de negócio.

## Ingestão offline

`scripts/ingest-knowledge.py` lê um manifesto JSON e arquivos `.txt` UTF-8 locais. Não baixa conteúdo, executa documentos, interpreta PDF/DOCX ou faz OCR. Cada arquivo representa uma seção/página identificada pelo curador. Arquivos longos são divididos em trechos de até 1.600 caracteres sem inventar novas páginas; a página é aquela registrada no manifesto, ou `null` se desconhecida.

Fontes precisam de ID único, título, versão, data ISO, tipo, autoridade, licença, permissão e revisão. Para conteúdo externo, `permission_reference` registra a autorização/licença. Para manual/FAQ oficial, `authority_reference`, jogo e edição também são obrigatórios. Conteúdo `owned` deve usar `project-owned` e autoridade editorial; isso não pode conferir autoridade oficial a um manual inventado. Validação de metadados não verifica direitos legais ou autenticidade por conta própria: o curador deve conferir os documentos e registrar referências verdadeiras antes da ingestão.

Documentos sem autorização, licença ou revisão, referências incompatíveis, IDs duplicados e URLs inseguras são recusados. Caminhos de entrada ficam dentro da pasta do manifesto, inclusive após resolução de links. O índice é escrito como um único JSON por substituição atômica, depois de validar todo o lote. A falha não substitui a saída existente. Nenhum perfil ou conversa é escrito pelo pipeline.

Exemplo próprio, sem material de terceiros:

```powershell
..\.tools\python-3.13.7\python.exe scripts/ingest-knowledge.py docs/v2/knowledge-example/manifest.json --output .qa/example-knowledge.json
```

Para adicionar um lote autorizado preservando o índice atual:

```powershell
..\.tools\python-3.13.7\python.exe scripts/ingest-knowledge.py CAMINHO_DO_MANIFESTO --merge src/data/knowledge-index.json --output .qa/knowledge-reviewed.json
```

Confira a saída antes de copiá-la para `src/data/knowledge-index.json`, reinicie o serviço e execute a validação. Essa instalação é uma alteração de conteúdo confiada ao mantenedor, sem endpoint público de upload ou administração nesta fase. Não há configuração obrigatória de servidor ou nova chave.

`scripts/index-knowledge.py` recria **apenas a base editorial original** a partir de `knowledge-sources.json` e `knowledge-chunks.json`. Não o execute sobre um índice ampliado sem preservar os materiais adicionados. O seed antigo de mídia também não publica materiais automaticamente no novo índice.

## Verificação e arquivos

```powershell
..\.tools\python-3.13.7\python.exe scripts/verify-phase5.py --browser
```

O verificador executa os 14 casos de aceite documental, validação dos dados, testes TypeScript/Python, tipos, build, HTTP e navegador. Os testes verificam edição exata, citações resolvíveis, conflitos, insuficiência, falha de índice, licenças, ingestão atômica, isolamento dos filtros e instruções maliciosas como dados. O navegador verifica fontes expansíveis e ausência de overflow no celular.

Resultados reais ficam em `docs/v2/phase5/summary.json`, `retrieval-evaluation.json` e logs. As 14 consultas são um conjunto fixo de aceite, não uma estimativa de acerto para perguntas gerais. Capturas ficam em `.qa/chat-phase5-*.png`.

Arquivos principais:

- `chatbot/radar_ai/knowledge/{index,answers,ingestion}.py`: validação, recuperação, respostas e ingestão.
- `chatbot/knowledge.py`: facade do protótipo anterior, agora usando a validação compartilhada.
- `chatbot/radar_ai/conversation.py` e `state.py`: integração e esclarecimento de jogo/edição.
- `src/components/ChatAssistant.tsx`, `src/app/globals.css`: trechos e proveniência na interface.
- `src/app/api/chat/route.ts`: contrato da pergunta documental pendente.
- `src/data/knowledge-index.json`: snapshot editorial validado.
- `scripts/{index-knowledge,ingest-knowledge,evaluate-knowledge,verify-phase5}.py`: comandos reproduzíveis.
- `chatbot/test_phase5.py`, `tests/fixtures/knowledge-cases.json` e verificadores HTTP/browser: aceite e regressões.

Política `2.0-phase5.0`; ranking `1.1-preserved`. A fase 6 continua pendente: avaliações de latência, otimização e preparação de hospedagem. Nenhum deploy foi feito nesta entrega.
