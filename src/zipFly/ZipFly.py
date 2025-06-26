from typing import Generator, AsyncGenerator, Union

from . import consts
from .BaseFile import BaseFile
from .ZipBase import ZipBase
import copy
import types

def process_file_names(files) -> list[BaseFile]:
    """Renames duplicated file names"""
    seen_names = set()

    for file in files:
        # Split name
        base, ext = file.name.rsplit('.', 1) if '.' in file.name else (file.name, '')
        ext = f".{ext}" if ext else ""

        candidate = base
        counter = 0
        new_name = f"{candidate}{ext}"

        # Generate unique name
        while new_name in seen_names:
            counter += 1
            candidate = f"{base} ({counter})"
            new_name = f"{candidate}{ext}"

        # Set unique name and mark it as seen
        file.set_file_name(new_name)
        seen_names.add(new_name)

    return files


def deepcopy_skip_generators(obj_list):
    """
    Deep copies a list of objects, skipping any object entirely
    if it contains a generator or async generator as an attribute.
    """

    def has_generator(obj):
        for value in getattr(obj, '__dict__', {}).values():
            if isinstance(value, (types.GeneratorType, types.AsyncGeneratorType)):
                return True
        return False

    def custom_copy(obj, memo=None):
        if memo is None:
            memo = {}

        if isinstance(obj, dict):
            return {k: custom_copy(v, memo) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return type(obj)(custom_copy(item, memo) for item in obj)
        elif isinstance(obj, (int, float, str, bool, type(None))):  # Immutable types
            return obj
        elif isinstance(obj, (types.GeneratorType, types.AsyncGeneratorType)):  # Skip generators
            return obj
        elif hasattr(obj, '__dict__'):  # Handle custom objects
            if has_generator(obj):
                return obj  # or `return obj` to skip deepcopy but keep it in the list
            new_obj = copy.copy(obj)  # Shallow copy first
            for key, value in obj.__dict__.items():
                setattr(new_obj, key, custom_copy(value, memo))
            return new_obj
        else:
            return copy.deepcopy(obj, memo)  # Default deep copy

    return [custom_copy(obj) for obj in obj_list]

class ZipFly(ZipBase):

    def __init__(self, files: list[BaseFile]):
        processed_files = process_file_names(deepcopy_skip_generators(files))
        super().__init__(processed_files)

        self._LOCAL_FILE_HEADER_SIZE = 30
        self._DATA_DESCRIPTOR_SIZE = 24
        self._CENTRAL_DIR_HEADER_SIZE = 46
        self._ZIP64_EXTRA_FIELD_SIZE = 28
        self._ZIP64_END_OF_CDIR_RECORD_SIZE = 56
        self._ZIP64_END_OF_CDIR_LOCATOR_SIZE = 20
        self._END_OF_CDIR_RECORD_CD_RECORD_SIZE = 22

        self._remaining_offset = 0
        self.__used = False

    def was_used(self) -> bool:
        return self.__used

    def calculate_archive_size(self) -> int:
        """Calculates total archive size. Raises an error if it can't"""
        total_size = 0

        for file in self.files:
            total_size += self._calculate_file_size_in_archive(file)
            central_directory_header_size = self._CENTRAL_DIR_HEADER_SIZE + len(file.file_path_bytes) + self._ZIP64_EXTRA_FIELD_SIZE
            total_size += central_directory_header_size

        total_size += self._ZIP64_END_OF_CDIR_RECORD_SIZE
        total_size += self._ZIP64_END_OF_CDIR_LOCATOR_SIZE
        total_size += self._END_OF_CDIR_RECORD_CD_RECORD_SIZE

        return total_size

    def _calculate_file_size_in_archive(self, file: BaseFile):
        """Returns the size of: [local file header] + [file data] + [data descriptor]"""
        block_size = 0

        local_file_header_size = self._LOCAL_FILE_HEADER_SIZE + len(file.file_path_bytes)
        block_size += local_file_header_size
        block_size += file.size
        block_size += self._DATA_DESCRIPTOR_SIZE

        return block_size

    def _find_starting_file(self, byte_offset: int) -> Union[tuple[int, int], tuple[None, int]]:
        """This function is used in byte_offset mode. It finds the file in which byte offset is located.
        Returns:
            A tuple containing the index of the file and the offset within the file if found, otherwise tuple[None, remaining_offset].
        Raises:
            ValueError
        """
        if not byte_offset:  # skip if not using byte_offset mode
            return 0, 0

        if byte_offset > self.calculate_archive_size():
            raise ValueError("Byte offset > total archive size")

        running_offset = 0
        for index, file in enumerate(self.files):
            file_size_in_archive = self._calculate_file_size_in_archive(file)

            # We must set offset for files bcs the offset won't be handled by the usual parts of the code bcs we are skipping them later on
            file.set_offset(running_offset)

            if running_offset <= byte_offset < running_offset + file_size_in_archive:
                return index, byte_offset - running_offset

            # We must set both crc and compressed size for the files in the archive that we entirely "skip"
            file.set_crc(file.calculate_crc())
            file.set_compressed_size(file.size)

            if file.compression_method != consts.NO_COMPRESSION:
                raise ValueError("Byte offset is supported only for non compressed files")

            running_offset += file_size_in_archive

        return None, byte_offset - running_offset

    def _make_end_structures(self) -> Generator[bytes, None, None]:
        """
        Make zip64 end structures, which include:
            central directory file header for every file
            zip64 extra field for every file
            zip64 end of central dir record
            zip64 end of central dir locator
            end of central dir record
        """
        # Save offset to start of central dir for zip64 end of cdir record
        self._offset_to_start_of_central_dir = self._get_offset()

        # Stream central directory entries
        for file in self.files:
            chunk = self._make_cdir_file_header(file)
            chunk += self._make_zip64_extra_field(file)
            self._cdir_size += len(chunk)
            chunk = self._apply_remaining_offset(chunk)
            self._add_offset(len(chunk))

            yield chunk

        yield self._apply_remaining_offset(self._make_zip64_end_of_cdir_record())

        yield self._apply_remaining_offset(self._make_zip64_end_of_cdir_locator())

        yield self._apply_remaining_offset(self._make_end_of_cdir_record())

    async def _async_stream_single_file(self, file: BaseFile) -> AsyncGenerator[bytes, None]:
        """This function streams a single file, it also applies running_offset is needed"""

        yield self._apply_remaining_offset(self._make_local_file_header(file))

        async for chunk in file.async_generate_processed_file_data():
            yield self._apply_remaining_offset(chunk)

        yield self._apply_remaining_offset(self._make_data_descriptor(file))

    def _stream_single_file(self, file: BaseFile) -> Generator[bytes, None, None]:
        """
        stream single zip file with header and descriptor at the end.
        """
        yield self._apply_remaining_offset(self._make_local_file_header(file))

        for chunk in file.generate_processed_file_data():
            yield self._apply_remaining_offset(chunk)

        yield self._apply_remaining_offset(self._make_data_descriptor(file))

    async def async_stream(self, byte_offset: int = 0) -> AsyncGenerator[bytes, None]:
        """Streams the entire archive asynchronously"""
        self._check_if_can_stream()

        starting_file_index, remaining_offset = self._find_starting_file(byte_offset)
        self._remaining_offset = remaining_offset

        self._set_offset(byte_offset - remaining_offset)
        if starting_file_index is not None:
            for file in self.files[starting_file_index:]:
                file.set_offset(self._get_offset())
                async for chunk in self._async_stream_single_file(file):
                    self._add_offset(len(chunk))
                    yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk

    def stream(self, byte_offset: int = 0) -> Generator[bytes, None, None]:
        self._check_if_can_stream()

        starting_file_index, remaining_offset = self._find_starting_file(byte_offset)
        self._remaining_offset = remaining_offset

        self._set_offset(byte_offset - remaining_offset)
        if starting_file_index is not None:
            for file in self.files[starting_file_index:]:
                file.set_offset(self._get_offset())
                for chunk in self._stream_single_file(file):
                    self._add_offset(len(chunk))
                    yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk

    def _check_if_can_stream(self):
        if self.__used:
            raise RuntimeError("Do not re-use zipFly instances. Recreate it.")
        self.__used = True

    def _apply_remaining_offset(self, data):
        if self._remaining_offset == 0:
            return data
        data_length = len(data)

        # If the offset is greater than or equal to the data length, return empty data
        if self._remaining_offset >= data_length:
            self._remaining_offset -= data_length  # Decrement offset by the length of the skipped data
            self._add_offset(data_length)
            return b''

        # Otherwise, slice data from the offset and reset the offset to 0
        result = data[self._remaining_offset:]
        self._add_offset(self._remaining_offset)
        self._remaining_offset = 0  # Offset is fully applied
        return result
