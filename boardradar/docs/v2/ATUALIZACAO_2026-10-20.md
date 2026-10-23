# Atualização dos documentos e implementação local

Os DOCX atualizados estão preservados em `fontes/`. Seus adendos de 20/10/2026 são referências de produto, não evidência de funcionalidades já entregues. A orientação explícita do usuário mantém a execução local e prioriza IA e catálogo. Não foram ativados LLM, serviços pagos ou integrações externas.

## Implementado nesta atualização

- Índice SQLite local derivado de `src/data/library.json`, sem dependências Python adicionais. IDs BGG, campos desconhecidos e proveniência são preservados no registro original.
- Busca parametrizada por categoria/mecânica, jogadores, duração e complexidade BGG, com resultados limitados. Expansões identificadas ficam fora da descoberta; formato desconhecido permanece explicitamente incerto.
- O Radar atende pedidos como “Busque no catálogo jogos de fantasia para 4 pessoas até 90 minutos” e continua com “Qual deles dura menos?” ou “Qual deles é mais complexo?”.
- Restrições explícitas novas substituem valores anteriores. Orçamento sem ofertas e exclusões que a busca não verifica impedem resultados apresentados como compatíveis.
- Resultados da biblioteca continuam informativos, sem se passarem por recomendação editorial, manual oficial ou oferta.
- Relatório reproduzível de cobertura em `catalog-coverage.json`, ligado ao SHA-256 do snapshot.

## Reconstrução

Execute `python scripts/build-game-index.py` na raiz do projeto usando o Python disponível na máquina. O banco é `.local/games.sqlite3`, derivado e ignorado no versionamento. A geração valida a integridade e substitui o índice apenas após concluir. Reinicie o serviço após reconstruir.

Se o índice estiver ausente ou desatualizado, a busca usa um banco temporário em memória derivado do JSON atual; nunca continua silenciosamente usando dados antigos. Não há gravação de conversas nem perfis neste banco.

## Escopo dos documentos ainda planejado

PER-01/PER-02 completos dependem de onboarding, consentimento e persistência de preferências. A atualização posterior de [contas locais](../CONTAS_LOCAIS.md) acrescentou cadastro, login e jogos pessoais, mas não perfil histórico de recomendação. AI-01 foi ampliado na recuperação estruturada, mas não representa implementação integral da arquitetura-alvo com LLM.

COM-01/COM-02 exigem parceiros e fontes autorizadas; a POC segue DEMO e sem redirecionamento comercial. WIS-01/WIS-02, P2P-01/P2P-02, autenticação, notificações e métricas de vendas permanecem no backlog. Nada foi marcado como compra atribuída ou oferta real.

A cobertura importada não equivale a curadoria revisada. Não foram coletados novos fatos na internet nesta atualização. O relatório identifica lacunas para orientar a revisão posterior.
