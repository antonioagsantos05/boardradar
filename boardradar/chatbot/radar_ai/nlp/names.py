"""Exact longest-name matching and conservative, confirmation-only fuzzy matches."""
from difflib import SequenceMatcher
import re
from .normalizer import name_key
from .synonyms import INTERESTS


def choices(catalog):
    records=[]
    for game in catalog.games:
        records.append({'entity_type':'game','id':game['id'],'title':game['name'],'aliases':[game['name'],*game.get('aliases',[])]})
    for video in catalog.videos:
        records.append({'entity_type':'videogame','id':video['id'],'title':video['title'],'aliases':[video['title'],video['franchise']]})
    return records


def match_names(text,catalog):
    key=name_key(text);records=choices(catalog);found=[]
    for record in records:
        for alias in record['aliases']:
            alias=name_key(alias)
            if not alias:continue
            for match in re.finditer(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',key):found.append((match.start(),match.end(),record))
    selected=[]
    for start,end,record in sorted(found,key=lambda hit:-(hit[1]-hit[0])):
        if any(start>=a and end<=b and (start,end)!=(a,b) for a,b,_ in selected):continue
        if not any(start==a and end==b and record['id']==r['id'] and record['entity_type']==r['entity_type'] for a,b,r in selected):selected.append((start,end,record))
    exact=[]
    for start,end,record in sorted(selected,key=lambda item:item[0]):
        if not any(r['id']==record['id'] and r['entity_type']==record['entity_type'] for r in exact):exact.append({**record,'start':start,'end':end})

    # Match only name-like segments, not arbitrary substrings of a request.
    cleaned=re.sub(r'^(?:por favor\s+)?(?:me\s+)?(?:recomende|recomenda|indique|indica|sugira|compare|comparar|fale sobre|me conte sobre|gosto de|curto|quero|qual a diferenca entre|parecido com)\s+','',key)
    cleaned=re.sub(r'^(?:um jogo |algo |jogos )?(?:parecido com|como)\s+','',cleaned)
    segments=re.split(r'\s+(?:com|e|versus|vs)\s+',cleaned)
    known=set(name_key(w) for synonyms in INTERESTS.values() for w in synonyms)
    fuzzy=[]
    for segment in segments[:5]:
        segment=re.split(r'\s+(?:para|ate|em|por|de no maximo|que|mas|nao|sem)\s+|\s+r\s+|\s+\d+\s+(?:pessoas|reais|minutos|horas)',segment)[0].strip()
        segment=re.sub(r'^(?:o jogo|o videogame|jogo|videogame)\s+','',segment)
        segment=re.sub(r'^(?:o|a|os|as)\s+','',segment)
        if not segment or segment in known or len(segment)<4 or len(segment.split())>9:continue
        if any(segment==name_key(alias) for record in exact for alias in record['aliases']):continue
        if any(token in {'pessoas','jogadores','reais','orcamento','tempo','cooperativo','competitivo','familia','prefiro','tenho','minutos'} for token in segment.split()):continue
        scores=[]
        for record in records:
            best=0.0
            for alias in record['aliases']:
                alias=name_key(alias)
                ratio=SequenceMatcher(None,segment,alias).ratio()
                # A genuine prefix may name more than one product; ask, never choose.
                if len(segment)>=5 and alias.startswith(segment+' '):ratio=max(ratio,.86)
                best=max(best,ratio)
            threshold=.84 if len(segment.split())>1 else .87
            if best>=threshold:scores.append((best,record))
        if scores:
            scores.sort(key=lambda pair:(-pair[0],pair[1]['title']))
            top=scores[0][0]
            for score,record in scores:
                if score<top-.08:continue
                candidate={k:record[k] for k in ('entity_type','id','title')}
                candidate.update(match_type='approximate',similarity=round(score,3))
                if not any(c['id']==candidate['id'] and c['entity_type']==candidate['entity_type'] for c in fuzzy):fuzzy.append(candidate)
    # Identical aliases identifying different entities are ambiguous even if exact.
    for first in exact:
        same=[r for r in exact if (r['start'],r['end'])==(first['start'],first['end'])]
        if len(same)>1:
            for r in same:
                if not any(c['id']==r['id'] and c['entity_type']==r['entity_type'] for c in fuzzy):fuzzy.append({k:r[k] for k in ('entity_type','id','title')})
    return exact,fuzzy[:5]
