"""Bounded, portable conversation state. User state is never commercial authority."""
from datetime import datetime, timezone

TTL_SECONDS = 1800
VERSION = 1


def timestamp(now=None):
    return int((now or datetime.now(timezone.utc)).timestamp())


def validate_session(value):
    if not isinstance(value, dict) or set(value) != {'version', 'issued_at', 'expires_at'}:
        raise ValueError('Sessão inválida.')
    if type(value['version']) != int or value['version'] != VERSION or any(type(value[k]) != int for k in ('issued_at', 'expires_at')):
        raise ValueError('Sessão inválida.')
    if value['issued_at'] < 0 or value['expires_at'] - value['issued_at'] != TTL_SECONDS:
        raise ValueError('Prazo de sessão inválido.')
    return dict(value)


def begin(now=None):
    issued = timestamp(now)
    return {'version': VERSION, 'issued_at': issued, 'expires_at': issued + TTL_SECONDS}


def expired(session, now=None):
    current = timestamp(now)
    return session['issued_at'] > current or current >= session['expires_at']
