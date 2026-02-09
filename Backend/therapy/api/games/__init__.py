# Import plugins so they auto-register in registry
from therapy.api.games.plugins.ja import JointAttentionGame  # noqa: F401
from therapy.api.games.plugins.matching import MatchingGame  # noqa: F401
from therapy.api.games.plugins.object_discovery import ObjectDiscoveryGame  # noqa: F401
from therapy.api.games.plugins.problem_solving import ProblemSolvingGame  # noqa: F401
from therapy.api.games.plugins.memory_match import MemoryMatchGame  # noqa: F401
