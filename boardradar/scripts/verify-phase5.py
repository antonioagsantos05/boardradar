"""Run phase-five acceptance without overwriting the historical phase-one baseline."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/v2/phase5'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    bundled=ROOT.parent/'.tools/node-v22.22.0-win-x64/node.exe'
    node=str(bundled) if bundled.exists() else 'node'
    env={**os.environ,'NEXT_TELEMETRY_DISABLED':'1','PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8','PATH':str(bundled.parent)+os.pathsep+os.environ.get('PATH','')}
    tests=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'tests').glob('*.test.ts'))
    commands=[('retrieval-evaluation',[sys.executable,'scripts/evaluate-knowledge.py']),('data-validation',[node,'node_modules/tsx/dist/cli.mjs','scripts/validate-data.ts']),('typescript-tests',[node,'node_modules/tsx/dist/cli.mjs','--test',*tests]),('python-tests',[sys.executable,'-m','unittest','discover','-s','chatbot','-p','test_*.py','-v']),('typecheck',[node,'node_modules/typescript/bin/tsc','--noEmit']),('build',[node,'node_modules/next/dist/bin/next','build']),('http-smoke',[node,'scripts/smoke.mjs'])]
    if args.browser:commands.append(('browser',[node,'scripts/check-chat-browser.mjs']))
    results=[]
    for name,command in commands:
        print('Fase 5: '+name,flush=True)
        start=time.perf_counter()
        try:
            process=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
            code=process.returncode;log=process.stdout+'\n'+process.stderr
        except (subprocess.TimeoutExpired,OSError) as error:
            code=124;log=type(error).__name__
        (OUT/(name+'.log')).write_text(log,encoding='utf-8')
        results.append({'name':name,'command':command,'exit_code':code,'elapsed_seconds':round(time.perf_counter()-start,3),'log':name+'.log'})
        (OUT/'checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('  resultado: '+str(code),flush=True)
        if code:break
    sys.path.insert(0,str(ROOT/'chatbot'))
    from radar_ai.recommendation import CANDIDATE_ENGINE
    from radar_ai.offers import OFFER_ENGINE
    from radar_ai.policies import POLICY
    from engine import respond
    rules={'policy_version':POLICY['version'],'ranking_version':POLICY['ranking']['version'],'candidate_rules':CANDIDATE_ENGINE.describe(),'offer_rules':OFFER_ENGINE.describe()}
    (OUT/'rule-registry.json').write_text(json.dumps(rules,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    examples={message:respond(message) for message in ['O que e deck-building?','O que e cooperativo?','Posso atacar em Root g45-pt-base?','O que e Zorbledoodle?']}
    (OUT/'example-responses.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    scope=[*ROOT.glob('chatbot/radar_ai/**/*.py'),*ROOT.glob('chatbot/test_*.py'),ROOT/'chatbot/engine.py',ROOT/'src/domain/recommendation.ts',ROOT/'src/domain/offer-policy.ts',ROOT/'src/data/policy.json',ROOT/'src/data/media-works.json',ROOT/'src/data/media-game-relations.json',ROOT/'src/components/ChatAssistant.tsx',ROOT/'src/app/globals.css',ROOT/'src/app/api/chat/route.ts',ROOT/'tests/fixtures/nlp-cases.json',ROOT/'tests/phase2.test.ts',ROOT/'tests/fixtures/recommendation-invariants.json',ROOT/'scripts/smoke.mjs',ROOT/'scripts/check-chat-browser.mjs',ROOT/'scripts/verify-phase5.py',ROOT/'scripts/evaluate-knowledge.py',ROOT/'scripts/index-knowledge.py',ROOT/'scripts/ingest-knowledge.py',ROOT/'chatbot/knowledge.py',ROOT/'src/data/knowledge-index.json',ROOT/'src/data/knowledge-sources.json',ROOT/'src/data/knowledge-chunks.json',ROOT/'tests/fixtures/knowledge-cases.json']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in scope}
    passed=len(results)==len(commands) and all(r['exit_code']==0 for r in results)
    ts_log=(OUT/'typescript-tests.log').read_text(encoding='utf-8') if (OUT/'typescript-tests.log').exists() else ''
    py_log=(OUT/'python-tests.log').read_text(encoding='utf-8') if (OUT/'python-tests.log').exists() else ''
    ts_count=re.search(r'# tests (\d+)',ts_log);py_count=re.search(r'Ran (\d+) tests',py_log)
    test_counts={'typescript':int(ts_count.group(1)) if ts_count else None,'python':int(py_count.group(1)) if py_count else None}
    summary={'phase':5,'generated_at':datetime.now().astimezone().isoformat(),'status':'passed' if passed else 'needs_attention','checks':results,'test_counts':test_counts,'policy_version':POLICY['version'],'source_sha256':hashes,'limits':['Command durations are not request latency benchmarks','Catalogue metadata remains preliminary','Client state is untrusted preferences, not identity or commercial authorization','30-minute absolute context expiry; legacy state is accepted on initial migration','No LLM/inference provider','No official manuals in deployed corpus; eight owned editorial excerpts only. Phase 6 hosting remains pending']}
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Fase 5: '+summary['status'],flush=True)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
