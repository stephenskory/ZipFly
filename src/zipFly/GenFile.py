import time
from typing import Generator, AsyncGenerator, Union

from . import consts
from .BaseFile import BaseFile


class GenFile(BaseFile):
    """DO NOT REUSE GenFile instances!"""
    def __init__(self, name: str, generator: Union[Generator[bytes, None, None], AsyncGenerator[bytes, None]], compression_method: int = consts.NO_COMPRESSION, modification_time: float = None, size: int = None, crc: int = None):
        if size and compression_method != consts.NO_COMPRESSION:
            raise ValueError("File size is allowed only with NO_COMPRESSION")

        super().__init__(name, compression_method)
        self._generator = generator
        self._predicted_size = size
        self._streamed_size = 0
        self._predicted_crc = crc  # used in byte offset mode
        self._modification_time = modification_time if modification_time else time.time()
        self._finished_streaming = False

    def __str__(self):
        return f"GenFile[name={self.name}]"

    def __repr__(self):
        return f"GenFile({self.name})"

    def _get_generator(self):
        return self._generator

    def _generate_file_data(self) -> Generator[bytes, None, None]:
        generator = self._get_generator()
        if isinstance(generator, Generator):
            for chunk in generator:
                self._streamed_size += len(chunk)
                yield chunk
        else:
            raise ValueError(f"generator must be of type Generator, not '{type(generator)}'")

        self._finish_and_validate()

    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:
        generator = self._get_generator()
        if isinstance(generator, AsyncGenerator):
            async for chunk in generator:
                self._streamed_size += len(chunk)
                yield chunk
        else:
            raise ValueError(f"generator must be of type AsyncGenerator, not '{type(generator)}'")

        self._finish_and_validate()

    def _finish_and_validate(self):
        self._finished_streaming = True
        if self._predicted_size is not None and self._predicted_size != self._streamed_size:
            raise RuntimeError(f"Size({self._predicted_size}) != streamed size({self._streamed_size})")

        if self._predicted_crc is not None and self._predicted_crc != self.get_crc():
            raise RuntimeError(f"Crc({self._predicted_crc}) != streamed crc({self.get_crc()})")

    @property
    def size(self) -> int:
        if not self._finished_streaming:
            if self.is_byte_offset_mode():
                if self._predicted_size is None:
                    raise RuntimeError("Archive size not known before streaming. Probably GenFile() is missing size attribute.")
                return self._predicted_size
        return self._streamed_size

    @property
    def modification_time(self) -> float:
        return self._modification_time

    def get_predicted_crc(self) -> int:
        if self.is_byte_offset_mode():
            if self._predicted_crc is None:
                raise RuntimeError("Crc not known before streaming. Probably GenFile() is missing crc attribute.")
            return self._predicted_crc
        raise ValueError("Attempted to get predicted crc without byte offset mode")
