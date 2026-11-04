"""Presentation-only EN/PL catalogue. IDs, plans and game state are never rewritten."""
import json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CATALOG=json.loads((ROOT/'content/i18n/catalog.json').read_text(encoding='utf-8'))
PAIRS=CATALOG['pairs'];REVERSE={v:k for k,v in PAIRS.items()};PATTERNS=[(re.compile(p),r) for p,r in CATALOG['patterns']]
_language='en';_missing=set()
class OriginalText(str):
 def __add__(self,other):return OriginalText(str(self)+translate(other))
 def __radd__(self,other):return OriginalText(translate(other)+str(self))
 def __getitem__(self,key):return OriginalText(super().__getitem__(key))

def initialize():
 global _language
 candidate=os.getenv('CHESS_CORP_LANGUAGE','en')
 if sys.platform=='emscripten':
  try:
   import platform
   candidate=str(platform.window.chessCorpGetLanguage())
  except (AttributeError,TypeError):pass
 _language=candidate if candidate in ('en','pl') else 'en'
 return _language

def language():return _language

def set_language(value):
 global _language
 if value not in ('en','pl'):return
 _language=value
 if sys.platform=='emscripten':
  try:
   import platform
   platform.window.chessCorpSetLanguage(value)
  except (AttributeError,TypeError):pass

def translate(value,lang=None,_depth=0):
 if isinstance(value,OriginalText):return value
 value=str(value);lang=lang or _language
 if value.startswith(('[PL original]','[EN oryginał]','[Original /')):return value
 for marker in ('[PL original]','[EN oryginał]','[Original /'):
  if marker in value:
   prefix,tail=value.split(marker,1);return translate(prefix,lang,_depth+1)+marker+tail
 if value.strip() and value!=value.strip():
  left=len(value)-len(value.lstrip());right=len(value.rstrip())
  return value[:left]+translate(value.strip(),lang,_depth)+value[right:]
 if lang=='pl':return REVERSE.get(value,value)
 if value in PAIRS:return PAIRS[value]
 if _depth<5:
  for pattern,replacement in PATTERNS:
   match=pattern.fullmatch(value)
   if match:
    return re.sub(r'\$(\d+)',lambda m:translate(match.group(int(m[1])),'en',_depth+1),replacement)
 if any(c in value for c in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ') and len(_missing)<200:_missing.add(value[:220])
 return value

def original(text,source_language):
 if source_language==_language:return OriginalText(text)
 if source_language in ('en','pl'):
  return OriginalText('['+source_language.upper()+(' original] ' if _language=='en' else ' oryginał] ')+str(text))
 return OriginalText('[Original / language unknown] '+str(text))

def missing():return sorted(_missing)

def puzzle_text(puzzle,source_language):
 if _language=='pl':
  from game.director_contract import puzzle_question
  return original(puzzle['flavor'],source_language)+' '+puzzle_question({**puzzle,'flavor':''}).strip()
 a,b=puzzle['a'],puzzle['b'];kind=puzzle['template']
 question=f'What is {a} + {b}?' if kind=='SUM' else f'What is {a} - {b}?' if kind=='DIFFERENCE' else f'What is the next number: {a}, {a+b}, {a+2*b}, ? (constant step).'
 return original(puzzle['flavor'],source_language)+' '+question

def localize_plan(plan,lang):
 # Used ONLY when constructing a mock result; never rewrites an accepted AI plan.
 if isinstance(plan,dict):return {k:localize_plan(v,lang) if k in ('jobs','decisions','actions','create_quest','quest','place_objects','place_object','puzzle') else translate(v,lang) if k in ('title','description','objective','completion_message','label','item_label','goal','summary','text','flavor') and isinstance(v,str) else v for k,v in plan.items()}
 if isinstance(plan,list):return [localize_plan(v,lang) for v in plan]
 return plan
