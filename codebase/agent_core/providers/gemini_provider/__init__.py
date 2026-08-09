"""Gemini provider package.

Public surface stays identical to the old single-file module:
`from agent_core.providers.gemini_provider import GeminiProvider`.

The GEMINI_* configuration flags are re-exported here because the A/B mode
benchmark monkey-patches them at runtime via setattr on this module; the
provider submodules read them dynamically from agent_core.config so those
patches take effect.
"""

from agent_core.config import (  # noqa: F401  (re-exported for runtime patching)
    GEMINI_IMPLICIT_CACHE,
    GEMINI_PRUNE_TOOLS_ON_CHAIN,
    GEMINI_SKIP_TOOLS_ON_CHAIN,
    GEMINI_STATELESS,
    GEMINI_STATELESS_CACHE,
    GEMINI_STATELESS_SKIP_SCHEMAS,
)
from agent_core.providers.gemini_provider.provider import GeminiProvider

__all__ = ["GeminiProvider"]