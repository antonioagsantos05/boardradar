from dataclasses import asdict,dataclass,field
from typing import Literal

Intent=Literal['recommendation','refinement','information','comparison','rule','edition','offer','explanation','greeting','thanks','reset','commercial','unknown','clarification']


@dataclass
class Entities:
    players:int|None=None
    max_price_cents:int|None=None
    duration_minutes:float|None=None
    max_complexity:int|None=None
    mode:str|None=None
    preferred_tags:list[str]=field(default_factory=list)
    excluded_tags:list[str]=field(default_factory=list)
    game_ids:list[str]=field(default_factory=list)
    edition_ids:list[str]=field(default_factory=list)
    videogame_ids:list[str]=field(default_factory=list)
    media_ids:list[str]=field(default_factory=list)
    excluded_game_ids:list[str]=field(default_factory=list)
    remove:list[str]=field(default_factory=list)


@dataclass
class Interpretation:
    intent:Intent='unknown'
    entities:Entities=field(default_factory=Entities)
    confidence:float=0.0
    missing_information:list[str]=field(default_factory=list)
    ambiguities:list[dict]=field(default_factory=list)
    errors:list[dict]=field(default_factory=list)
    cheaper:bool=False
    more:bool=False

    def public(self):
        return {**asdict(self),'version':'nlp-3.0','confidence_kind':'heuristic_not_calibrated'}
