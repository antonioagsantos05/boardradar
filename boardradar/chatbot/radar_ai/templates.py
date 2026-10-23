"""Small parameterized responses; no generated or inferred catalogue claims."""
TEMPLATES = {
    'expired': 'O contexto desta conversa expirou após 30 minutos. Vamos reconstruir suas preferências: quantas pessoas vão jogar e qual é o orçamento?',
    'compare_missing': 'Qual outro jogo você quer comparar com {name}?',
    'comparison': 'Comparei {names} usando os atributos cadastrados. Os metadados são preliminares. Interação, variabilidade, curva de aprendizado e estratégia detalhada ainda não estão cadastradas.',
    'edition': 'Estas são as edições cadastradas de {names}. Idioma e produto precisam de confirmação. Edições diferentes não são tratadas como equivalentes.',
    'offer': 'Ofertas DEMO recentes de {names}, separadas por edição. Valores em reais, sem frete. Lojas e preços são fictícios; a compatibilidade com suas preferências aparece separadamente.',
    'media': 'Usei relações editoriais de {names}. São analogias de temática ou mecânica, com revisão pendente; não comprovam adaptação oficial nem experiência equivalente.',
}


def render(key, **values):
    return TEMPLATES[key].format(**values)
