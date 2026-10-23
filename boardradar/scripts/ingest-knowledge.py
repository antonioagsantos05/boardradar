"""Ingest a permission manifest into one atomic, deployable local JSON index."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'chatbot'))
from radar_ai.knowledge.ingestion import ingest_manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--merge',type=Path,help='Validated existing snapshot; duplicate IDs are rejected.')
    args=parser.parse_args()
    try:
        merge=json.loads(args.merge.read_text(encoding='utf-8-sig')) if args.merge else None
        index=ingest_manifest(args.manifest,merge=merge)
        output=args.output.resolve()
        if output.suffix.lower()!='.json':raise ValueError('O índice de saída deve ser um arquivo .json.')
        if output==args.manifest.resolve() or args.merge and output==args.merge.resolve():
            raise ValueError('Use um caminho de saída diferente do manifesto e do índice de entrada.')
        output.parent.mkdir(parents=True,exist_ok=True)
        temporary=output.with_suffix('.tmp')
        temporary.write_text(json.dumps(index.artifact(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temporary.replace(output)
        print(f'Validated {len(index.artifact()["sources"])} sources / {len(index.artifact()["chunks"])} chunks -> {output}')
        return 0
    except (OSError,ValueError,TypeError,KeyError) as error:
        print('Ingestão recusada: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
