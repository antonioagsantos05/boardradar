"""Generate the current project handoff as a DOCX using the standard library."""
import json
import re
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT.parent / 'BoardRadar_Documentacao_Projeto.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
parts = []
images = []


def paragraph(text='', style='Normal', page_break=False):
    properties = f'<w:pStyle w:val="{style}"/>'
    if page_break:
        properties += '<w:pageBreakBefore/>'
    parts.append(f'<w:p><w:pPr>{properties}</w:pPr><w:r><w:t xml:space="preserve">{escape(str(text))}</w:t></w:r></w:p>')


def table(headers, rows, widths):
    cells = []
    for index, row in enumerate([headers] + rows):
        cell_xml = []
        for value, width in zip(row, widths):
            shade = '<w:shd w:fill="0B2B36"/>' if index == 0 else ('<w:shd w:fill="F2F5EF"/>' if index % 2 else '')
            run_props = '<w:b/><w:color w:val="FFFFFF"/>' if index == 0 else '<w:color w:val="16333B"/>'
            cell_xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr><w:p><w:pPr><w:spacing w:after="80" w:before="80"/></w:pPr><w:r><w:rPr>{run_props}<w:sz w:val="19"/></w:rPr><w:t xml:space="preserve">{escape(str(value))}</w:t></w:r></w:p></w:tc>')
        cells.append('<w:tr><w:trPr>' + ('<w:tblHeader/>' if index == 0 else '') + '<w:cantSplit/></w:trPr>' + ''.join(cell_xml) + '</w:tr>')
    parts.append('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders><w:bottom w:val="single" w:sz="4" w:color="DCE4DA"/><w:insideH w:val="single" w:sz="4" w:color="DCE4DA"/></w:tblBorders><w:tblCellMar><w:top w:w="50" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="50" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>' + ''.join(f'<w:gridCol w:w="{n}"/>' for n in widths) + '</w:tblGrid>' + ''.join(cells) + '</w:tbl>')
    paragraph()


def picture(path, max_width, max_height):
    if not path.exists():
        return
    data = path.read_bytes()
    width, height = struct.unpack('>II', data[16:24])
    scale = min(max_width / width, max_height / height)
    cx, cy = round(width * scale * 914400), round(height * scale * 914400)
    index = len(images) + 1
    images.append((f'image{index}.png', data))
    parts.append(f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{index}" name="Captura {index}" descr="Interface do assistente Radar em execução local"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{index}" name="image{index}.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rImage{index}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def read_json(name):
    return json.loads((ROOT / 'src' / 'data' / f'{name}.json').read_text(encoding='utf-8-sig'))


games, videos, stores, offers = [read_json(n) for n in ['games', 'videogames', 'stores', 'offers']]
paragraph('BOARDRADAR', 'Title')
paragraph('Documentação do projeto e entrega da POC', 'Subtitle')
paragraph('Versão 1.1 • 19 de outubro de 2026', 'Subtitle')
paragraph('Descubra seu próximo jogo. Encontre uma experiência com a sua cara.', 'Lead')
paragraph('Este documento registra o estado implementado do projeto local, incluindo o assistente conversacional em Python. Complementa a especificação original e distingue funcionalidades disponíveis de pendências para produção.')
paragraph('DEMONSTRAÇÃO: lojas, preços e históricos são fictícios. Nenhuma compra real é realizada. Metadados do catálogo e identificação de edições ainda precisam de conferência editorial.', 'Notice')
table(['Entrega', 'Quantidade / situação'], [
    ['Jogos de tabuleiro', str(len(games))], ['Referências de videogames', str(len(videos))],
    ['Lojas fictícias', str(len(stores))], ['Ofertas simuladas', str(len(offers))],
    ['Assistente', 'Python local, contexto de conversa e regras de catálogo'],
    ['Persistência', 'JSON somente leitura; preferências e favoritos no navegador'],
], [3300, 6000])

paragraph('1. Stack e arquitetura', 'Heading1', True)
table(['Camada', 'Tecnologia', 'Responsabilidade'], [
    ['Aplicação web', 'Next.js 16.4.2 / React 19 / TypeScript', 'Páginas, catálogo, filtros e APIs'],
    ['Apresentação', 'CSS, SVG e Lucide', 'Identidade BoardRadar e interface responsiva'],
    ['Validação', 'Zod / validação Python', 'Contratos de entrada e integridade dos dados'],
    ['Assistente', 'Python 3.13.7; biblioteca padrão', 'Interpretação, contexto e recomendação conversacional'],
    ['Runtime web', 'Node.js 22.22.0 / npm 10.9.4', 'Execução e gestão dos processos locais'],
    ['Armazenamento', 'Arquivos JSON e localStorage', 'Catálogo e preferências sem banco'],
], [1800, 3300, 4200])
paragraph('Fluxo do chat', 'Heading2')
for line in ['Navegador → ChatAssistant.tsx → POST /api/chat (Next.js)', 'Next.js → HTTP privado em loopback + token efêmero → Python', 'Python → valida contexto → interpreta mensagem → lê catálogo → aplica filtros → pontua', 'Python → resposta + sugestões + novo estado → Next.js → interface']:
    paragraph(line, 'Code')
paragraph('npm start e npm run dev iniciam Next.js e Python juntos. O sistema escolhe uma porta local para o serviço Python. O token interno muda a cada execução e não é enviado ao navegador. O chat não exige chave de API, pip, Docker ou banco.')
paragraph('A recomendação da navegação continua em TypeScript. A recomendação conversacional utiliza um motor Python próprio sobre os mesmos JSONs; mantém filtros obrigatórios e acrescenta curadoria de combate. Não é um modelo generativo nem uma implementação de compreensão irrestrita de linguagem.')

paragraph('2. Funcionalidades e operação', 'Heading1')
paragraph('As seções abaixo são extraídas do README atual do projeto. Os comandos são executados dentro da pasta boardradar; o caminho local completo é C:\\Users\\antonio.agsantos\\Desktop\\teste\\boardradar.')
markdown = (ROOT / 'README.md').read_text(encoding='utf-8-sig')
code = False
for line in markdown.splitlines():
    if line.startswith('# '):
        continue
    if line.startswith('```'):
        code = not code
        continue
    if not line.strip():
        continue
    if code:
        paragraph(line, 'Code')
    elif line.startswith('## '):
        paragraph(line[3:], 'Heading2')
    else:
        paragraph(line.replace('`', ''), 'Normal')

paragraph('3. Verificações realizadas nesta entrega', 'Heading1', True)
table(['Verificação', 'Resultado registrado'], [
    ['Testes TypeScript', '6 testes aprovados: filtros, orçamento, busca, edição, datas e afinidade editorial'],
    ['Testes Python', '17 testes aprovados: combate, contexto, respostas curtas, negações, orçamento, tempo, reset, entradas inválidas e alternativas'],
    ['Build Next.js', 'Compilação e TypeScript concluídos; páginas e APIs geradas'],
    ['Smoke HTTP', 'Páginas, 404, catálogo, edição, ofertas, histórico, recomendação, proxy Python, contexto e bloqueio comercial aprovados'],
    ['Chrome headless', 'Conversa real, refinamento, orçamento livre, mobile, reset e assunto desconhecido aprovados; sem exceções JavaScript no cenário'],
], [2400, 6900])
paragraph('Esses resultados cobrem os cenários executados no ambiente local. Não representam certificação de acessibilidade, teste de carga, validação de todas as frases possíveis ou conferência factual do catálogo.')

paragraph('4. Interface validada', 'Heading1', True)
paragraph('Captura desktop — conversa com refinamento e ofertas demonstrativas.', 'Caption')
picture(ROOT / '.qa' / 'chat-desktop.png', 6.3, 4.5)
paragraph('Captura mobile — painel de conversa adaptado à largura de 390 px.', 'Caption', True)
picture(ROOT / '.qa' / 'chat-mobile.png', 3.1, 6.6)

paragraph('5. Próximos passos', 'Heading1', True)
for text in [
    '1. Revisar factual e editorialmente os 60 jogos: jogadores, duração, complexidade, categorias e regras da edição.',
    '2. Confirmar os produtos comparáveis, especialmente kits e decks de jogos colecionáveis, com idioma, editora e SKU.',
    '3. Coletar conversas de teste consentidas e ampliar os sinônimos e os fluxos a partir de falhas reais de compreensão.',
    '4. Se desejado, integrar IA generativa ao serviço Python, mantendo respostas fundamentadas no catálogo e preços provenientes das ofertas.',
    '5. Planejar hospedagem que suporte o processo Python, autenticação administrativa e integrações comerciais autorizadas.',
    '6. Definir critérios mensuráveis de desempenho e concluir auditoria de acessibilidade e privacidade antes de produção.',
]:
    paragraph(text)

paragraph('Anexo A — catálogo dos 60 jogos', 'Heading1', True)
paragraph('Lista acordada com o cliente. Categorias e demais metadados refletem o JSON atual; os dados complementares são preliminares.')
table(['Nº', 'Jogo', 'Categoria principal'], [[i + 1, g['name'], g['category']] for i, g in enumerate(games)], [500, 5700, 3100])
paragraph('Anexo B — referências de videogames', 'Heading1', True)
table(['Nº', 'Franquia', 'Referência e afinidades'], [[i + 1, v['franchise'], v['title'] + ' — ' + ', '.join(v['tags'])] for i, v in enumerate(videos)], [500, 2400, 6400])
paragraph('Anexo C — lojas fictícias', 'Heading1')
for i, store in enumerate(stores, 1):
    paragraph(f"{i}. {store['name']} — loja fictícia, sem domínio ou checkout comercial.")

styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/><w:color w:val="243A40"/><w:lang w:val="pt-BR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="130" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'''
definitions = [('Normal',22,'243A40',False),('Title',64,'0B2B36',True),('Subtitle',28,'687C73',False),('Lead',26,'B67B1F',False),('Heading1',34,'0B2B36',True),('Heading2',27,'348577',True),('Code',19,'0B2B36',False),('Notice',22,'916826',True),('Caption',20,'687C73',False)]
for name, size, color, bold in definitions:
    props = ('<w:keepNext/>' if name.startswith('Heading') else '') + ('<w:shd w:fill="F0F3EC"/>' if name == 'Code' else '')
    font = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>' if name == 'Code' else ''
    styles += f'<w:style w:type="paragraph" w:styleId="{name}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/><w:pPr>{props}</w:pPr><w:rPr>{font}<w:sz w:val="{size}"/><w:color w:val="{color}"/>{"<w:b/>" if bold else ""}</w:rPr></w:style>'
styles += '</w:styles>'
styles = styles.replace('<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:basedOn w:val="Normal"/>','<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>')
document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>{''.join(parts)}<w:sectPr><w:footerReference w:type="default" r:id="rFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="500" w:footer="500"/></w:sectPr></w:body></w:document>'''
rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
rels += ''.join(f'<Relationship Id="rImage{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>' for i, (name, _) in enumerate(images, 1)) + '</Relationships>'
footer = f'<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr><w:r><w:rPr><w:sz w:val="17"/><w:color w:val="74857B"/></w:rPr><w:t>BoardRadar • POC demonstrativa • </w:t></w:r><w:fldSimple w:instr="PAGE"/></w:p></w:ftr>'
content_types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>'
root_rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rDocument" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, value in {'[Content_Types].xml':content_types,'_rels/.rels':root_rels,'word/document.xml':document,'word/styles.xml':styles,'word/_rels/document.xml.rels':rels,'word/footer1.xml':footer}.items():
        ElementTree.fromstring(value)
        archive.writestr(name, value.encode('utf-8'))
    for name, data in images:
        archive.writestr('word/media/' + name, data)
with zipfile.ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
    root = ElementTree.fromstring(archive.read('word/document.xml'))
    text = ' '.join(t.text or '' for t in root.iter(f'{{{W}}}t'))
    for expected in ['Python', 'npm start', 'Pokémon', 'XCOM', 'metadados', '17 testes']:
        assert expected in text, expected
print(f'DOCX gerado e validado: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes; {len(images)} imagens)')
