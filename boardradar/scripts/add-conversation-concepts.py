"""Add original editorial concepts; do not ingest third-party manuals."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/data/knowledge-chunks.json'
chunks=json.loads(path.read_text(encoding='utf-8'))
extras=[('chunk-worker-placement','Conceito: alocação de trabalhadores','Na alocação de trabalhadores, você distribui suas peças entre espaços de ação para obter recursos ou executar atividades. Quando os espaços são limitados, escolher uma ação também pode reduzir as opções dos outros participantes. As regras de ocupação dependem de cada jogo.'),
        ('chunk-drafting','Conceito: drafting','Drafting é escolher uma opção de um conjunto disponível, como uma carta ou um dado, antes que as outras pessoas façam suas escolhas. Em alguns jogos as cartas restantes são passadas ao próximo participante; em outros a oferta fica no centro da mesa.')]
for cid,section,text in extras:
    if not any(c['id']==cid for c in chunks):chunks.append({'id':cid,'source_id':'radar-editorial-2','game_id':None,'edition_id':None,'section':section,'page':None,'text':text})
path.write_text(json.dumps(chunks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
