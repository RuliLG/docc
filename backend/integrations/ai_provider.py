from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def analyze_repository(
        self, repository_path: str, question: str, prompt: str
    ) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
