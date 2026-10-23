"""Versioned thresholds, strict money conversion and preserved ranking profiles."""
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation,ROUND_FLOOR
from .catalog import load

POLICY=load('policy')


def validate_policy(policy):
    if policy.get('demo_mode') is not True or policy.get('compare_editions')!='same_internal_id' or policy.get('money_unit')!='integer_cents':
        raise ValueError('Unsupported commercial policy')
    if type(policy.get('max_offer_age_days'))!=int or policy['max_offer_age_days']<=0:
        raise ValueError('Invalid offer validity policy')
    ranking=policy['ranking']
    weights=ranking['weights']
    if set(weights)!={'themes','style','videogame','complexity','editorial'} or any(type(v) not in (int,float) or not Decimal(str(v)).is_finite() or v<0 for v in weights.values()) or sum(weights.values())!=100:
        raise ValueError('Invalid ranking weights')
    if not ranking.get('version') or not policy.get('version'):raise ValueError('Missing policy version')
    if ranking['python'].get('complexity')!='prefer_lower_with_explicit_max' or ranking['typescript'].get('complexity')!='distance_to_preference':raise ValueError('Unsupported ranking profile')
    for key in ('combat_tactical','combat_war','combat_cooperative','combat_collection_penalty'):
        value=ranking['python'][key]
        if type(value) not in (int,float) or not Decimal(str(value)).is_finite() or value<0:raise ValueError('Invalid editorial coefficient')
    return policy


def budget_to_cents(value):
    if isinstance(value,bool):raise ValueError('Invalid budget')
    try:
        amount=Decimal(str(value))
        if not amount.is_finite() or not 0<amount<=100000:raise ValueError('Invalid budget')
        # Never round a maximum budget upwards; legacy JSON is expressed in BRL.
        return int((amount*100).to_integral_value(rounding=ROUND_FLOOR))
    except (InvalidOperation,TypeError):
        raise ValueError('Invalid budget') from None


def validate_constraints(state):
    if not isinstance(state,dict) or not isinstance(state.get('preferences'),dict):raise ValueError('Invalid constraints')
    p=state['preferences']
    for field,maximum in (('players',20),('duration',10000),('complexity',5)):
        if field in p and (type(p[field]) not in (int,float) or not Decimal(str(p[field])).is_finite() or not 0<p[field]<=maximum):raise ValueError('Invalid '+field)
    if 'players' in p and int(p['players'])!=p['players']:raise ValueError('Invalid players')
    if 'budget' in p:budget_to_cents(p['budget'])
    if p.get('mode') not in (None,'cooperative','competitive'):raise ValueError('Invalid mode')
    for field in ('interests','excluded'):
        if not isinstance(state.get(field),list) or any(not isinstance(t,str) for t in state[field]):raise ValueError('Invalid '+field)
    if not isinstance(p.get('videogames',[]),list) or any(not isinstance(i,str) for i in p.get('videogames',[])):raise ValueError('Invalid videogames')
    if not isinstance(state.get('excluded_games',[]),list) or any(not isinstance(i,str) for i in state.get('excluded_games',[])):raise ValueError('Invalid excluded games')
    return state


def is_fresh(checked,now=None,policy=None):
    policy=policy or POLICY
    now=now or datetime.now(timezone.utc)
    try:
        timestamp=datetime.fromisoformat(checked.replace('Z','+00:00'))
        if timestamp.tzinfo is None:return False
        return 0<=(now-timestamp).total_seconds()<=policy['max_offer_age_days']*86400
    except (ValueError,TypeError,AttributeError):
        return False
