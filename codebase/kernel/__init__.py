"""
agent_unit_pie.kernel

Central kernel package for the Agent Unit PIE cognition system.

This package exposes the core runtime engines used across:

- observations
- events
- signals
- patterns
- relations
- timelines
- memory
- retrieval
- compression
- ontology
- simulations
- digital twins

The goal of this module is to provide a unified import surface
for all core cognition infrastructure.
"""

# VERSION

__version__ = "0.1.0"

# ONTOLOGY

try:
    from .ontology_registry import OntologyRegistry
except Exception:
    OntologyRegistry = None

# OBSERVATION PIPELINE

try:
    from .observation_pipeline import ObservationPipeline
except Exception:
    ObservationPipeline = None

# EVENTS

try:
    from .event_engine import EventEngine
except Exception:
    EventEngine = None

# SIGNALS

try:
    from .signals.signal_engine import SignalEngine
except Exception:
    SignalEngine = None

# PATTERNS

try:
    from .patterns.pattern_engine import PatternEngine
except Exception:
    PatternEngine = None

# RELATIONS

try:
    from .relations.relation_engine import RelationEngine
except Exception:
    RelationEngine = None

# TIMELINES

try:
    from .timeline.timeline_engine import TimelineEngine
except Exception:
    TimelineEngine = None

# MEMORY

try:
    from .memory.memory_router import MemoryRouter
except Exception:
    MemoryRouter = None

try:
    from .memory.working_memory_generator import WorkingMemoryGenerator
except Exception:
    WorkingMemoryGenerator = None

try:
    from .memory.episodic_memory import EpisodicMemory
except Exception:
    EpisodicMemory = None

try:
    from .memory.semantic_memory import SemanticMemory
except Exception:
    SemanticMemory = None

try:
    from .memory.pattern_memory import PatternMemory
except Exception:
    PatternMemory = None

# RETRIEVAL

try:
    from .retrieval.retrieval_engine import RetrievalEngine
except Exception:
    RetrievalEngine = None

try:
    from .retrieval.unit_retriever import UnitRetriever
except Exception:
    UnitRetriever = None

try:
    from .retrieval.pattern_retriever import PatternRetriever
except Exception:
    PatternRetriever = None

try:
    from .retrieval.timeline_retriever import TimelineRetriever
except Exception:
    TimelineRetriever = None

try:
    from .retrieval.relation_retriever import RelationRetriever
except Exception:
    RelationRetriever = None

try:
    from .retrieval.semantic_retriever import SemanticRetriever
except Exception:
    SemanticRetriever = None

# COMPRESSION

try:
    from .compression_engine import CompressionEngine
except Exception:
    CompressionEngine = None

# UNIT REGISTRY

try:
    from .unit_registry import UnitRegistry
except Exception:
    UnitRegistry = None

# GLOBAL EXPORTS

__all__ = [

    # core
    "OntologyRegistry",
    "ObservationPipeline",
    "EventEngine",

    # cognition
    "SignalEngine",
    "PatternEngine",
    "RelationEngine",
    "TimelineEngine",

    # memory
    "MemoryRouter",
    "WorkingMemoryGenerator",
    "EpisodicMemory",
    "SemanticMemory",
    "PatternMemory",

    # retrieval
    "RetrievalEngine",
    "UnitRetriever",
    "PatternRetriever",
    "TimelineRetriever",
    "RelationRetriever",
    "SemanticRetriever",

    # compression
    "CompressionEngine",

    # units
    "UnitRegistry",
]