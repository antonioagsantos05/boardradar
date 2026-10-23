"""Reproducible phase-one baseline. No application behavior is changed."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'v2' / 'baseline'
SOURCE_DOCS = [
    'especificacao_completa_boardgame_poc (1).docx',
    'BoardRadar_2_0_Especificacao_Tecnica.docx',
    'BoardRadar_2_0_Plano_de_Negocio.docx',
]
SKIP = {'node_modules','.next','.npm-cache','.qa','__pycache__','.git'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, content):
    (OUT / name).write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def documents():
    records=[]
    rules=[]
    for name in SOURCE_DOCS:
        path=ROOT.parent / name
        if not path.exists():
            records.append({'file':name,'status':'missing'})
            continue
        with zipfile.ZipFile(path) as archive:
            tree=ET.fromstring(archive.read('word/document.xml'))
        paragraphs=[''.join(t.text or '' for t in p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')) for p in tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')]
        text_name=path.stem+'.txt'
        (OUT / text_name).write_text('\n'.join(paragraphs)+'\n',encoding='utf-8')
        records.append({'file':name,'status':'read','sha256':sha(path),'paragraphs':len(paragraphs),'extracted_to':text_name})
        if name.startswith('especificacao_completa'):
            for i,p in enumerate(paragraphs[:-1]):
                if p.startswith('RN-') and len(p)==6 and p[3:].isdigit():
                    rules.append({'id':p,'text':paragraphs[i+1],'source_file':name,'source_sha256':sha(path)})
    write_json('source-documents.json',records)
    write_json('business-rules-original.json',rules)
    return records,rules


def inventory():
    records=[]
    forbidden=[]
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(p in SKIP for p in rel.parts) or rel.parts[:3]==('docs','v2','baseline') or path.name.startswith('.env'):
            continue
        if path.suffix not in {'.py','.ts','.tsx','.json','.mjs','.md','.css'}:
            continue
        records.append({'file':rel.as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
        if path.suffix=='.py':
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                names=[n.name.split('.')[0] for n in node.names] if isinstance(node,ast.Import) else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else []
                for name in names:
                    if name in {'openai','ollama','transformers','llama_cpp','torch','anthropic'}:
                        forbidden.append({'file':rel.as_posix(),'import':name})
    write_json('source-inventory.json',records)
    write_json('inference-dependencies.json',{'scope':'Python imports + declared npm dependency names; not a general network security audit','forbidden_imports':forbidden,'npm_dependencies':json.loads((ROOT/'package.json').read_text(encoding='utf-8-sig'))['dependencies']})
    return forbidden


def data_summary():
    counts={}
    for path in sorted((ROOT/'src/data').glob('*.json')):
        content=json.loads(path.read_text(encoding='utf-8-sig'))
        counts[path.name]=len(content) if isinstance(content,list) else 'configuration'
    write_json('data-counts.json',counts)
    return counts


def probes():
    sys.path.insert(0,str(ROOT/'chatbot'))
    from engine import respond
    cases=[
        ('budget-natural','Tenho 200 reais e quero algo para jogar com minha família.','Capturar teto de 20000 centavos; lacuna conhecida no parser atual.'),
        ('comparison','Compare Root com Scythe.','Comparação estruturada entre os dois jogos; não implementada no chat.'),
        ('rule-evidence','Qual regra de combate posso usar nesta edição de Root?','Pedir edição e evidência; não confundir descrição de catálogo com regra oficial.'),
        ('named-game-constraints','Recomende Gloomhaven para 8 pessoas até R$ 1','Não apresentar recomendação elegível incompatível com jogadores/orçamento.'),
    ]
    results=[]
    for identifier,message,expected in cases:
        try:
            result=respond(message)
            results.append({'id':identifier,'message':message,'target_behavior':expected,'current_result':result,'classification':'diagnostic; not an acceptance pass'})
        except Exception as error:
            results.append({'id':identifier,'message':message,'error_type':type(error).__name__,'classification':'diagnostic; not an acceptance pass'})
    write_json('diagnostic-probes.json',results)


def checks(include_browser=False):
    node_dir=ROOT.parent/'.tools/node-v22.22.0-win-x64'
    node=str(node_dir/'node.exe') if (node_dir/'node.exe').exists() else 'node'
    env={**os.environ,'NEXT_TELEMETRY_DISABLED':'1','PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8','PATH':str(node_dir)+os.pathsep+os.environ.get('PATH','')}
    commands=[
        ('data-validation',[node,'node_modules/tsx/dist/cli.mjs','scripts/validate-data.ts']),
        ('typescript-tests',[node,'node_modules/tsx/dist/cli.mjs','--test','tests/recommendation.test.ts']),
        ('python-tests',[sys.executable,'chatbot/test_engine.py']),
        ('typecheck',[node,'node_modules/typescript/bin/tsc','--noEmit']),
        ('production-build',[node,'node_modules/next/dist/bin/next','build']),
        ('http-smoke',[node,'scripts/smoke.mjs']),
    ]
    if include_browser:
        commands.append(('browser-chat',[node,'scripts/check-chat-browser.mjs']))
    results=[]
    for name,command in commands:
        print('Verificando: '+name,flush=True)
        started=time.perf_counter()
        if name=='http-smoke' and any(r['name']=='production-build' and r['exit_code']!=0 for r in results):
            results.append({'name':name,'exit_code':None,'status':'skipped: build failed'})
            continue
        try:
            result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=180)
            log=result.stdout+'\n'+result.stderr
            code=result.returncode
        except subprocess.TimeoutExpired:
            log='Verificação excedeu o limite de 180 segundos. Resultado não confirmado.'
            code=124
        except OSError as error:
            log=type(error).__name__+': '+str(error)
            code=127
        (OUT/(name+'.log')).write_text(log,encoding='utf-8')
        results.append({'name':name,'command':command,'exit_code':code,'elapsed_seconds':round(time.perf_counter()-started,3),'log':name+'.log'})
        write_json('checks.json',results)
        print(f'  resultado: {code}',flush=True)
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    docs,rules=documents()
    counts=data_summary()
    probes()
    results=checks(args.browser)
    forbidden=inventory()
    complete=all(d['status']=='read' for d in docs) and len(rules)==25 and all(r['exit_code']==0 for r in results) and not forbidden
    write_json('summary.json',{'phase':1,'scope':'Audit and implementation plan only','generated_at':datetime.now().astimezone().isoformat(),'status':'passed' if complete else 'needs_attention','original_rules_extracted':len(rules),'documents':len(docs),'data_counts':counts,'checks':results,'forbidden_python_imports':forbidden,'limits':['Not an audit of factual catalogue accuracy','No latency SLA, AI quality score or production readiness certification','Diagnostics expose gaps; later phases must correct them','No LLM or inference service used']})
    print('Auditoria fase 1: '+('APROVADA' if complete else 'PENDÊNCIAS')+'; evidências em docs/v2/baseline',flush=True)
    return 0 if complete else 1


if __name__=='__main__':
    raise SystemExit(main())
