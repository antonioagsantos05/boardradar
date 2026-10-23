# Contas e jogos pessoais

Atualização: a jornada agora apresenta explorar/vender, perfil opcional, wishlist, avisos e conversas. Veja o [guia consolidado dos fluxos do PDF](v2/FLUXOS_USUARIO_LOCAL.md), que prevalece sobre as descrições históricas de fases abaixo.

Acesse “Minha conta” no cabeçalho ou `/conta`. É possível criar uma conta com nome, e-mail e senha, entrar, sair e cadastrar, editar e remover jogos pessoais. Cada registro tem nome, categoria, número de jogadores, duração e observações.

Os dados persistem em `.local/accounts.sqlite3`, separado do índice derivado `.local/games.sqlite3`. O banco de contas não deve ser apagado ao reconstruir o catálogo. Para backup, pare o projeto e copie o arquivo de contas. O e-mail é um identificador local, sem verificação ou envio de mensagens. Não há recuperação de senha por e-mail nesta versão.

Senhas usam PBKDF2-SHA256 com salt aleatório e 600.000 iterações. A sessão dura até sete dias, usa token aleatório e armazena apenas seu hash no banco. O navegador recebe cookie HttpOnly e SameSite Strict; Secure é aplicado quando há HTTPS. Sair revoga a sessão atual. Escritas exigem origem igual à aplicação, validação e autorização pelo proprietário; autenticação tem limite local de tentativas. O transporte Python continua privado, em loopback, com token interno.

Jogos cadastrados ficam em “Meus jogos”, sem substituir os dados editoriais nem virar evidência para regras ou recomendações. O módulo separado **Meus anúncios** permite preparar rascunhos com edição, preço, condição e fotos e enviá-los à moderação; consulte o [plano do marketplace](v2/MARKETPLACE_FASES.md). A [fase 3](v2/MARKETPLACE_FASE_3.md) permite descoberta dos anúncios ativos e controles de disponibilidade. Fotos dos anúncios ativos têm leitura pública local; as demais continuam privadas. Preferências persistentes de recomendação também ainda não estão vinculadas à conta.

Para testes isolados é possível definir `RADAR_ACCOUNT_DB` com outro caminho antes de iniciar. O uso normal dispensa configuração.
