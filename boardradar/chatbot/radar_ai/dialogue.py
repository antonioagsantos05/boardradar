"""Explicit short follow-ups, grounded in catalogue attributes and owned concepts."""
import re
from .catalog import DEFAULT_CATALOG
from .knowledge.index import load_index
from .knowledge.answers import answer_query
from .nlp.normalizer import normalize
from .nlp import apply_entities
from .recommendation import recommend
from .tools import compare_games,game_details

TOPICS={'chunk-deckbuilding':('deck-building',['g22','g30','g61','g65']),
        'chunk-coop':('cooperativo',[g['id'] for g in DEFAULT_CATALOG.games if 'cooperativo' in g['tags']]),
        'chunk-4x':('4X',['g43','g44','g52']),
        'chunk-worker-placement':('alocação de trabalhadores',['g19','g22','g24','g25','g30']),
        'chunk-drafting':('drafting',['g7','g13','g64'])}


def followup(message,state,parsed):
    if parsed.errors or parsed.ambiguities or parsed.intent in ('reset','commercial','rule','greeting','thanks'):return None
    text=normalize(message);topic=state.get('last_topic');e=parsed.entities
    def result(answer,**extra):return {'text':answer,'state':state,'recommendations':[],'suggestions':['Recomeçar'],**extra}
    if re.search(r'(?:tem|possui|voce tem).*(?:manual oficial)|qual edicao.*precisa',text):
        return result('A base atual não tem manuais oficiais autorizados. Preciso da identificação exata da sua edição e de um manual ou FAQ correspondente para conferir ações de jogo.',sources=[],answer_confidence='unknown')
    if topic:
        try:index=load_index();source=index.resolve(topic)
        except (OSError,ValueError):source=None
        if source and re.search(r'de onde|qual.*fonte|veio essa|fonte dessa',text):
            return result(f"Essa explicação vem de {source['title']}, seção {source['section']}, versão {source['version']}. É conteúdo editorial próprio, não um manual oficial de jogo.",sources=[source],answer_confidence='editorial_excerpt')
        if source and re.search(r'outra mecanica|outro conceito|mais uma mecanica',text):
            choices=['chunk-worker-placement','chunk-drafting','chunk-deckbuilding'];next_id=choices[(choices.index(topic)+1)%len(choices)] if topic in choices else choices[0]
            evidence=index.resolve(next_id)
            if evidence:
                state['last_topic']=next_id
                return result(evidence['excerpt'],sources=[evidence],answer_confidence='editorial_excerpt')
        if source and re.search(r'mais simples|simplifique|mais facil de entender',text):
            simple={'chunk-deckbuilding':'Você começa com algumas cartas e melhora seu baralho enquanto joga. As cartas novas ajudam a fazer jogadas melhores nas próximas rodadas.',
                    'chunk-coop':'Os participantes jogam no mesmo time e tentam alcançar um objetivo em conjunto. As condições exatas dependem do jogo.',
                    'chunk-4x':'É uma categoria de jogos sobre explorar, expandir, usar recursos e disputar espaço. Cada jogo dá mais importância a uma parte dessa experiência.'}
            return result(simple.get(topic,source['excerpt']),sources=[source],answer_confidence='editorial_excerpt')
        if source and re.search(r'isso.*(?:combate|luta)|significa.*combate',text):
            return result('A etiqueta 4X envolve exploração, expansão, uso de recursos e disputa, mas não informa sozinha como o combate funciona ou quanto ele pesa na partida. Para comparar isso precisamos olhar o jogo específico.',sources=[source],answer_confidence='editorial_excerpt') if topic=='chunk-4x' else result('Esse conceito, sozinho, não confirma que um jogo tenha combate. Diga o nome do jogo para eu verificar os atributos cadastrados.',sources=[source])
        if source and topic=='chunk-deckbuilding' and re.search(r'colecionaveis|colecionavel',text):
            return result(source['excerpt'],sources=[source],answer_confidence='editorial_excerpt')
        if topic in TOPICS and re.search(r'exemplo|jogo com essa|jogo com isso|outro mais barato',text):
            ranked=recommend(state,'barato' in text,candidate_ids=TOPICS[topic][1])
            if 'outro' in text:ranked=[r for r in ranked if r['id'] not in state['last_ids']]
            cards=ranked[:3]
            if not cards:return result('Não encontrei outro exemplo desse conceito que atenda aos seus filtros e tenha os dados necessários. Podemos ajustar o orçamento, o tempo ou os jogadores.')
            state['last_ids']=[c['id'] for c in cards];state['subject_ids']=state['last_ids'][:1]
            return result('Estes são exemplos de '+TOPICS[topic][0]+' compatíveis com as condições informadas.',recommendations=cards)
    ids=state.get('subject_ids',[])
    games=[g for gid in ids for g in DEFAULT_CATALOG.games if g['id']==gid]
    if games and e.players and re.search(r'aceita|suporta|funciona',text) and not e.game_ids:
        g=games[0];fits=g['players']['min']<=e.players<=g['players']['max']
        return result(f"{g['name']} {'aceita' if fits else 'não atende a'} {e.players} pessoas pelos dados cadastrados: a faixa é de {g['players']['min']} a {g['players']['max']}. Esses metadados ainda precisam de confirmação da edição.")
    if len(games)>=2:
        if re.search(r'troque|substitua',text) and len(e.game_ids)==2:
            old,new=e.game_ids
            if old in ids and new not in ids:
                state['subject_ids']=[new if i==old else i for i in ids]
                games=[next(g for g in DEFAULT_CATALOG.games if g['id']==gid) for gid in state['subject_ids']]
                return result('Atualizei a comparação com os jogos pedidos.',comparison=compare_games(games,state),game_details=game_details(games,state))
        field='duration' if re.search(r'rapido|dura menos|menos tempo',text) else 'complexity' if re.search(r'complexo|complexidade|iniciantes',text) else None
        if field and not e.game_ids:
            low=bool(field=='duration' or 'menos' in text or 'iniciante' in text)
            chosen=(min if low else max)(games,key=lambda g:g[field])
            values='; '.join(f"{g['name']}: {g[field]}{' min' if field=='duration' else '/5'}" for g in games)
            return result(values+f". {chosen['name']} tem o {'menor' if low else 'maior'} valor cadastrado. "+('Complexidade é uma estimativa editorial; a curva de aprendizado não foi medida.' if field=='complexity' else 'O tempo depende do grupo e da edição.'))
        if not e.game_ids and any(v is not None for v in (e.players,e.duration_minutes,e.max_price_cents)):
            state.update(apply_entities(state,parsed))
            return result('Mantive os dois jogos e atualizei a compatibilidade com suas condições.',comparison=compare_games(games,state),game_details=game_details(games,state))
    return None
