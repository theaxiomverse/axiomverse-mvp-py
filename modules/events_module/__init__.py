# modules/events_module/__init__.py
from .event_emitter import EventEmitter
from .event_emitter_interface import EventEmitterInterface

__all__ = ['EventEmitter', 'EventEmitterInterface']