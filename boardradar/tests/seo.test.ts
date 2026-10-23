import test from 'node:test';
import assert from 'node:assert/strict';
import {siteSettings,seoDescription} from '../src/domain/seo';
test('local SEO never enables indexing without a configured public HTTPS origin',()=>{
 for(const value of ['', 'http://127.0.0.1:3000','https://localhost','http://boardradar.example'])assert.equal(siteSettings(value).canIndex,false);
 assert.equal(siteSettings('https://boardradar.example').canIndex,true);
});
test('SEO origin rejects credentials, unsupported schemes and paths',()=>{
 for(const value of ['javascript:alert(1)','https://user:pass@example.com','https://example.com/path','https://example.com/?q=secret','https://example.com/#fragment'])assert.throws(()=>siteSettings(value));
});
test('description uses short plain text without inventing game data',()=>{
 assert.equal(seoDescription('<p>Jogo   cooperativo.</p>'),'Jogo cooperativo.');assert.equal(seoDescription('a'.repeat(200)).length,160);
});
