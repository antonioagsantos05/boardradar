"""Evidence templates, never execution of document text or inferred rulings."""
import re
from .index import load_index
from ..nlp.normalizer import normalize


def is_document_query(text):
    return bool(re.search(r'\b(?:o que (?:e|significa)|defina|conceito|nos documentos|na documentacao|buscar fontes|busque fontes|pesquise fontes)\b',normalize(text)))


def answer_query(query,*,game_id=None,edition_id=None,is_rule=False,index=None):
    base={'sources':[],'answer_confidence':'unknown','knowledge_status':'insufficient','recommendations':[]}
    def result(text,**values):return {**base,'text':text,**values}
    try:index=index if index is not None else load_index()
    except (OSError,ValueError,KeyError,TypeError):
        return result('A base documental local está indisponível. Não vou responder sem conferir as fontes.',knowledge_status='unavailable')
    if is_rule:
        if not game_id:
            return result('Qual é o jogo e a edição? Conte também a situação da partida para eu procurar evidência no manual correto.',knowledge_status='needs_game')
        if not edition_id:
            return result('Qual é a edição exata desse jogo? Ainda não tenho evidência documental autorizada suficiente para responder à ação. A edição de demonstração do catálogo não identifica um manual oficial.',knowledge_status='needs_edition')
        matches=index.reviewed_answers(query,game_id,edition_id)
        if matches:
            excerpts={answer for _,answer in matches}
            citations=list({c['chunk_id']:c for c,_ in matches}.values())
            if len(excerpts)>1:
                return result('Encontrei respostas revisadas divergentes para essa pergunta e edição. Não vou escolher uma regra: confira as fontes e a situação da partida.',sources=citations,knowledge_status='conflict')
            return result('Trecho revisado para esta pergunta e edição: “'+matches[0][1]+'”',sources=citations,
                          answer_confidence='reviewed_excerpt',knowledge_status='answered')
        hits=index.search(query,game_id,edition_id,official_only=True)
        if hits:
            return result('Encontrei trechos do documento dessa edição, mas a semelhança textual não confirma uma ação permitida. Confira os trechos e detalhe a situação; ainda não há uma resposta revisada para esta pergunta.',
                          sources=[h['citation'] for h in hits],knowledge_status='evidence_only')
        return result('Ainda não tenho evidência documental autorizada suficiente para essa ação nessa edição. Preciso de um manual ou FAQ autorizado e pertinente; não vou inventar regras ou páginas.')
    hits=index.search(query,game_id,edition_id)
    if not hits:
        return result('Não encontrei evidência suficiente na base local para essa pergunta. Tente um conceito como deck-building, cooperativo ou 4X.',knowledge_status='no_results')
    # No paraphrase: expose the exact editorial passage and its provenance.
    return result(' '.join(h['text'] for h in hits),
                  sources=[h['citation'] for h in hits],answer_confidence='editorial_excerpt',knowledge_status='answered')
