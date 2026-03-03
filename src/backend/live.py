import logging
import winreg
from typing import List, Tuple, Optional

from .interfaces import RegistryInterface


logger = logging.getLogger(__name__)


class LiveRegistry(RegistryInterface):
    """
    Реализация интерфейса RegistryInterface для работы с живым
    системным реестром Windows.

    Класс предоставляет безопасное чтение подразделов и значений
    реестра с использованием контекстных менеджеров для корректного
    освобождения дескрипторов.
    """

    _ROOT_MAP = {
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_USERS": winreg.HKEY_USERS,
        "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
    }

    _TYPE_MAP = {
        winreg.REG_SZ: "REG_SZ",
        winreg.REG_DWORD: "REG_DWORD",
        winreg.REG_BINARY: "REG_BINARY",
        winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
        winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
        winreg.REG_QWORD: "REG_QWORD",
        winreg.REG_NONE: "REG_NONE",
        winreg.REG_LINK: "REG_LINK",
        winreg.REG_RESOURCE_LIST: "REG_RESOURCE_LIST",
        winreg.REG_FULL_RESOURCE_DESCRIPTOR: "REG_FULL_RESOURCE_DESCRIPTOR",
        winreg.REG_RESOURCE_REQUIREMENTS_LIST: "REG_RESOURCE_REQUIREMENTS_LIST",
    }

    def get_root_keys(self) -> List[str]:
        """
        Возвращает список поддерживаемых корневых разделов реестра.
        """
        return list(self._ROOT_MAP.keys())

    def _parse_path(self, full_path: str) -> Tuple[Optional[int], str]:
        """
        Разбирает полный путь реестра на корневой дескриптор и относительный путь.

        Если корневой раздел не распознан, возвращает (None, "").
        """
        if not full_path:
            logger.warning("Передан пустой путь реестра.")
            return None, ""

        parts = full_path.split("\\", 1)
        root_name = parts[0]

        root_hkey = self._ROOT_MAP.get(root_name)
        if root_hkey is None:
            logger.warning("Неизвестный корневой раздел реестра: %s", root_name)
            return None, ""

        sub_path = parts[1] if len(parts) > 1 else ""
        return root_hkey, sub_path

    def _type_to_str(self, type_id: int) -> str:
        """
        Преобразует числовой идентификатор типа реестра в строковое представление.
        Если тип неизвестен — возвращает 'UNKNOWN'.
        """
        return self._TYPE_MAP.get(type_id, "UNKNOWN")

    def _open_key(self, root_hkey: int, sub_path: str):
        """
        Открывает ключ реестра в режиме только для чтения.

        В случае ошибки логирует исключение и пробрасывает его дальше.
        """
        try:
            return winreg.OpenKey(root_hkey, sub_path, 0, winreg.KEY_READ)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 5:
                logger.warning("Нет доступа к ключу: %s\\%s", root_hkey, sub_path)
            else:
                logger.error(
                    "Ошибка открытия ключа реестра: root=%s, sub_path=%s, error=%s",
                    root_hkey,
                    sub_path,
                    exc,
                )
            raise

    def get_subkeys(self, path: str) -> List[str]:
        """
        Возвращает список имён подразделов указанного ключа реестра.

        В случае ошибки доступа или отсутствия ключа возвращает пустой список.
        """
        root_hkey, sub_path = self._parse_path(path)
        if root_hkey is None:
            return []

        try:
            with self._open_key(root_hkey, sub_path) as key:
                num_subkeys, _, _ = winreg.QueryInfoKey(key)

                subkeys: List[str] = []
                for index in range(num_subkeys):
                    try:
                        subkeys.append(winreg.EnumKey(key, index))
                    except OSError as exc:
                        # Возможна ситуация race condition,
                        # если ключ был удалён во время перечисления.
                        logger.debug(
                            "Ошибка при перечислении подраздела (index=%s): %s",
                            index,
                            exc,
                        )
                        continue

                return subkeys

        except OSError:
            return []

    def get_values(self, path: str) -> List[Tuple[str, str, str]]:
        """
        Возвращает список значений указанного ключа реестра.

        Формат результата:
            (имя_значения, тип_значения_строкой, значение_в_виде_строки)

        В случае ошибки возвращает пустой список.
        """
        root_hkey, sub_path = self._parse_path(path)
        if root_hkey is None:
            return []

        results: List[Tuple[str, str, str]] = []

        try:
            with self._open_key(root_hkey, sub_path) as key:
                _, num_values, _ = winreg.QueryInfoKey(key)

                for index in range(num_values):
                    try:
                        name, value, type_id = winreg.EnumValue(key, index)
                        results.append(
                            (name, self._type_to_str(type_id), str(value))
                        )
                    except OSError as exc:
                        logger.debug(
                            "Ошибка при перечислении значения (index=%s): %s",
                            index,
                            exc,
                        )
                        continue

        except OSError:
            return []

        return results

    def close(self):
        """
        Метод оставлен для совместимости с интерфейсом.
        Освобождение ресурсов выполняется автоматически
        через контекстные менеджеры.
        """
        pass