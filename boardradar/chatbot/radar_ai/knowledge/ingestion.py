"""Offline, explicit ingestion of licensed UTF-8 text; no download or execution."""
import hashlib
import json
from pathlib import Path
from .index import DocumentIndex, validate_documents


def split_text(text,maximum=1600):
    if type(maximum)!=int or not 1<=maximum<=1800:raise ValueError('Tamanho de trecho inválido.')
    remaining=text.strip();chunks=[]
    while remaining:
        end=min(len(remaining),maximum)
        if end<len(remaining):
            boundary=remaining.rfind('\n',0,end)
            if boundary<maximum//2:boundary=remaining.rfind(' ',0,end)
            if boundary>=maximum//2:end=boundary
        chunks.append(remaining[:end]);remaining=remaining[end:].lstrip()
    return chunks


def ingest_manifest(manifest_path,*,merge=None,catalog=None):
    path=Path(manifest_path).resolve();root=path.parent
    manifest=json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(manifest,dict) or set(manifest)!={'sources','documents'}:
        raise ValueError('Manifesto deve conter somente sources e documents.')
    sources=manifest['sources'];documents=manifest['documents']
    validate_documents(sources,[],catalog)
    if not isinstance(documents,list) or len(documents)>1000:raise ValueError('Lista de documentos inválida.')
    chunks=[]
    for d in documents:
        if not isinstance(d,dict) or not all(k in d for k in ('id','source_id','file','section','page')):
            raise ValueError('Documento sem identidade, arquivo, seção ou página explícita.')
        source=next((s for s in sources if s['id']==d['source_id']),None)
        if not source:raise ValueError('Documento sem fonte autorizada no manifesto.')
        if not isinstance(d['file'],str) or Path(d['file']).suffix.lower()!='.txt':
            raise ValueError('Somente texto UTF-8 .txt revisado é aceito nesta fase.')
        file=(root/d['file']).resolve()
        if not file.is_relative_to(root):raise ValueError('Arquivo fora da pasta do manifesto.')
        if file.stat().st_size>5_000_000:raise ValueError('Documento acima de 5 MB.')
        raw=file.read_bytes();text=raw.decode('utf-8-sig')
        parts=split_text(text)
        if not parts:raise ValueError('Documento vazio.')
        if d.get('qa') and len(parts)>1:
            raise ValueError('Separe respostas revisadas em arquivos com no máximo 1600 caracteres.')
        for i,part in enumerate(parts,1):
            chunks.append({'id':d['id'] if len(parts)==1 else f"{d['id']}-{i}",
                           'source_id':source['id'],'game_id':source.get('game_id'),
                           'edition_id':source.get('edition_id'),'section':d['section'],'page':d['page'],
                           'text':part,'qa':d.get('qa',[]),'document_sha256':hashlib.sha256(raw).hexdigest()})
    if merge is not None:
        original=DocumentIndex.from_artifact(merge,catalog=catalog).artifact()
        sources=[*original['sources'],*sources];chunks=[*original['chunks'],*chunks]
    return DocumentIndex(sources,chunks,catalog=catalog)
