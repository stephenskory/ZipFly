"""Run tests of ZipFly."""

import time
import zipfile
import zlib

# Need to also have https://pypi.org/project/pytest-asyncio/ installed
# The 4GB tests are kind of slow, this can help if you have enough memory.
# Install this https://pypi.org/project/pytest-xdist/ and then
# `pytest -n auto`
import pytest

from src.zipFly import GenFile, LocalFile, ZipFly, consts
from tests.test_utils import lorem_ipsum_generator, lorem_ipsum, single_archive_size, lorem_ipsum_generator_async, multifile_archive_size


def test_GenFile_COMPRESSION_DEFLATE(tmp_path):
    """Test GenFile with compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "deflate.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_GenFile_COMPRESSION_DEFLATE_async(tmp_path):
    """Test GenFile with compression (async)."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "deflate_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


def test_GenFile_NO_COMPRESSION(tmp_path):
    """Test GenFile without compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.NO_COMPRESSION,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_GenFile_NO_COMPRESSION_async(tmp_path):
    """Test GenFile without compression (async)."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.NO_COMPRESSION,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


def test_LocalFile_COMPRESSION(tmp_path):
    """Test LocalFile with compression."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "compressed.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_LocalFile_COMPRESSION_async(tmp_path):
    """Test LocalFile with compression (async)."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "compressed_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


def test_LocalFile_NO_COMPRESSION(tmp_path):
    """Test LocalFile without compression."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
        compression_method=consts.NO_COMPRESSION,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress_local.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()
        for info in zfp.infolist():
            print(f"{info.filename}: CRC={hex(info.CRC)}")

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_LocalFile_NO_COMPRESSION_async(tmp_path):
    """Test LocalFile without compression (async)."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
        compression_method=consts.NO_COMPRESSION,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress_local_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


def test_multifile_archive(tmp_path):
    """Test adding multiple files to an archive."""
    n_files = 5
    input_paths = []
    for i in range(n_files):
        path = tmp_path / f"lorem_{i}.txt"
        path.write_bytes(lorem_ipsum)
        input_paths.append(path)

    files = [
        LocalFile(
            name=f"lorem_ipsum_{i}.txt",
            file_path=path,
            compression_method=consts.COMPRESSION_DEFLATE,
        )
        for i, path in enumerate(input_paths)
    ]
    zip_fly = ZipFly(files)

    zip_path = tmp_path / "multifile.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    outs = []
    with zipfile.ZipFile(zip_path) as zfp:
        for zname in zfp.filelist:
            with zfp.open(zname.filename) as tfp:
                outs.append(tfp.read())

    for out in outs:
        assert out == lorem_ipsum

    assert zip_fly.calculate_archive_size() == multifile_archive_size


@pytest.mark.asyncio
async def test_multifile_archive_async(tmp_path):
    """Test adding multiple files to an archive (async version) using tmp_path."""
    n_files = 5
    outnames = []

    # Create temp files using tmp_path
    for i in range(n_files):
        temp_file = tmp_path / f"lorem_{i}.txt"
        temp_file.write_bytes(lorem_ipsum)
        outnames.append(temp_file)

    # Prepare LocalFile objects
    files = [
        LocalFile(
            name=f"lorem_ipsum_{i}.txt",
            file_path=str(path),
            compression_method=consts.COMPRESSION_DEFLATE,
        )
        for i, path in enumerate(outnames)
    ]

    zip_fly = ZipFly(files)
    archive_path = tmp_path / "test_archive.zip"

    # Stream zip archive asynchronously
    with archive_path.open("wb") as f_out:
        async for chunk in zip_fly.async_stream():
            f_out.write(chunk)

    assert zip_fly.calculate_archive_size() == multifile_archive_size

    # Validate zip content
    outs = []
    with zipfile.ZipFile(archive_path, "r") as zfp:
        for zname in zfp.filelist:
            with zfp.open(zname.filename) as tfp:
                outs.append(tfp.read())

    for out in outs:
        assert out == lorem_ipsum


def test_zipfly_stream_reuse_raises():
    """Ensure ZipFly raises an error when .stream() is reused."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.NO_COMPRESSION,
    )
    zip_fly = ZipFly([file1])

    for _ in zip_fly.stream():
        break

    with pytest.raises(Exception):
        for _ in zip_fly.stream():
            break

@pytest.mark.asyncio
async def test_zipfly_resumable_async(tmp_path):
    """
    Test resumable async streaming of ZipFly.
    Writes first part of archive, pauses, then resumes from byte offset.
    """
    # Setup your large file and ZipFly instance
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.NO_COMPRESSION,
        crc=zlib.crc32(lorem_ipsum)
    )
    files = [file1]

    zipFly1 = ZipFly(files)
    zipFly2 = ZipFly(files)

    out_file = tmp_path / "resumed.zip"

    byte_offset = 0
    STOP_BYTE = 46

    zipFly1.calculate_archive_size()

    # Pause function: write until STOP_BYTE
    async def pause_zip_async():
        nonlocal byte_offset
        with open(out_file, "wb") as f_out:
            async for chunk in zipFly1.async_stream():
                remaining = STOP_BYTE - byte_offset
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]

                f_out.write(chunk)
                byte_offset += len(chunk)

                if byte_offset >= STOP_BYTE:
                    break

    # Resume function: continue from STOP_BYTE
    async def resume_zip_async():
        with open(out_file, "ab") as f_out:
            async for chunk in zipFly2.async_stream(byte_offset=STOP_BYTE):
                f_out.write(chunk)

    # Run pause and resume
    await pause_zip_async()
    await resume_zip_async()

    # Validate zip file is valid and contains expected file with correct size
    with zipfile.ZipFile(out_file, "r") as zfp:
        info = zfp.getinfo("lorem_ipsum.txt")
        assert info.file_size == len(lorem_ipsum)
        with zfp.open("lorem_ipsum.txt") as tfp:
            content = tfp.read()
            assert len(content) == len(lorem_ipsum)

# Test if renaming duplicated file names works
# Test if modification_time works for both gen file and localfile
