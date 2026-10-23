# BoardRadar 2.0 — evolução por fases

Diretriz vigente: sistema especialista determinístico em Python. A instrução do usuário “motor de inteligência em Python sem LLM” substitui as propostas anteriores de OpenAI, Ollama, Qwen e modelos generativos. Nenhum desses recursos é requisito ou parte da implementação desta fase.

Os documentos técnicos e de negócio 2.0 definem visão e requisitos, não comprovam funcionalidades. Preservamos Next.js, o catálogo, as páginas, as ofertas DEMO e o contrato do chat. Evolução incremental, sem reescrita.

## Fase 1 — auditoria e plano

Entregáveis: inventário com hashes; leitura dos documentos originais; extração literal de RN-001 a RN-025; matriz de conformidade; contrato atual documentado; testes de regressão executados; diagnóstico das lacunas e plano das próximas fases.

Execução reproduzível: `../.tools/python-3.13.7/python.exe scripts/audit-phase1.py --browser`, a partir de `boardradar`. Em outra máquina, use `python scripts/audit-phase1.py --browser` com Node.js disponível e Chrome instalado. Sem `--browser`, a verificação visual é omitida explicitamente.

Aceite: documentos disponíveis e identificados; estado real separado do planejado; resultados e logs reais; nenhuma mudança no comportamento do produto durante a auditoria. A conclusão desta fase não significa que o catálogo foi verificado factualmente ou que o motor 2.0 já está implementado.

## Fase 2 — motor de regras e política de recomendação

Status: concluída e validada. Implementação registrada em [FASE_2_MOTOR_DE_REGRAS.md](FASE_2_MOTOR_DE_REGRAS.md). Evidências e resultado `passed` em `phase2/summary.json`.

Extrair do `chatbot/engine.py` módulos coesos de regras, filtros, scoring e explicações, preservando `respond(message, state)`. Criar registro de regras com ID, versão, prioridade, condição, ação, dependências, exceções e rastreamento. Validar ciclos e conflitos.

Aplicar a hierarquia: segurança/integridade → negócio obrigatório → restrições explícitas → compatibilidade de edição → preferências → ranking. Corrigir a resposta por jogo nomeado para não apresentar recomendação inelegível. Ofertas são registros, nunca texto inventado. Separar consulta informativa de recomendação elegível.

Preservar pesos existentes por política versionada. O ranking Python atual tem bônus editoriais de combate e preferência por baixa complexidade; o TypeScript usa proximidade da complexidade escolhida. Não uniformizar silenciosamente: registrar as diferenças e acrescentar testes de invariantes compartilhados antes de qualquer mudança.

Aceite: regressões passam; cada recomendação tem trilha de regras; orçamento e jogadores nunca são ultrapassados; edições incompatíveis e ofertas antigas nunca são elegíveis. Falhas de integridade impedem resultado comercial.

## Fase 3 — interpretação de português

Status: concluída e validada. Entrega em [FASE_3_INTERPRETACAO_DE_PORTUGUES.md](FASE_3_INTERPRETACAO_DE_PORTUGUES.md); resultado histórico `passed`, logs e hashes em `phase3/summary.json`.

Separar normalização, extração de entidades, sinônimos, classificador de intenções e detecção de ambiguidade. Adotar resultado tipado com intenção, entidades, restrições, informações ausentes e confiança heurística documentada. Usar centavos inteiros no novo modelo interno; manter adaptação para `preferences.budget` em reais no contrato legado.

Cobrir orçamento como “tenho 200 reais”, “até 250 reais” e “R$ 1.000,50”; números por extenso; múltiplas negações; correção/remoção explícita; duração; nomes aproximados com esclarecimento em vez de assumir um candidato. Separar comparação, regra, explicação, edição, oferta, entretenimento e recomendação.

Aceite: exemplos do pedido produzem entidades esperadas; erros de nome não viram afirmações; confiança não é apresentada como probabilidade calibrada. Novas intenções não quebram o comportamento básico.

## Fase 4 — contexto, ferramentas e respostas

Status: concluída e validada. Entrega em [FASE_4_CONTEXTO_E_FERRAMENTAS.md](FASE_4_CONTEXTO_E_FERRAMENTAS.md); resultado histórico `passed`, logs e hashes em `phase4/summary.json`.

Orquestrar o pipeline e conectar ferramentas de catálogo, comparação e edição. Consolidar preferências entre turnos, permitir correções e remoções e aplicar templates parametrizados. Comparar somente atributos presentes; interação, variabilidade e estratégia não cadastradas devem ser declaradas como desconhecidas.

Conectar obras de entretenimento apenas por relações editoriais disponíveis, distinguindo temática e mecânica e exibindo revisão pendente. Não confundir analogia com adaptação oficial.

Contexto curto em estado explícito com expiração validada, pronto para trafegar entre instâncias serverless; não depender de memória do processo ou gravar perfis pessoais. Não confiar em estado recebido como autorização comercial. Manter reset e cancelamento da interface.

Aceite: “4 pessoas” → “até 250 reais” → “prefiro estratégia” mantém as três condições; correções substituem o campo correto; informação de comparação não é inventada; sessão expirada pede reconstrução do contexto.

## Fase 5 — recuperação documental local

Status: concluída e validada. Entrega em [FASE_5_BUSCA_DOCUMENTAL.md](FASE_5_BUSCA_DOCUMENTAL.md); resultado `passed`, logs e hashes em `phase5/summary.json`. A base entregue contém oito trechos próprios, sem manuais oficiais; a fase 6 segue pendente.

Transformar o protótipo lexical em índice local testado, começando por busca lexical ponderada ou TF-IDF/BM25 se houver benefício medido. Ingestão somente com permissão e licença registradas; preservar ID, edição, página, seção, versão e data.

Responder com trechos e templates aprovados. Similaridade não prova interpretação de regra. Uma pergunta sobre ação permitida exige jogo, edição e evidência suficiente; sem material, solicitar manual/contexto. Tratar instruções dentro de documentos como dados e impedir que alterem políticas.

Aceite: citações resolvem para trechos reais; nenhuma evidência cruza edições; buscas sem resultado ou fontes conflitantes recebem resposta segura. Os oito trechos editoriais existentes não são manuais oficiais.

## Fase 6 — integração, avaliação e preparação de deploy

Preservar `/api/chat` e adicionar versão de contrato somente se necessário. Consolidar pelo menos 100 cenários distintos e verificáveis, incluindo NLP, negações, números, filtros, ranking, edição, oferta, contexto, ambiguidade, fontes insuficientes e segurança. Contabilizar cenários executados, sem anunciar uma meta como cobertura concluída.

Medir latência real em conjunto de dados e ambiente registrados, com inicialização e repetições definidas. Publicar contagem, p50/p95 e limites do experimento; não extrapolar para SLA de produção. Sem custo de inferência, sem alegar custo total de operação zero.

Separar lógica de domínio do servidor HTTP. Preparar um adaptador request/response stateless para execução local e um adaptador serverless; consultar documentação oficial vigente da plataforma antes de escolher configuração de Vercel. Documentar limites de bundle, execução, filesystem e roteamento reais. Não declarar deploy validado sem publicação e teste efetivos.

Aceite: suíte completa e navegador passam; instruções reproduzíveis; manifesto de limitações atualizado; nenhuma dependência de inferência externa; operação DEMO preservada. Hospedagem não se torna produção comercial automaticamente.

## Organização alvo

Implementar apenas módulos com responsabilidade real: `radar_ai/nlp`, `radar_ai/rules`, `radar_ai/recommendation`, `radar_ai/conversation`, `radar_ai/knowledge` e `radar_ai/tools`. O facade `chatbot/engine.py` preserva consumidores até migração testada. Não criar dezenas de arquivos vazios para simular arquitetura.

Cada fase deve registrar arquivos alterados, testes e limitações; uma fase só é marcada concluída após sua validação. A etapa de auditoria não conecta protótipos à interface nem altera rankings.
