import re
import unicodedata


def normalize(value):
    text=''.join(c for c in unicodedata.normalize('NFD',value) if unicodedata.category(c) not in ('Mn','Cf'))
    return re.sub(r'\s+',' ',text.lower().replace('’',"'").replace('‘',"'").replace('–','-').replace('−','-')).strip()


def name_key(value):return re.sub(r'[^a-z0-9]+',' ',normalize(value)).strip()


def contains(text,word):
    return re.search(r'(?<!\w)'+re.escape(normalize(word))+r'(?!\w)',text)


UNITS={'zero':0,'um':1,'uma':1,'dois':2,'duas':2,'tres':3,'quatro':4,'cinco':5,'seis':6,'sete':7,'oito':8,'nove':9,'dez':10,'onze':11,'doze':12,'treze':13,'catorze':14,'quatorze':14,'quinze':15,'dezesseis':16,'dezasseis':16,'dezessete':17,'dezoito':18,'dezenove':19}
TENS={'vinte':20,'trinta':30,'quarenta':40,'cinquenta':50,'sessenta':60,'setenta':70,'oitenta':80,'noventa':90}
HUNDREDS={'cem':100,'cento':100,'duzentos':200,'duzentas':200,'trezentos':300,'trezentas':300,'quatrocentos':400,'quinhentos':500,'seiscentos':600,'setecentos':700,'oitocentos':800,'novecentos':900}
VALUES={**UNITS,**TENS,**HUNDREDS,'mil':1000}
_WORD='(?:'+'|'.join(sorted(VALUES,key=len,reverse=True))+')'
_PHRASE=re.compile(r'\b'+_WORD+r'(?:\s+(?:e\s+)?'+_WORD+r')*\b')


def numeric_text(text):
    def convert(match):
        total=group=0
        for word in match.group().split():
            if word=='e':continue
            if word=='mil':total+=(group or 1)*1000;group=0
            else:group+=VALUES[word]
        return str(total+group)
    return _PHRASE.sub(convert,text)
