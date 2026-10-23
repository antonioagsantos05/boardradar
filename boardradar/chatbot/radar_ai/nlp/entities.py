"""Slot extraction. Money is parsed with Decimal and represented in integer cents."""
from decimal import Decimal,InvalidOperation
import re
from .models import Entities
from .normalizer import normalize,numeric_text,contains
from .synonyms import INTERESTS

NUMBER=r'-?\d+(?:[.,]\d+)*'


def negated(text,start):
    prefix=re.split(r'[,.;!?]|\b(?:mas|porem|prefiro)\b',text[:start])[-1]
    # A fresh affirmative verb ends the previous negative clause.
    starts=list(re.finditer(r'\b(?:quero|gosto de|curto|prefiro|aceito|recomen\w*|indic\w*|sug\w*)\b',prefix))
    if starts:
        verb=starts[-1]
        before=prefix[:verb.start()]
        prefix=prefix[verb.start():]
        if re.search(r'\bnao\s*$',before):prefix='nao '+prefix
    return bool(re.search(r'\b(?:nao|sem|evitar|odeio|nem)\b',prefix))


def negative(text,word):
    match=contains(text,word)
    return bool(match and negated(text,match.start()))


def parse_money(value):
    if re.fullmatch(r'-?\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?',value):value=value.replace('.','').replace(',','.')
    elif re.fullmatch(r'-?\d+(?:[.,]\d{1,2})?',value):value=value.replace(',','.')
    else:raise ValueError('Use valores como 200, 200,50 ou 1.000,50.')
    try:
        amount=Decimal(value)
        if not amount.is_finite() or not Decimal('.01')<=amount<=100000:raise ValueError('Informe um orçamento entre R$ 0,01 e R$ 100.000.')
        return int(amount*100)
    except InvalidOperation:raise ValueError('Orçamento inválido.') from None


def _resolve(values,field,result,errors,text):
    last=values[-1] if values else None
    values=list(dict.fromkeys(values))
    if len(values)>1 and not re.search(r'\b(?:melhor|corrigindo|na verdade|em vez|agora)\b',text):
        label={'players':'quantidade de jogadores','max_price_cents':'orçamento','duration_minutes':'tempo de partida'}[field]
        errors.append({'field':{'max_price_cents':'budget','duration_minutes':'duration'}.get(field,field),'message':'Encontrei valores diferentes para '+label+'. Qual deles devo usar?','values':values})
    elif values:setattr(result,field,last)


def extract(text,state,intent):
    e=Entities();errors=[];numeric=numeric_text(text)
    pending=state.get('waiting_for')
    # Removals are field-specific; "limpar orçamento" must not reset everything.
    removal_patterns={
      'budget':r'sem (?:limite(?: de)?|restricao de) (?:orcamento|preco|valor)|qualquer (?:preco|valor)|sem orcamento|(?:remov\w*|retir\w*|tir\w*|limp\w*) (?:o |a |limite de |teto de )*(?:orcamento|preco|valor)',
      'duration':r'sem (?:limite|restricao) de (?:tempo|duracao)|qualquer duracao|(?:remov\w*|retir\w*|tir\w*|limp\w*) (?:o |a |limite de |filtro de )*(?:tempo|duracao)',
      'players':r'qualquer (?:quantidade de jogadores|numero de jogadores)|sem filtro de jogadores|(?:remov\w*|retir\w*|tir\w*|limp\w*) (?:o |a |filtro de |numero de )*(?:jogadores|pessoas)',
      'complexity':r'qualquer complexidade|pode ser complexo|mais complexo|(?:remov\w*|retir\w*|tir\w*|limp\w*) (?:o |a |limite de )*complexidade',
      'mode':r'tanto faz|qualquer modo|nao (?:precisa|tem que) ser cooperativ\w*|nao tenho preferencia (?:por |de )?cooperativ\w*',
      'interests':r'(?:remov\w*|retir\w*|limp\w*) (?:os |as |o |a )*(?:temas|tema|estilos|estilo|interesses)',
      'videogames':r'(?:remov\w*|retir\w*|limp\w*) (?:os |as |o |a |preferencia por )*(?:videogames|videogame|referencias)',
    }
    for field,pattern in removal_patterns.items():
        match=re.search(pattern,text)
        if match and (field=='mode' or not negated(text,match.start())):e.remove.append(field)
    if text in ('nao','nao quero') and pending=='budget':e.remove.append('budget')

    players=[]
    def player_number(token,position):
        if not re.fullmatch(r'-?\d+',token):
            errors.append({'field':'players','message':'Informe uma quantidade inteira de jogadores, sem separador decimal.'})
        else:players.append((position,Decimal(token)))
    for match in re.finditer(r'(?<![\w.,])('+NUMBER+r')\s*(?:pessoas|jogadores|participantes|amigos)\b',numeric):
        player_number(match.group(1),match.start(1))
    for match in re.finditer(r'\b(?:para|somos|seremos|em|com)\s+('+NUMBER+r')(?![\d.,])',numeric):
        suffix=numeric[match.end():]
        if re.match(r'\s*(?:reais|real|conto|contos|minutos|min|horas?|h|anos|jogos|r\$)\b',suffix):continue
        player_number(match.group(1),match.start(1))
    # An explicit alternative must be clarified, not silently pick the first.
    alternative=re.search(r'('+NUMBER+r')\s*(?:ou|a)\s*('+NUMBER+r')\s*(?:pessoas|jogadores)',numeric)
    if alternative:
        players=[];player_number(alternative.group(1),alternative.start(1));player_number(alternative.group(2),alternative.start(2))
    if re.fullmatch(NUMBER,numeric) and pending=='players':player_number(numeric,0)
    solo=re.search(r'\b(?:solo|sozinho|sozinha)\b',numeric)
    duel=re.search(r'\bduelos?\b',numeric)
    if solo:players.append((solo.start(),Decimal(1)))
    if duel:players.append((duel.start(),Decimal(2)));e.mode='competitive'
    players=[value for _,value in sorted(players,key=lambda item:item[0])]
    if 'players' not in e.remove:
        if any(not v.is_finite() or v!=int(v) or not 1<=v<=20 for v in players):errors.append({'field':'players','message':'Informe uma quantidade inteira de 1 a 20 jogadores.'})
        else:_resolve([int(v) for v in players],'players',e,errors,text)

    money=[]
    patterns=[r'r\$\s*('+NUMBER+r')',r'('+NUMBER+r')\s*(?:reais|real|conto|contos)\b',r'\b(?:ate|orcamento(?: de)?|teto(?: de)?|no maximo|gastar(?: ate)?)\s*(?:r\$\s*)?('+NUMBER+r')']
    for pattern in patterns:
        for match in re.finditer(pattern,numeric):
            tail=numeric[match.end():]
            if re.match(r'\s*(?:minutos|min|horas?|h|pessoas|jogadores|participantes|anos|jogos)\b',tail):continue
            try:money.append((match.start(1),parse_money(match.group(1))))
            except ValueError as error:errors.append({'field':'budget','message':str(error)})
    if re.fullmatch(NUMBER,numeric) and pending=='budget':
        try:money.append((0,parse_money(numeric)))
        except ValueError as error:errors.append({'field':'budget','message':str(error)})
    if 'budget' not in e.remove:_resolve([value for _,value in sorted(money,key=lambda item:item[0])],'max_price_cents',e,errors,text)

    durations=[];consumed=[]
    def time_number(token):
        if not re.fullmatch(r'-?\d+(?:[.,]\d{1,2})?',token):raise ValueError('Tempo inválido')
        return Decimal(token.replace(',','.'))
    for combined in re.finditer(r'('+NUMBER+r')\s*(?:horas?|h)\s*(?:e\s*)?(?:meia|('+NUMBER+r')\s*(?:minutos|min)?)\b',numeric):
        try:durations.append((combined.start(),float(time_number(combined.group(1))*60+(time_number(combined.group(2)) if combined.group(2) else 30))))
        except (ValueError,InvalidOperation):errors.append({'field':'duration','message':'Use um tempo como 30 minutos, 1 hora ou 1h30.'})
        consumed.append(combined.span())
    for match in re.finditer(r'\bmeia hora\b',numeric):
        if not any(a<=match.start()<b for a,b in consumed):durations.append((match.start(),30.0))
    for match in re.finditer(r'('+NUMBER+r')\s*(minutos|min|horas?|h)\b',numeric):
        if not any(a<=match.start()<b for a,b in consumed):
            try:durations.append((match.start(),float(time_number(match.group(1)))*(60 if match.group(2).startswith('h') else 1)))
            except (ValueError,InvalidOperation):errors.append({'field':'duration','message':'Use um tempo como 30 minutos, 1 hora ou 1h30.'})
    durations=[value for _,value in sorted(durations)]
    if 'duration' not in e.remove:
        if any(not 0<v<=10000 for v in durations):errors.append({'field':'duration','message':'Informe um tempo positivo, como 30 minutos ou 1 hora.'})
        else:_resolve(durations,'duration_minutes',e,errors,text)

    # A question about a game being beginner-friendly must not change preference.
    if intent not in ('information','explanation','rule','comparison','edition','offer'):
        for match in re.finditer(r'\b(?:iniciante\w*|faceis|facil|simples|leves?|complexos?|dificil|pesados?)\b',text):
            word=match.group();neg=negated(text,match.start())
            if word.startswith(('complex','dific','pesad')):
                if neg:e.max_complexity=2
                elif 'complexity' not in e.remove:e.remove.append('complexity')
            elif not neg:e.max_complexity=2
    for tag,synonyms in INTERESTS.items():
        occurrences=[]
        for synonym in synonyms:
            for match in re.finditer(r'(?<!\w)'+re.escape(normalize(synonym))+r'(?!\w)',text):occurrences.append((match.start(),negated(text,match.start())))
        if not occurrences:continue
        signs={neg for _,neg in occurrences}
        if len(signs)>1 and not re.search(r'\b(?:mas|porem|melhor|na verdade|agora|corrigindo)\b',text):
            errors.append({'field':'negation','message':'Você quer incluir ou excluir '+tag+'?','tag':tag});continue
        last_negative=sorted(occurrences)[-1][1]
        if tag=='cooperativo' and 'mode' in e.remove:continue
        (e.excluded_tags if last_negative else e.preferred_tags).append(tag)
        if tag=='cooperativo':e.mode='competitive' if last_negative else 'cooperative'
    if re.search(r'\b(?:competitivo\w*|contra (?:outros|amigos)|um contra|uns contra)\b',text):
        m=re.search(r'competitivo\w*|contra (?:outros|amigos)|um contra|uns contra',text)
        if m and not negated(text,m.start()):e.mode='competitive'
    if re.search(r'nao\s+quero\s+nao\s+cooperativ',text):errors.append({'field':'negation','message':'Você prefere cooperativo ou competitivo?'})
    return e,errors
