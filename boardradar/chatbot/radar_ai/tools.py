"""Read-only specialist tools. All eligible prices pass the shared offer policy."""
from .catalog import DEFAULT_CATALOG
from .offers import select_offers
from .policies import budget_to_cents
from .recommendation import evaluate_game

UNKNOWN = 'Não cadastrado'


def game_details(games, state, *, catalog=None, now=None):
    catalog = catalog or DEFAULT_CATALOG
    rows = []
    for game in games:
        _, decision = evaluate_game(game,state,catalog=catalog,now=now)
        rows.append({k:game[k] for k in ('id','name','description','players','duration','complexity')} |
                    {'kind':'information','eligible_for_preferences':decision.eligible,'rejections':decision.rejections})
    return rows


def compare_games(games, state, *, catalog=None, now=None):
    details = game_details(games,state,catalog=catalog,now=now)
    attributes = [
        ('Jogadores',[f"{g['players']['min']}–{g['players']['max']}" for g in games]),
        ('Duração (min)',[g['duration'] for g in games]),
        ('Complexidade (1–5)',[g['complexity'] for g in games]),
        ('Categoria',[g['category'] for g in games]),
        ('Temas e etiquetas',[', '.join(g['tags']) for g in games]),
        ('Compatível com a busca',['Sim' if d['eligible_for_preferences'] else 'Não' for d in details]),
    ]
    for field in ('Interação','Variabilidade','Curva de aprendizado','Estratégia detalhada'):
        attributes.append((field,[UNKNOWN for _ in games]))
    return {'games':[{'id':g['id'],'name':g['name']} for g in games],
            'rows':[{'attribute':a,'values':v} for a,v in attributes],
            'provenance':[g.get('provenance',{}) for g in games],'metadata_status':'pending_verification'}


def editions_for(games):
    return [{'game_id':g['id'],'game_name':g['name'],'editions':g['editions'],
             'metadata_status':'pending_verification'} for g in games]


def offers_for(games, state, edition_ids=None, *, catalog=None, now=None):
    catalog = catalog or DEFAULT_CATALOG
    budget = state['preferences'].get('budget')
    ceiling = budget_to_cents(budget) if budget is not None else None
    rows = []
    for g in games:
        for edition in g['editions']:
            if edition_ids and edition['id'] not in edition_ids:continue
            _, decision = evaluate_game(g,state,catalog=catalog,now=now,edition_id=edition['id'])
            offers = select_offers(g,edition['id'],catalog=catalog,now=now)
            rows.append({'game_id':g['id'],'game_name':g['name'],'edition_id':edition['id'],
                         'edition_name':edition['name'],'language':edition.get('language',UNKNOWN),
                         'metadata_status':'pending_verification','is_demo':True,'shipping_included':False,
                         'eligible_for_preferences':decision.eligible,
                         'offers':[{'id':o['id'],'price_cents':o['price_cents'],'currency':'BRL',
                                    'checked_at':o['checked_at'],'condition':o.get('condition',UNKNOWN),
                                    'store_name':next(s['name'] for s in catalog.stores if s['id']==o['store_id']),
                                    'within_budget':ceiling is None or o['price_cents']<=ceiling}
                                   for o in offers]})
    return rows
