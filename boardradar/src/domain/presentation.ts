export function displayText(value: string) {
  if (/anúncio fictício|componentes fictícios|dados genéricos de teste/i.test(value)) return '';
  return value.replace(/\s*[—–-]\s*anúncio de exemplo/gi, '').replace(/\[DEMO\]\s*/gi, '').replace(/\s*[—–-]\s*edição de referência\s*/gi, ' ').replace(/edição de referência/gi, 'Edição base').replace(/\s*\((?:simulad[oa]|simulação|hipotética para POC)\)/gi, '').replace(/Vendedor Demo /gi, 'Vendedor ').trim();
}
