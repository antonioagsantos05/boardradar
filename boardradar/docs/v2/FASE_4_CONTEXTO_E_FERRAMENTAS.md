# Fase 4 — contexto e ferramentas

O Radar mantém preferências entre turnos, consulta atributos do catálogo, compara até três jogos e apresenta edições e ofertas DEMO dentro da conversa. A implementação continua determinística, sem LLM ou serviços de inferência.

## Comportamento entregue

- `4 pessoas` → `até 250 reais` → `prefiro estratégia` preserva os três critérios. Correções e remoções continuam usando o interpretador da fase 3.
- `Compare Root` pergunta pelo segundo jogo; `Scythe` completa a comparação. Uma consulta explícita diferente substitui a consulta pendente. `Cancelar` mantém as preferências e encerra o esclarecimento.
- `Fale sobre Root` → `ofertas dele` mantém o assunto. Comparações também permitem `edições deles` e `ofertas deles`.
- A tabela usa jogadores, duração, complexidade, categoria e etiquetas cadastrados. Interação, variabilidade, curva de aprendizado e estratégia detalhada aparecem como **Não cadastrado**. Os metadados continuam preliminares.
- As edições são os registros existentes, sem criar traduções, SKUs ou equivalências. Ofertas são agrupadas por edição, com loja fictícia, preço, condição e data; o frete não é conhecido nem somado. `Ofertas g1-pt-base` seleciona exatamente esse produto.
- Apenas ofertas que passam pela política compartilhada de integridade, BRL, centavos inteiros, DEMO, disponibilidade e validade são exibidas. Preços acima do orçamento recebem uma indicação; consultar preços não transforma o jogo em recomendação elegível. O endpoint comercial permanece bloqueado.
- Filmes e séries usam exclusivamente as relações editoriais locais: por exemplo, `Gosto do filme Duna` ou `Gosto da série The Witcher`. Referências de videogames preservam seu ranking anterior e recebem as relações editoriais correspondentes quando cadastradas. As relações identificam temática/mecânica e revisão pendente. Afinidade não comprova adaptação oficial ou regras equivalentes.

As referências de entretenimento restringem candidatos; filtros obrigatórios continuam sendo aplicados antes do ranking. Não foram criados bônus numéricos novos. Pesos editoriais cadastrados não são probabilidades de satisfação. Uma preferência temática ou de videogame posterior substitui a referência de filme/série.

## Contexto e limite de confiança

O campo `state.session` contém `version`, `issued_at` e `expires_at`, em segundos UTC. A duração absoluta é de 1.800 segundos; novos turnos não prolongam o prazo. Prazo inválido é rejeitado. Contexto expirado ou com emissão futura é descartado, e a resposta solicita reconstrução sem aplicar silenciosamente a nova mensagem às preferências antigas.

Preferências, assunto, edição selecionada e esclarecimento pendente viajam no JSON. Não existe tabela global de sessões, histórico em disco ou perfil pessoal. O mesmo JSON funciona em outro processo. O estado inicial legado sem sessão continua aceito para compatibilidade e recebe um prazo no primeiro retorno.

Esse envelope **não é assinado** e não autentica pessoas: o cliente pode editar suas preferências e iniciar outra conversa. Os limites temporais validam o envelope, não impedem sua recriação por um cliente. Nenhum campo recebido autoriza compras, altera a política DEMO ou substitui a validação do catálogo. Autenticação e persistência de perfis não fazem parte desta entrega.

A interface mantém reset com cancelamento da requisição em andamento, proteção contra respostas atrasadas e timeout. O contexto não é gravado em localStorage. A infraestrutura HTTP permanece local; estado portátil não significa hospedagem serverless validada.

## Arquivos principais

- `chatbot/radar_ai/conversation.py`: orquestração e continuidade.
- `session.py`, `state.py`: prazo e validação do envelope.
- `tools.py`: consulta estruturada, comparação, edições e ofertas.
- `media.py`: referências editoriais e integridade das relações.
- `templates.py`: respostas parametrizadas.
- `src/app/api/chat/route.ts`: contrato ampliado com validação estrita.
- `src/components/ChatAssistant.tsx`: tabela, edições, ofertas e justificativas editoriais.
- `chatbot/test_phase4.py`, `scripts/smoke.mjs`, `scripts/check-chat-browser.mjs`: cenários de aceite e regressão.

Política `2.0-phase4.0`; perfil de ranking `1.1-preserved`. Os relatórios anteriores são históricos e não são sobrescritos.

## Verificação reproduzível

```powershell
..\.tools\python-3.13.7\python.exe scripts/verify-phase4.py --browser
```

O comando valida dados, executa testes TypeScript/Python, verifica tipos, compila e testa HTTP e navegador. Resultados, contagem real de testes, logs e hashes ficam em `docs/v2/phase4/summary.json`. Capturas visuais ficam em `.qa/`. Chrome é necessário para a opção `--browser`.

## Próximas fases

A fase 5 implementará recuperação documental e evidências locais. Esta fase continua recusando respostas sobre regras sem documentação suficiente. Os trechos editoriais existentes não são manuais oficiais. A fase 6 tratará avaliação de latência, adaptador serverless e preparação de hospedagem; não há deploy publicado por esta entrega.
