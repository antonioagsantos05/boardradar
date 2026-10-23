"""Run against port 3001 started with .qa/account-workspace-flow.sqlite3. Uses only QA accounts."""
import json,os,sqlite3,struct,time,uuid,zlib
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('BOARD_RADAR_TEST_URL','http://127.0.0.1:3001')
QA_DB=ROOT/'.qa/account-workspace-flow.sqlite3'
CAPTURES=ROOT/'.qa/workspace-captures';CAPTURES.mkdir(parents=True,exist_ok=True)
assert QA_DB.parent.resolve()==(ROOT/'.qa').resolve()
suffix=uuid.uuid4().hex[:8]
password='Teste-de-fluxo-123!'
def png():
 def chunk(name,data):return struct.pack('!I',len(data))+name+data+struct.pack('!I',zlib.crc32(name+data)&0xffffffff)
 width,height=180,120
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes([46,92,67])*width)*height))+chunk(b'IEND',b'')
def api(context,path,data):
 response=context.request.post(BASE+path,data=data,headers={'Origin':BASE})
 assert response.ok,(path,response.status,response.text())
 return response.json()
def screenshot(page,name):
 page.evaluate("document.activeElement?.blur();window.scrollTo({top:0,behavior:'instant'})")
 page.wait_for_timeout(150);page.screenshot(path=str(CAPTURES/name),full_page=True)
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 seller=browser.new_context(viewport={'width':1440,'height':1050});page=seller.new_page();errors=[]
 page.on('pageerror',lambda error:errors.append(str(error)))
 page.route('**/*',lambda r:r.abort() if r.request.resource_type=='image' and not r.request.url.startswith(BASE+'/api/listing-images') else r.continue_())
 page.goto(BASE+'/cadastro',wait_until='domcontentloaded')
 page.get_by_label('Como podemos te chamar?',exact=True).fill('Ana Fluxo')
 email='ana-'+suffix+'@example.local'
 page.get_by_label('E-mail',exact=True).fill(email);page.get_by_label('Senha',exact=True).fill(password)
 page.get_by_role('button',name='Criar minha conta',exact=True).click();page.wait_for_url('**/onboarding?next=%2F',wait_until='domcontentloaded')
 expect(page.get_by_role('heading',level=1)).to_contain_text('Ana, deixe o Radar conhecer você.')
 page.get_by_label('Minha experiência').select_option('intermediate')
 page.get_by_role('checkbox',name='Estratégia',exact=True).check();page.get_by_role('checkbox',name='Cooperativo',exact=True).check()
 for index in range(20):page.locator('.franchise-preferences input').nth(index).check()
 page.get_by_label('Orçamento habitual em reais').fill('250')
 page.get_by_role('checkbox',name='Quero que o Radar use minhas escolhas',exact=False).check();page.get_by_role('button',name='Salvar minhas preferências').click()
 page.wait_for_url(BASE+'/',wait_until='domcontentloaded')
 assert page.locator('.hero-tabletop-art svg').count()==1
 screenshot(page,'home-game-pieces-desktop.png')
 saved=seller.request.get(BASE+'/api/account').json()['profile'];assert len(saved['videogames'])==20;assert saved['styles']==['estratégia','cooperativo'];assert saved['budget']==250
 page.goto(BASE+'/minha-conta?sec=perfil',wait_until='domcontentloaded');expect(page.get_by_role('checkbox',name='Estratégia',exact=True)).to_be_checked();expect(page.locator('.franchise-preferences input:checked')).to_have_count(20)
 menu=page.get_by_role('navigation',name='Seções da conta',exact=True)
 expect(menu.get_by_role('link',name='Wishlist',exact=True)).to_have_count(0);expect(menu.get_by_role('link')).to_have_count(8)
 page.reload(wait_until='domcontentloaded');expect(page.locator('.franchise-preferences input:checked')).to_have_count(20)
 print('OK: cadastro, home após salvar e 20 franquias persistidas',flush=True)
 page.goto(BASE+'/meus-anuncios',wait_until='domcontentloaded');expect(page.get_by_role('navigation',name='Seções da conta')).to_be_visible();page.get_by_role('link',name='Novo anúncio',exact=True).click()
 expect(page.get_by_role('heading',name='Jogo e edição',exact=True)).to_be_visible()
 page.get_by_label('Título do anúncio',exact=True).fill('Pandemic para novas partidas')
 page.get_by_label('Descrição do exemplar',exact=True).fill('Exemplar completo, guardado com cuidado e com todos os componentes.')
 page.get_by_role('button',name='Continuar',exact=True).click()
 page.get_by_role('button',name='Meu jogo está completo',exact=True).click();page.get_by_role('button',name='Não há defeitos aparentes',exact=True).click();page.get_by_role('button',name='Continuar',exact=True).click()
 page.get_by_label('Preço em reais',exact=True).fill('150,50');page.get_by_label('Cidade e região',exact=True).fill('Campinas, SP');page.get_by_label('Como o jogo pode ser entregue?',exact=True).select_option('both');page.get_by_role('button',name='Salvar e adicionar fotos',exact=True).click()
 page.wait_for_url('**/vender?id=*',wait_until='domcontentloaded');expect(page.get_by_role('heading',name='Fotos',exact=True)).to_be_visible()
 expect(page.get_by_role('button',name='Revisar anúncio',exact=True)).to_be_disabled()
 photo={'name':'exemplar.png','mimeType':'image/png','buffer':png()}
 page.get_by_label('Adicionar foto ao anúncio',exact=True).set_input_files(photo);expect(page.locator('.listing-photo-grid img')).to_have_count(1)
 page.get_by_role('button',name='Remover foto',exact=False).click();expect(page.locator('.listing-photo-grid img')).to_have_count(0);expect(page.get_by_role('button',name='Revisar anúncio',exact=True)).to_be_disabled()
 page.get_by_label('Adicionar foto ao anúncio',exact=True).set_input_files(photo);expect(page.locator('.listing-photo-grid img')).to_have_count(1)
 screenshot(page,'sell-photos-desktop.png')
 page.get_by_role('button',name='Salvar rascunho e sair',exact=False).click();page.wait_for_url('**/meus-anuncios',wait_until='domcontentloaded')
 expect(page.locator('.seller-card')).to_have_count(1);page.get_by_role('button',name='Continuar anúncio',exact=False).click()
 expect(page.get_by_label('Título do anúncio',exact=True)).to_have_value('Pandemic para novas partidas')
 page.get_by_label('Título do anúncio',exact=True).fill('Pandemic completo e bem cuidado')
 page.get_by_role('button',name='Continuar',exact=True).click();expect(page.get_by_label('Componentes e itens ausentes',exact=True)).to_have_value('Completo, sem peças faltando.');page.get_by_role('button',name='Continuar',exact=True).click();expect(page.get_by_label('Preço em reais',exact=True)).to_have_value('150.50');page.get_by_role('button',name='Salvar e adicionar fotos',exact=True).click();expect(page.locator('.listing-photo-grid img')).to_have_count(1)
 page.get_by_role('button',name='Revisar anúncio',exact=True).click();expect(page.get_by_role('button',name='Enviar para análise',exact=False)).to_be_disabled();page.get_by_role('checkbox',name='Revisei o anúncio',exact=False).check();page.get_by_role('button',name='Enviar para análise',exact=False).click();page.wait_for_url('**/meus-anuncios?enviado=1',wait_until='domcontentloaded');expect(page.locator('.seller-card .status-pending_review')).to_have_count(1)
 listing=seller.request.get(BASE+'/api/listings').json()['listings'][0];listing_id=listing['id'];assert listing['price_cents']==15050
 outsider=browser.new_context();assert outsider.request.get(BASE+'/api/listings?view=detail&id='+listing_id).status==404
 moderator=browser.new_context();mod=api(moderator,'/api/account',{'action':'register','data':{'name':'Moderação QA','email':'mod-'+suffix+'@example.local','password':password}})
 with sqlite3.connect(QA_DB) as db:db.execute("INSERT OR IGNORE INTO user_roles VALUES (?,'moderator')",(mod['user']['id'],))
 api(moderator,'/api/listings',{'action':'approve','data':{'id':listing_id,'revision':listing['revision'],'reason':'Exemplar conferido em teste isolado.','edition_confirmed':True}})
 assert outsider.request.get(BASE+'/api/listings?view=detail&id='+listing_id).ok
 public=outsider.request.get(BASE+'/api/listings?view=public&q=Pandemic').json();assert listing_id in [item['id'] for item in public['listings']]
 page.goto(BASE+'/meus-anuncios',wait_until='domcontentloaded');expect(page.locator('.seller-card .status-active')).to_have_count(1);screenshot(page,'listings-desktop.png')
 print('OK: rascunho, retomada, edição, fotos, aceite, revisão e anúncio aprovado público',flush=True)
 buyer=browser.new_context();api(buyer,'/api/account',{'action':'register','data':{'name':'Comprador QA','email':'buyer-'+suffix+'@example.local','password':password}});api(buyer,'/api/listings',{'action':'inquire','data':{'id':listing_id,'message':'Olá! O jogo ainda está disponível?'}})
 page.goto(BASE+'/mensagens',wait_until='domcontentloaded');expect(page.get_by_role('navigation',name='Seções da conta')).to_be_visible();expect(page.locator('.inbox-bubble')).to_have_count(1);page.get_by_label('Sua mensagem',exact=True).fill('Olá! Sim, está disponível.');page.get_by_role('button',name='Enviar',exact=True).click();expect(page.locator('.inbox-bubble')).to_have_count(2);assert len(buyer.request.get(BASE+'/api/listings?view=inbox').json()['conversations'][0]['messages'])==2;screenshot(page,'conversations-desktop.png')
 for width in [390,320]:
  page.set_viewport_size({'width':width,'height':844})
  for route in ['/','/minha-conta?sec=perfil','/meus-anuncios','/mensagens','/vender']:
   page.goto(BASE+route,wait_until='domcontentloaded')
   if route!='/':expect(page.get_by_role('navigation',name='Seções da conta')).to_be_visible()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route)
   if width==390:screenshot(page,route.split('?')[0].strip('/').replace('/','-')+'-mobile.png' if route!='/' else 'home-mobile.png')
 page.set_viewport_size({'width':1440,'height':1050});page.goto(BASE+'/meus-anuncios',wait_until='domcontentloaded')
 for label,expected in [('Pausar','paused'),('Reativar','active'),('Reservar','reserved'),('Disponibilizar','active')]:
  page.get_by_role('button',name=label,exact=True).click();expect(page.locator('.seller-card .status-'+expected)).to_have_count(1)
  assert outsider.request.get(BASE+'/api/listings?view=detail&id='+listing_id).status==(200 if expected=='active' else 404)
 page.get_by_role('button',name='Marcar vendido',exact=True).click();page.get_by_role('dialog').get_by_role('button',name='Marcar vendido',exact=True).click();expect(page.locator('.seller-card .status-sold')).to_have_count(1);assert outsider.request.get(BASE+'/api/listings?view=detail&id='+listing_id).status==404
 payload={key:listing[key] for key in ['edition_id','description','condition','language','price_cents','region','components','delivery','defects']};payload.update(title='Outro exemplar para anunciar',negotiable=False,sealed=False)
 api(seller,'/api/listings',{'action':'create','data':payload});page.reload(wait_until='domcontentloaded');draft=page.locator('.seller-card').filter(has=page.locator('.status-draft'));draft.get_by_role('button',name='Remover',exact=True).click();page.get_by_role('dialog').get_by_role('button',name='Remover anúncio',exact=True).click();expect(page.locator('.seller-card .status-removed')).to_have_count(1)
 api(seller,'/api/account',{'action':'logout','data':{}});page.goto(BASE+'/entrar',wait_until='domcontentloaded');page.get_by_label('E-mail',exact=True).fill(email);page.get_by_label('Senha',exact=True).fill(password);page.get_by_role('button',name='Entrar na minha conta',exact=True).click();page.wait_for_url('**/minha-conta',wait_until='domcontentloaded');page.goto(BASE+'/minha-conta?sec=perfil',wait_until='domcontentloaded');expect(page.locator('.franchise-preferences input:checked')).to_have_count(20)
 assert not errors,errors
 browser.close();print('OK: conversas reais entre contas QA, menu compartilhado, ciclo de status, exclusão, novo login e celular. Nenhum dado de usuário real foi alterado.',flush=True)
