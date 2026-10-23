"""Validated, immutable snapshot with weighted lexical inverted postings."""
import copy
from datetime import date
import hashlib
import json
import re
from urllib.parse import urlparse
from ..catalog import DEFAULT_CATALOG, DATA
from ..nlp.normalizer import normalize

INDEX_VERSION='lexical-weighted-1'
STOP=set('a as o os e de da do das dos em no na nos nas um uma uns umas que qual quais como para por sobre jogo jogos regra regras me diga explique explica fale conte significa conceito documento documentos buscar busca busque procure favor pode posso permitido permitida desta deste nessa nesse essa esse esta este isso ser ao se eu voce'.split())
ALIASES={'cooperativos':'cooperativo','cooperativas':'cooperativo','cooperativa':'cooperativo','edicoes':'edicao','expansoes':'expansao','mecanicas':'mecanica','cartas':'carta','baralhos':'baralho','precos':'preco','ofertas':'oferta','fontes':'fonte'}


def tokens(text):
    text=normalize(text).replace('deckbuilding','deck building')
    return {ALIASES.get(t,t) for t in re.findall(r'[a-z0-9]{2,}',text) if t not in STOP}


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()


def valid_id(value):
    return isinstance(value,str) and bool(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,99}',value))


def nonempty(value,maximum=300):
    return isinstance(value,str) and 0<len(value.strip())<=maximum


def validate_documents(sources,chunks,catalog=None):
    catalog=catalog or DEFAULT_CATALOG
    if not isinstance(sources,list) or not isinstance(chunks,list) or len(sources)>1000 or len(chunks)>20000:
        raise ValueError('Base documental inválida ou muito grande.')
    games={g['id']: {e['id'] for e in g['editions']} for g in catalog.games}
    registry={};seen=set()
    for s in sources:
        if not isinstance(s,dict) or not valid_id(s.get('id')) or s['id'] in registry:
            raise ValueError('Fonte com identificador inválido ou duplicado.')
        if not all(nonempty(s.get(k)) for k in ('title','version','license')):
            raise ValueError('Fonte sem título, versão ou licença.')
        if (s.get('permission') not in ('owned','authorized','open-license') or s.get('review_status')!='reviewed'
            or s.get('authority') not in ('editorial','official') or s.get('type') not in ('editorial','manual','faq')):
            raise ValueError('Fonte sem autorização e revisão registradas.')
        if s['permission']=='owned':
            if s['license']!='project-owned' or s['authority']!='editorial':
                raise ValueError('Material próprio não comprova autoridade oficial.')
        elif not nonempty(s.get('permission_reference'),1000):
            raise ValueError('Registre a evidência de autorização ou licença aberta.')
        if s['authority']=='official' and (not nonempty(s.get('authority_reference'),1000) or s['type'] not in ('manual','faq')):
            raise ValueError('Manual oficial exige referência de autoridade.')
        try:
            if not isinstance(s.get('retrieved_at'),str) or len(s['retrieved_at'])!=10:raise ValueError()
            date.fromisoformat(s['retrieved_at'])
        except (TypeError,ValueError):raise ValueError('Data documental inválida.') from None
        url=s.get('url')
        if url is not None and (not isinstance(url,str) or len(url)>2000 or urlparse(url).scheme!='https' or not urlparse(url).netloc):
            raise ValueError('URL documental inválida; use HTTPS ou null.')
        gid=s.get('game_id');eid=s.get('edition_id')
        if gid is not None and not isinstance(gid,str) or eid is not None and not isinstance(eid,str):
            raise ValueError('Identidade documental inválida.')
        if (gid is None)!=(eid is None) or gid is not None and (gid not in games or eid not in games[gid]):
            raise ValueError('Fonte com jogo/edição desconhecido ou incompatível.')
        if s['authority']=='official' and gid is None:raise ValueError('Fonte oficial exige jogo e edição exatos.')
        registry[s['id']]=s
    for c in chunks:
        if not isinstance(c,dict) or not valid_id(c.get('id')) or c['id'] in seen:
            raise ValueError('Trecho com identificador inválido ou duplicado.')
        seen.add(c['id']);s=registry.get(c.get('source_id'))
        if not s:raise ValueError('Trecho sem fonte registrada.')
        if not nonempty(c.get('text'),1800) or not nonempty(c.get('section'),200):
            raise ValueError('Trecho sem texto/seção ou acima do limite.')
        if c.get('game_id')!=s.get('game_id') or c.get('edition_id')!=s.get('edition_id'):
            raise ValueError('Trecho e fonte não pertencem ao mesmo jogo/edição.')
        if c.get('page') is not None and (type(c['page'])!=int or c['page']<1):raise ValueError('Página inválida.')
        qa=c.get('qa',[])
        if not isinstance(qa,list) or len(qa)>20:raise ValueError('Respostas curadas inválidas.')
        for a in qa:
            if (not isinstance(a,dict) or not nonempty(a.get('question'),1000) or not nonempty(a.get('answer_excerpt'),1800)
                or a['answer_excerpt'] not in c['text'] or a.get('reviewed') is not True
                or not nonempty(a.get('review_reference'),1000) or s['authority']!='official'):
                raise ValueError('Resposta exige revisão e trecho literal de manual/FAQ oficial.')
    return True


class DocumentIndex:
    def __init__(self,sources,chunks,*,catalog=None):
        validate_documents(sources,chunks,catalog)
        self._scope_terms={g['id']:tokens(' '.join([g['name'],*g.get('aliases',[])])) for g in (catalog or DEFAULT_CATALOG).games}
        self._sources={s['id']:copy.deepcopy(s) for s in sources}
        self._chunks={c['id']:copy.deepcopy(c) for c in chunks}
        self._postings={}
        for c in self._chunks.values():
            section=tokens(c['section']);body=tokens(c['text'])
            for term in section|body:
                self._postings.setdefault(term,{})[c['id']]=(3 if term in section else 0)+(1 if term in body else 0)

    def artifact(self):
        data=copy.deepcopy({'sources':list(self._sources.values()),'chunks':list(self._chunks.values())})
        return {'schema_version':1,'index_version':INDEX_VERSION,'content_sha256':digest(data),**data}

    @classmethod
    def from_artifact(cls,value,*,catalog=None):
        if not isinstance(value,dict) or type(value.get('schema_version'))!=int or value.get('schema_version')!=1 or value.get('index_version')!=INDEX_VERSION:
            raise ValueError('Versão de índice incompatível.')
        if value.get('content_sha256')!=digest({'sources':value.get('sources'),'chunks':value.get('chunks')}):
            raise ValueError('Integridade do índice documental inválida.')
        return cls(value['sources'],value['chunks'],catalog=catalog)

    def resolve(self,chunk_id):
        c=self._chunks.get(chunk_id)
        if c is None:return None
        s=self._sources[c['source_id']]
        return {'source_id':s['id'],'chunk_id':c['id'],'title':s['title'],'section':c['section'],
                'page':c.get('page'),'game_id':c.get('game_id'),'edition_id':c.get('edition_id'),
                'version':s['version'],'date':s['retrieved_at'],'license':s['license'],
                'url':s.get('url'),'authority':s['authority'],'excerpt':c['text'],
                'content_sha256':hashlib.sha256(c['text'].encode('utf-8')).hexdigest()}

    def search(self,query,game_id=None,edition_id=None,limit=4,official_only=False):
        if not isinstance(query,str) or not 0<len(query.strip())<=1000:raise ValueError('Consulta inválida.')
        if type(limit)!=int or not 1<=limit<=10:raise ValueError('Limite documental inválido.')
        if edition_id and not game_id or official_only and (not game_id or not edition_id):return []
        terms=tokens(query)
        if game_id:terms-=self._scope_terms.get(game_id,set())
        if edition_id:terms-=tokens(edition_id)
        if not terms:return []
        scores={}
        for term in terms:
            for cid,weight in self._postings.get(term,{}).items():scores[cid]=scores.get(cid,0)+weight
        hits=[]
        for cid,score in scores.items():
            c=self._chunks[cid];s=self._sources[c['source_id']]
            if official_only and s['authority']!='official':continue
            if game_id and c.get('game_id')!=game_id:continue
            if edition_id and c.get('edition_id')!=edition_id:continue
            # General searches never leak edition-specific rules into concept answers.
            if not game_id and c.get('game_id') is not None:continue
            overlap=terms & (tokens(c['section'])|tokens(c['text']))
            coverage=len(overlap)/len(terms)
            if coverage<.5:continue
            hits.append({**copy.deepcopy(c),'source':copy.deepcopy(s),'score':round(score/(4*len(terms)),4),
                         'coverage':round(coverage,4),'citation':self.resolve(cid)})
        return sorted(hits,key=lambda h:(-h['score'],h['id']))[:limit]

    def reviewed_answers(self,query,game_id,edition_id):
        """Exact curated question; fuzzy lexical similarity cannot authorize an action."""
        key=question_key(query)
        return [(self.resolve(c['id']),a['answer_excerpt']) for c in self._chunks.values()
                if c.get('game_id')==game_id and c.get('edition_id')==edition_id
                and self._sources[c['source_id']]['authority']=='official'
                for a in c.get('qa',[]) if question_key(a['question'])==key]


def question_key(query):
    # Keep negation, order and numbers: "posso" and "não posso" must stay distinct.
    return ' '.join(re.findall(r'[a-z0-9]+',normalize(query)))


def load_index(path=None):
    path=path or DATA/'knowledge-index.json'
    return DocumentIndex.from_artifact(json.loads(path.read_text(encoding='utf-8-sig')))
