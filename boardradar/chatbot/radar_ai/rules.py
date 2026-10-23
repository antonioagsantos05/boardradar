"""Prioritized rules, dependency validation, explicit exceptions and conflict tracing."""
from dataclasses import dataclass,field
from enum import IntEnum
from typing import Callable


class Layer(IntEnum):
    SECURITY=10
    BUSINESS=20
    USER_CONSTRAINT=30
    COMPATIBILITY=40
    PREFERENCE=50
    RANKING=60


class RuleConfigurationError(ValueError):pass
class RuleConflict(ValueError):pass


@dataclass(frozen=True)
class Effect:
    key:str
    value:object


@dataclass(frozen=True)
class ExceptionCase:
    id:str
    condition:Callable


@dataclass(frozen=True)
class Rule:
    id:str
    version:str
    layer:Layer
    priority:int
    condition:Callable
    action:Callable
    depends_on:tuple=()
    exceptions:tuple=()
    conflicts_with:tuple=()
    description:str=''


@dataclass
class Decision:
    facts:dict=field(default_factory=dict)
    rejections:list=field(default_factory=list)
    trace:list=field(default_factory=list)

    @property
    def eligible(self):return not self.rejections


class RuleEngine:
    def __init__(self,rules):
        ids=[r.id for r in rules]
        if len(set(ids))!=len(ids):raise RuleConfigurationError('Duplicate rule ID')
        self.rules={r.id:r for r in rules}
        for rule in rules:
            if not rule.id or not rule.version:raise RuleConfigurationError('Rule ID/version required')
            if rule.exceptions and rule.layer in (Layer.SECURITY,Layer.BUSINESS,Layer.COMPATIBILITY):raise RuleConfigurationError('Critical rules cannot be exempted')
            if len({e.id for e in rule.exceptions})!=len(rule.exceptions):raise RuleConfigurationError('Duplicate exception ID')
            for dependency in rule.depends_on:
                if dependency not in self.rules:raise RuleConfigurationError('Missing dependency: '+dependency)
                if self.rules[dependency].layer>rule.layer:raise RuleConfigurationError('Dependency violates hierarchy')
            if any(c not in self.rules for c in rule.conflicts_with):raise RuleConfigurationError('Unknown conflict rule')
        self.ordered=[]
        visiting=set();done=set()
        def visit(identifier):
            if identifier in visiting:raise RuleConfigurationError('Cyclic rule dependencies')
            if identifier in done:return
            visiting.add(identifier)
            for dep in self.rules[identifier].depends_on:visit(dep)
            visiting.remove(identifier);done.add(identifier);self.ordered.append(self.rules[identifier])
        for rule in sorted(rules,key=lambda r:(r.layer,r.priority,r.id)):visit(rule.id)

    def evaluate(self,context):
        result=Decision();statuses={};applied=set();writers={}
        for rule in self.ordered:
            event={'rule_id':rule.id,'version':rule.version,'layer':rule.layer.name,'priority':rule.priority}
            try:
                if any(statuses.get(d) in ('rejected','error','conflict','blocked') for d in rule.depends_on):
                    event.update(status='blocked',reason='dependency_failed')
                elif rule.layer==Layer.RANKING and result.rejections:
                    event.update(status='blocked',reason='ineligible_candidate')
                else:
                    exception=next((e for e in rule.exceptions if e.condition(context,result)),None)
                    if exception:
                        event.update(status='exempt',reason=exception.id)
                    elif not rule.condition(context,result):
                        event['status']='passed'
                    else:
                        conflict=next((i for i in applied if i in rule.conflicts_with or rule.id in self.rules[i].conflicts_with),None)
                        if conflict:raise RuleConflict('mutually_exclusive_rules')
                        effects=tuple(rule.action(context,result))
                        if any(not isinstance(effect,Effect) for effect in effects):raise TypeError('Invalid action effect')
                        proposed={}
                        for effect in effects:
                            if effect.key!='reject':
                                if effect.key in proposed and proposed[effect.key]!=effect.value:raise RuleConflict('conflicting_effects')
                                if effect.key in writers and result.facts[effect.key]!=effect.value:raise RuleConflict('conflicting_assignment')
                                proposed[effect.key]=effect.value
                        # Commit effects atomically only after all conflicts are checked.
                        for effect in effects:
                            if effect.key=='reject':result.rejections.append({'rule_id':rule.id,'reason':str(effect.value)})
                            else:result.facts[effect.key]=effect.value;writers[effect.key]=rule.id
                        event['status']='rejected' if any(e.key=='reject' for e in effects) else 'applied'
                        applied.add(rule.id)
            except RuleConflict:
                result.rejections.append({'rule_id':rule.id,'reason':'rule_conflict'})
                event.update(status='conflict',reason='rule_conflict')
            except Exception as error:
                # No fallback may produce commercial results after an evaluation error.
                result.rejections.append({'rule_id':rule.id,'reason':'rule_execution_error'})
                event.update(status='error',reason=type(error).__name__)
            statuses[rule.id]=event['status'];result.trace.append(event)
        return result

    def describe(self):
        return [{'id':r.id,'version':r.version,'layer':r.layer.name,'priority':r.priority,'depends_on':list(r.depends_on),'exceptions':[e.id for e in r.exceptions],'conflicts_with':list(r.conflicts_with),'description':r.description} for r in self.ordered]


def reject(reason):
    return lambda _context,_decision:(Effect('reject',reason),)
