"""Reproducible retrieval acceptance cases, not a population quality benchmark."""
import json
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'chatbot'))
from radar_ai.knowledge import load_index,answer_query


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'docs/v2/phase5');args=parser.parse_args()
    fixture=json.loads((ROOT/'tests/fixtures/knowledge-cases.json').read_text(encoding='utf-8'))
    index=load_index();results=[]
    for case in fixture['cases']:
        response=answer_query(case['query'],index=index,**case.get('scope',{}))
        ids=[s['chunk_id'] for s in response['sources']]
        citations_valid=all(index.resolve(s['chunk_id'])==s for s in response['sources'])
        passed=(response['answer_confidence']==case['confidence'] and response['knowledge_status']==case['status']
                and (ids[:1]==[case['first_chunk']] if case.get('first_chunk') else ids==[]) and citations_valid)
        results.append({'id':case['id'],'passed':passed,'chunk_ids':ids,'citations_resolve':citations_valid,
                        'answer_confidence':response['answer_confidence'],'status':response['knowledge_status']})
    output=args.output_dir;output.mkdir(parents=True,exist_ok=True)
    report={'fixture_version':fixture['version'],'index_version':index.artifact()['index_version'],
            'content_sha256':index.artifact()['content_sha256'],'source_count':len(index.artifact()['sources']),
            'chunk_count':len(index.artifact()['chunks']),'case_count':len(results),
            'passed_count':sum(r['passed'] for r in results),'results':results,
            'limits':['Fixed editorial acceptance set, not general rule-answer accuracy','No official manuals in deployed corpus','No latency/SLA measurement']}
    (output/'retrieval-evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Retrieval acceptance: {report['passed_count']}/{report['case_count']}; corpus: {report['source_count']} sources / {report['chunk_count']} chunks")
    return 0 if all(r['passed'] for r in results) else 1


if __name__=='__main__':raise SystemExit(main())
