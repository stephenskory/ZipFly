import time
from abc import ABC, abstractmethod
from typing import Generator, AsyncGenerator

from . import consts
from .Compressor import Compressor


class BaseFile(ABC):
    def __init__(self, compression_method: int):
        self.__used = False
        self.__compressed_size = 0
        self.__offset = 0  # Offset to local file header
        self.__crc = 0
        self.__compression_method = compression_method or consts.NO_COMPRESSION
        self.__flags = 0b00001000  # flag about using data descriptor is always on

    def __str__(self):
        return f"FILE[{self.name}]"

    def generate_processed_file_data(self) -> Generator[bytes, None, None]:
        if self.__used:
            raise KeyError("ERROR: This file has already been used for streaming")
        self.__used = True
        compressor = Compressor(self)

        """
        Generates compressed file data
        """
        for chunk in self._generate_file_data():
            chunk = compressor.process(chunk)
            if len(chunk) > 0:
                yield chunk
            chunk = compressor.tail()
            if len(chunk) > 0:
                yield chunk

    async def async_generate_processed_file_data(self) -> AsyncGenerator[bytes, None]:
        if self.__used:
            raise KeyError("ERROR: This file has already been used for streaming")
        self.__used = True

        compressor = Compressor(self)

        """
        Generates compressed file data
        """
        async for chunk in self._async_generate_file_data():
            chunk = compressor.process(chunk)
            if len(chunk) > 0:
                yield chunk
            chunk = compressor.tail()
            if len(chunk) > 0:
                yield chunk

    def get_mod_time(self) -> int:
        # Extract hours, minutes, and seconds from the modification time
        t = time.localtime(self.modification_time)
        return ((t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)) & 0xFFFF

    def get_mod_date(self) -> int:
        # Extract year, month, and day from the modification time
        t = time.localtime(self.modification_time)
        year = t.tm_year - 1980  # ZIP format years start from 1980
        return ((year << 9) | (t.tm_mon << 5) | t.tm_mday) & 0xFFFF

    def set_offset(self, new_offset) -> None:
        self.__offset = new_offset

    def get_offset(self) -> int:
        return self.__offset

    def get_compressed_size(self) -> int:
        return self.__compressed_size

    def add_compressed_size(self, value) -> None:
        self.__compressed_size += value

    def set_compressed_size(self, new_value) -> None:
        self.__compressed_size = new_value

    def get_crc(self) -> int:
        return self.__crc

    def set_crc(self, new_crc) -> None:
        self.__crc = new_crc

    @property
    def file_path_bytes(self) -> bytes:
        try:
            return self.name.encode("ascii")
        except UnicodeError:
            self.__flags |= consts.UTF8_FLAG
            return self.name.encode("utf-8")

    @abstractmethod
    def _generate_file_data(self) -> Generator[bytes, None, None]:
        raise NotImplementedError

    @abstractmethod
    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:
        raise NotImplementedError

    @abstractmethod
    def set_file_name(self, new_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def calculate_crc(self) -> int:
        raise NotImplementedError

    @property
    def size(self) -> int:
        raise NotImplementedError

    @property
    def modification_time(self) -> float:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def flags(self) -> int:
        return self.__flags

    @property
    def compression_method(self) -> int:
        return self.__compression_method
