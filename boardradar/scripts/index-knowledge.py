"""Build a validated deployment snapshot from the project's own editorial seed."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'chatbot'))
from radar_ai.catalog import load,DATA
from radar_ai.knowledge.index import DocumentIndex


def main():
    index=DocumentIndex(load('knowledge-sources'),load('knowledge-chunks'))
    output=DATA/'knowledge-index.json'
    temporary=output.with_suffix('.tmp')
    temporary.write_text(json.dumps(index.artifact(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(output)
    print(f'Validated {len(index.artifact()["chunks"])} editorial chunks -> {output}')


if __name__=='__main__':main()
