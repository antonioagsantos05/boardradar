import uuid,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://127.0.0.1:3001'
franchises=json.loads(Path('data/franchises.json').read_text(encoding='utf-8'))
alien=next(f['id'] for f in franchises if f['nome']=='Alien')
profile={'experience':'intermediate','styles':['combate'],'videogames':[alien],'references':'','budget':250,'consent':True}
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True);ctx=browser.new_context(viewport={'width':1280,'height':960});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def post(path,data,context=ctx):
  r=context.request.post(BASE+path,data=data,headers={'Origin':BASE});assert r.ok,(r.status,r.text());return r.json()
 user=post('/api/account',{'action':'register','data':{'name':'Ana Radar','email':'chat-'+uuid.uuid4().hex[:8]+'@example.local','password':'Teste-de-fluxo-123!'}})['user']
 post('/api/account',{'action':'save_profile','data':profile})
 first=post('/api/chat',{'message':'Usar meus gostos'});assert any('Porque você gosta de Alien' in r['reason'] for r in first['recommendations'])
 why=post('/api/chat',{'message':'Por que esses jogos?','state':first['state']});assert set(first['ids'])==set(why['ids'])
 comparison=post('/api/chat',{'message':'Compare esses jogos','state':why['state']});assert comparison['comparison']
 guest=browser.new_context();r=post('/api/chat',{'message':'Usar meus gostos','local_profile':profile},guest);assert not r['recommendations'];assert r['actions'][0]['href']=='/minha-conta?sec=perfil'
 page.goto(BASE+'/radar-ai');expect(page.get_by_text('Ana, vamos encontrar sua próxima partida?',exact=False)).to_be_visible()
 page.get_by_role('button',name='Usar meus gostos',exact=True).click();expect(page.locator('.chat-recommendation').first).to_be_visible();expect(page.get_by_text('Porque você gosta de Alien',exact=False).first).to_be_visible()
 page.get_by_role('button',name='Por que esses jogos?',exact=True).click();expect(page.get_by_role('button',name='Enviar mensagem')).to_be_disabled();expect(page.locator('.message.assistant')).to_have_count(3)
 page.get_by_label('Mensagem para Radar').fill('Quero anunciar um jogo');page.get_by_role('button',name='Enviar mensagem',exact=True).click();expect(page.get_by_role('link',name='Criar meu anúncio',exact=True)).to_have_attribute('href','/vender')
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
 page.screenshot(path='.qa/workspace-captures/chat-evolved-mobile.png',full_page=True)
 # A separate account can use only its own browser fallback when no server profile exists.
 localctx=browser.new_context();localuser=post('/api/account',{'action':'register','data':{'name':'Local Radar','email':'chat-local-'+uuid.uuid4().hex[:8]+'@example.local','password':'Teste-de-fluxo-123!'}},localctx)['user'];localpage=localctx.new_page();localpage.goto(BASE+'/');localpage.evaluate('(data)=>localStorage.setItem("boardradar-profile:"+data.id,JSON.stringify(data.profile))',{'id':localuser['id'],'profile':profile});localpage.goto(BASE+'/radar-ai');localpage.get_by_role('button',name='Usar meus gostos',exact=True).click();expect(localpage.get_by_text('Porque você gosta de Alien',exact=False).first).to_be_visible()
 browser.close();print('OK: perfil autenticado, localStorage, explicações, comparação, atalhos, isolamento entre contas e interface móvel')
