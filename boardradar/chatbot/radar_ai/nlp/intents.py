import re


def classify(text):
    if re.fullmatch(r'(?:recomecar|reiniciar|resetar|limpar tudo|limpar|zerar conversa)[!. ]*',text):return 'reset'
    if re.search(r'\b(?:comprar|checkout|lojas? reais?)\b',text):return 'commercial'
    if re.fullmatch(r'(?:oi|ola|opa|bom dia|boa tarde|boa noite|e ai)[!?. ]*',text):return 'greeting'
    if re.fullmatch(r'(?:obrigad[oa]|valeu|show|perfeito)(?: (?:pela ajuda|pelas sugestoes))?[!?. ]*',text):return 'thanks'
    if re.search(r'\b(?:regra|regras|permitid[oa]|posso|como jogar)\b',text):return 'rule'
    if re.search(r'\b(?:edicao|edicoes|expansao|idioma|sku)\b',text):return 'edition'
    if re.search(r'\b(?:compare|comparar|comparacao|versus|vs)\b|diferenca entre',text):return 'comparison'
    if re.search(r'\b(?:oferta|ofertas|estoque|preco|precos|custa)\b',text) and not re.search(r'\b(?:recomen\w*|indic\w*|sug\w*|quero|tenho|ate|orcamento)\b',text):return 'offer'
    if re.search(r'por ?que|qual (?:desses|deles)|fale mais',text):return 'explanation'
    if re.search(r'\b(?:fale|conte|explique|explica|sobre)|como (?:funciona|joga)|(?:esse|este) jogo funciona|bom para iniciantes',text):return 'information'
    if re.search(r'\b(?:recomen\w*|indic\w*|sug\w*|quero|preciso|parecido|gosto|curto)\b',text):return 'recommendation'
    return 'unknown'
