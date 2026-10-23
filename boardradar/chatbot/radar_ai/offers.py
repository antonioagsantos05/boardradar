"""Fail-closed offer selection for exactly one edition and one game."""
from .catalog import DEFAULT_CATALOG
from .policies import POLICY,is_fresh,validate_policy
from .rules import Layer,Rule,RuleEngine,reject

OFFER_ENGINE=RuleEngine([
    Rule('SEC-OFFER-001','1.0',Layer.SECURITY,10,lambda c,d:type(c['offer'].get('price_cents'))!=int or not 0<c['offer']['price_cents']<=9007199254740991 or c['offer'].get('currency')!='BRL',reject('invalid_money'),description='Preço positivo em centavos inteiros seguros no contrato JSON e moeda BRL.'),
    Rule('RN-024-OFFER','1.0',Layer.BUSINESS,10,lambda c,d:c['offer'].get('is_demo') is not True or c['store'].get('is_demo') is not True,reject('non_demo_data'),depends_on=('SEC-OFFER-001',),description='Somente registros demonstrativos nesta POC.'),
    Rule('RN-007-OFFER','1.0',Layer.BUSINESS,20,lambda c,d:not is_fresh(c['offer'].get('checked_at'),c['now'],c['policy']),reject('stale_or_invalid_timestamp'),depends_on=('SEC-OFFER-001',),description='Oferta válida por sete dias; datas futuras/sem timezone são recusadas.'),
    Rule('RN-008-STOCK','1.0',Layer.BUSINESS,30,lambda c,d:c['offer'].get('availability')!='in_stock',reject('unavailable'),depends_on=('SEC-OFFER-001',),description='Oferta indisponível não é elegível.'),
    Rule('RN-005-OFFER','1.0',Layer.COMPATIBILITY,10,lambda c,d:c['offer'].get('edition_id')!=c['edition_id'] or not any(e['id']==c['edition_id'] for e in c['game']['editions']),reject('edition_mismatch'),depends_on=('SEC-OFFER-001',),description='Não agregar edições diferentes nem comparar produto de outro jogo.'),
])


def select_offers(game,edition_id=None,*,catalog=None,now=None,integrity_errors=None,policy=None):
    catalog=catalog or DEFAULT_CATALOG;policy=validate_policy(policy or POLICY)
    integrity_errors=catalog.integrity_errors() if integrity_errors is None else integrity_errors
    if integrity_errors:return []
    canonical=next((g for g in catalog.games if g['id']==game.get('id')),None)
    if canonical is None:return []
    game=canonical
    edition_id=edition_id or game['editions'][0]['id']
    if not any(e['id']==edition_id for e in game['editions']):return []
    stores={s['id']:s for s in catalog.stores}
    output=[]
    for offer in catalog.offers:
        if offer['edition_id']!=edition_id:continue
        decision=OFFER_ENGINE.evaluate({'offer':offer,'store':stores.get(offer['store_id'],{}),'game':game,'edition_id':edition_id,'now':now,'policy':policy})
        if decision.eligible:output.append({**offer,'rule_trace':decision.trace})
    return sorted(output,key=lambda o:(o['price_cents'],o['id']))


def best_offer(game,**kwargs):
    offers=select_offers(game,**kwargs)
    return offers[0] if offers else None
