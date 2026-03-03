import logging
import os
from typing import Dict, List, Tuple, Optional

from Registry import Registry

from .interfaces import RegistryInterface


logger = logging.getLogger(__name__)


class OfflineRegistry(RegistryInterface):
    """
    Реализация RegistryInterface для работы с одним офлайн-файлом
    реестра Windows (отдельным кустом: SYSTEM, SOFTWARE и т.д.).
    """

    def __init__(self, file_path: str):
        """
        Инициализирует объект работы с файлом куста реестра.

        """
        self.file_path: str = file_path
        self.reg: Optional[Registry.Registry] = None
        self.root = None
        self.root_name: str = "ERROR"

        try:
            self.reg = Registry.Registry(file_path)
            self.root = self.reg.root()
            self.root_name = os.path.basename(file_path)

            logger.info("Успешно загружен файл реестра: %s", self.root_name)

        except Exception as exc:
            logger.error(
                "Не удалось открыть файл реестра %s: %s",
                file_path,
                exc,
            )
            self.root = None
            self.root_name = "ERROR"

    def get_root_keys(self) -> List[str]:
        """
        Возвращает список подразделов корня текущего куста.
        """
        return self.get_subkeys("")

    def _get_key_by_path(self, path: str):
        """
        Возвращает объект ключа по относительному пути внутри куста.

        """
        if not self.root or not self.reg:
            return None

        normalized_path = path.strip("\\")

        if not normalized_path:
            return self.root

        try:
            return self.reg.open(normalized_path)
        except Exception:
            return None

    def get_subkeys(self, path: str) -> List[str]:
        """
        Возвращает список имён подразделов для указанного пути.
        """
        key = self._get_key_by_path(path)
        if not key:
            return []

        try:
            return [subkey.name() for subkey in key.subkeys()]
        except Exception as exc:
            logger.error(
                "Ошибка чтения подразделов '%s' в файле %s: %s",
                path,
                self.root_name,
                exc,
            )
            return []

    def get_values(self, path: str) -> List[Tuple[str, str, str]]:
        """
        Возвращает список значений ключа в формате:
            (имя, тип, значение_в_строковом_виде)
        """
        key = self._get_key_by_path(path)
        if not key:
            return []

        results: List[Tuple[str, str, str]] = []

        try:
            for value in key.values():
                try:
                    val_name = value.name()
                    val_type = value.value_type_str()
                    val_data = value.value()

                    if isinstance(val_data, bytes):
                        hex_preview = " ".join(
                            f"{byte:02X}" for byte in val_data[:8]
                        )
                        val_data = f"(bytes: {len(val_data)}) {hex_preview}..."

                    results.append(
                        (val_name, val_type, str(val_data))
                    )

                except Exception:
                    continue

        except Exception as exc:
            logger.error(
                "Ошибка чтения значений '%s' в файле %s: %s",
                path,
                self.root_name,
                exc,
            )

        return results

    def close(self) -> None:
        """
        Метод для совместимости с интерфейсом.

        """
        self.reg = None
        self.root = None


class MultiHiveRegistry(RegistryInterface):
    """
    Обёртка над несколькими офлайн-кустами реестра.

    Позволяет работать с несколькими файлами реестра как с единой
    логической структурой.
    """

    def __init__(self, file_paths: List[str]):
        """
        Инициализирует несколько кустов реестра.

        """
        self.hives: Dict[str, OfflineRegistry] = {}

        for path in file_paths:
            try:
                hive = OfflineRegistry(path)
                if hive.root:
                    self.hives[hive.root_name] = hive
                else:
                    logger.warning(
                        "Файл %s не был добавлен (не удалось инициализировать).",
                        path,
                    )
            except Exception as exc:
                logger.error(
                    "Сбой инициализации файла %s: %s",
                    path,
                    exc,
                )

    def get_root_keys(self) -> List[str]:
        """
        Возвращает список имён загруженных кустов.
        """
        return list(self.hives.keys())

    def _split_path(self, path: str) -> Tuple[str, str]:
        """
        Разделяет путь вида:
            SYSTEM\\ControlSet001

        На:
            hive_name = "SYSTEM"
            sub_path = "ControlSet001"
        """
        parts = path.split("\\", 1)
        hive_name = parts[0]
        sub_path = parts[1] if len(parts) > 1 else ""
        return hive_name, sub_path

    def get_subkeys(self, path: str) -> List[str]:
        hive_name, sub_path = self._split_path(path)

        hive = self.hives.get(hive_name)
        if not hive:
            return []

        return hive.get_subkeys(sub_path)

    def get_values(self, path: str) -> List[Tuple[str, str, str]]:
        hive_name, sub_path = self._split_path(path)

        hive = self.hives.get(hive_name)
        if not hive:
            return []

        return hive.get_values(sub_path)

    def close(self) -> None:
        """
        Очищает список загруженных кустов.
        """
        for hive in self.hives.values():
            hive.close()
        self.hives.clear()