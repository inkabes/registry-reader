from abc import ABC, abstractmethod
from typing import List, Tuple, Any


class RegistryInterface(ABC):
    """
    Абстрактный интерфейс для работы с реестром.

    Интерфейс гарантирует единый контракт взаимодействия.
    """

    @abstractmethod
    def get_root_keys(self) -> List[str]:
        """
        Возвращает список доступных корневых разделов реестра.

        """
        raise NotImplementedError

    @abstractmethod
    def get_subkeys(self, path: str) -> List[str]:
        """
        Возвращает список имён подразделов для указанного пути реестра.

        """
        raise NotImplementedError

    @abstractmethod
    def get_values(self, path: str) -> List[Tuple[str, str, Any]]:
        """
        Возвращает список значений указанного ключа реестра.

        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Освобождает ресурсы (файлы, дескрипторы, соединения)
        """
        raise NotImplementedError