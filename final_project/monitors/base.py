from abc import ABC, abstractmethod
from typing import Any, Dict

class Monitor(ABC):
    @abstractmethod
    def start(self):
        """Start the background monitoring process (if any)."""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop the background monitoring process."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Return the current aggregated state of the monitor."""
        pass
