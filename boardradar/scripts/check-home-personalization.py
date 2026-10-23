import json,uuid
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://127.0.0.1:3001'
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page()
 response=context.request.post(BASE+'/api/account',data={'action':'register','data':{'name':'Ana QA','email':'carousel-'+uuid.uuid4().hex[:8]+'@example.local','password':'Teste-de-fluxo-123!'}},headers={'Origin':BASE});assert response.ok
 user=response.json()['user']
 page.goto(BASE+'/onboarding');page.get_by_role('checkbox',name='Alien',exact=True).check();page.get_by_role('checkbox',name='Combate',exact=True).check();page.get_by_role('checkbox',name='Quero que o Radar use minhas escolhas',exact=False).check();page.get_by_role('button',name='Salvar minhas preferências').click();page.wait_for_url(BASE+'/')
 expect(page.locator('.personalized-section')).to_be_visible();assert page.evaluate("Object.keys(localStorage).some(k=>k.startsWith('boardradar-profile:'))")
 track=page.get_by_role('region',name='Jogos selecionados',exact=True);expect(track.locator('article')).to_have_count(8)
 assert track.evaluate("e=>getComputedStyle(e).scrollbarWidth")=="none"
 left=page.get_by_role('button',name='Anteriores: Jogos selecionados',exact=True).bounding_box();right=page.get_by_role('button',name='Próximos: Jogos selecionados',exact=True).bounding_box();box=track.bounding_box();assert left['x']<box['x'] and right['x']>box['x']+box['width']-10;assert abs(left['y']-right['y'])<2
 page.get_by_role('button',name='Próximos: Jogos selecionados',exact=True).click();page.wait_for_timeout(650);assert track.evaluate('(e)=>e.scrollLeft')>0
 page.reload();expect(page.locator('.personalized-section')).to_be_visible()
 page.goto(BASE+'/minha-conta?sec=perfil');expect(page.get_by_role('checkbox',name='Alien',exact=True)).to_be_checked();expect(page.get_by_role('checkbox',name='Combate',exact=True)).to_be_checked()
 page.goto(BASE+'/marketplace');expect(page.locator('.community-card').first).to_be_visible();text=page.locator('.community-listings .community-grid').inner_text();assert '[DEMO]' not in text;assert 'ANÚNCIO FICTÍCIO' not in text;assert 'Componentes:' not in text
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE+'/');expect(page.locator('.personalized-section')).to_be_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path=str(Path('.qa/workspace-captures/home-personalized-mobile.png')),full_page=True)
 browser.close()
 print('OK: localStorage, preferências após recarregar, recomendações temáticas, carrossel, cards compactos e celular')
