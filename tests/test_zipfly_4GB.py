"""4GB, slow tests"""

import time
import zipfile

import pytest

from src.zipFly import GenFile, ZipFly, consts
from tests.test_utils import sized_zeros_generator, sized_zeros_generator_async


@pytest.mark.slow
def test_4GB_GenFile_COMPRESSION_DEFLATE(tmp_path):
    """Test GenFile with compression for a large file."""
    gb4plus = 2 ** 32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        generator=sized_zeros_generator(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)

    fp_path = tmp_path / "archive_deflate.zip"
    with fp_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(fp_path, "r") as zfp, zfp.open("zeros.txt") as tfp:
        out = tfp.read()

    assert len(out) == gb4plus


@pytest.mark.slow
@pytest.mark.asyncio
async def test_4GB_GenFile_COMPRESSION_DEFLATE_async(tmp_path):
    """Async test: GenFile with compression for a large file."""
    gb4plus = 2 ** 32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        generator=sized_zeros_generator_async(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)

    fp_path = tmp_path / "archive_deflate_async.zip"
    with fp_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(fp_path, "r") as zfp, zfp.open("zeros.txt") as tfp:
        out = tfp.read()

    assert len(out) == gb4plus


@pytest.mark.slow
def test_4GB_GenFile_NO_COMPRESSION(tmp_path):
    """Test GenFile without compression for a large file."""
    gb4plus = 2 ** 32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        generator=sized_zeros_generator(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)

    fp_path = tmp_path / "archive_nocompression.zip"
    with fp_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(fp_path, "r") as zfp, zfp.open("zeros.txt") as tfp:
        out = tfp.read()

    assert len(out) == gb4plus


@pytest.mark.slow
@pytest.mark.asyncio
async def test_4GB_GenFile_NO_COMPRESSION_async(tmp_path):
    """Async test: GenFile without compression for a large file."""
    gb4plus = 2 ** 32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        generator=sized_zeros_generator_async(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)

    fp_path = tmp_path / "archive_nocompression_async.zip"
    with fp_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(fp_path, "r") as zfp, zfp.open("zeros.txt") as tfp:
        out = tfp.read()

    assert len(out) == gb4plus