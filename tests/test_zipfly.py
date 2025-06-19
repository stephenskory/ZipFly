"""Run tests of ZipFly."""

import time
import zipfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from tempfile import NamedTemporaryFile

# Need to also have https://pypi.org/project/pytest-asyncio/ installed
# The 4GB tests are kind of slow, this can help if you have enough memory.
# Install this https://pypi.org/project/pytest-xdist/ and then
# `pytest -n auto`
import pytest

from src.zipFly import GenFile, LocalFile, ZipFly, consts

# ruff: noqa: S101, N802

lorem_ipsum = b"""Est magni commodi voluptate consequuntur qui consequatur.
Nam quaerat velit eum non autem laborum quae qui.
Maxime similique qui et natus qui ut ut et.
Quia omnis dignissimos id molestias dolores provident quis quia.
Dicta quaerat facere molestiae. Et quod totam nihil.
Repudiandae enim esse optio ut nostrum aliquam et cumque.
Distinctio molestiae dolore et debitis saepe optio.
Incidunt id quo rerum dicta dolorem.
Eos non eum qui totam.
Dolores laborum quibusdam fugiat temporibus sed quia voluptatem dolor.
Fugit ut iste voluptatem dolores et vero.
Qui quibusdam nulla distinctio.
Numquam explicabo laboriosam delectus nemo recusandae blanditiis voluptates.
Esse ea magnam qui ea.
Id quo odio saepe rerum quia natus odio exercitationem.
Deleniti sunt dolores cupiditate quia eum ab fugit.
Similique ullam et tempore sunt incidunt ipsa.
Molestiae est harum similique aspernatur distinctio aut."""

single_archive_size = 1152
multifile_archive_size = 5388


def lorem_ipsum_generator() -> Generator[bytes]:
    """Yield lines of lorem ipsum."""
    lines = lorem_ipsum.split(b"\n")
    # Don't yield trailing newline
    for line in lines[:-1]:
        yield line
        yield b"\n"
    yield lines[-1]


async def lorem_ipsum_generator_async() -> AsyncGenerator[bytes]:
    """Yield lines of lorem ipsum."""
    for line in lorem_ipsum_generator():
        yield line


def sized_zeros_generator(size: int) -> Generator[bytes]:
    """Yield zeros up to a certain size."""
    yielded = 0
    line = b"0" * 1024
    while yielded < size:
        yield line[: size - yielded]
        yielded += len(line[: size - yielded])
        if yielded >= size:
            break


async def sized_zeros_generator_async(size: int) -> AsyncGenerator[bytes]:
    """Yield zeros up to a certain size."""
    for zeros in sized_zeros_generator(size):
        yield zeros


def test_GenFile_COMPRESSION_DEFLATE() -> None:
    """Test GenFile with compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    # Would need to bump to Python 3.12 to get the delete_on_close
    # parameter.
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out

    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_GenFile_COMPRESSION_DEFLATE_async() -> None:
    """Test GenFile with compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    # Would need to bump to Python 3.12 to get the delete_on_close
    # parameter.
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out

    assert zip_fly.calculate_archive_size() == single_archive_size


def test_GenFile_NO_COMPRESSION() -> None:
    """Test GenFile without compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    # Would need to bump minimum to Python 3.12 to get the delete_on_close
    # parameter and use a "with" context handler, so we'll not do that for now
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out

    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_GenFile_NO_COMPRESSION_async() -> None:
    """Test GenFile without compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    # Would need to bump minimum to Python 3.12 to get the delete_on_close
    # parameter and use a "with" context handler, so we'll not do that for now
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out

    assert zip_fly.calculate_archive_size() == single_archive_size


def test_LocalFile_COMPRESSION() -> None:
    """Test GenFile with compression."""
    lorem_ipsum_fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    lorem_ipsum_fp.write(lorem_ipsum)
    lorem_ipsum_fp.close()

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=lorem_ipsum_fp.name,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    assert zip_fly.calculate_archive_size() == single_archive_size

    Path.unlink(lorem_ipsum_fp.name)

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out


@pytest.mark.asyncio
async def test_LocalFile_COMPRESSION_async() -> None:
    """Test GenFile with compression."""
    lorem_ipsum_fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    lorem_ipsum_fp.write(lorem_ipsum)
    lorem_ipsum_fp.close()

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=lorem_ipsum_fp.name,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    assert zip_fly.calculate_archive_size() == single_archive_size

    Path.unlink(lorem_ipsum_fp.name)

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out


def test_LocalFile_NO_COMPRESSION() -> None:
    """Test GenFile without compression."""
    lorem_ipsum_fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    lorem_ipsum_fp.write(lorem_ipsum)
    lorem_ipsum_fp.close()

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=lorem_ipsum_fp.name,
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    assert zip_fly.calculate_archive_size() == single_archive_size

    Path.unlink(lorem_ipsum_fp.name)

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out


@pytest.mark.asyncio
async def test_LocalFile_NO_COMPRESSION_async() -> None:
    """Test GenFile without compression."""
    lorem_ipsum_fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    lorem_ipsum_fp.write(lorem_ipsum)
    lorem_ipsum_fp.close()

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=lorem_ipsum_fp.name,
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    assert zip_fly.calculate_archive_size() == single_archive_size

    Path.unlink(lorem_ipsum_fp.name)

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("lorem_ipsum.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert lorem_ipsum == out


def test_multifile_archive() -> None:
    """Test adding multiple files to an archive."""
    outnames = []
    n_files = 5
    for _ in range(n_files):
        lorem_ipsum_fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
        lorem_ipsum_fp.write(lorem_ipsum)
        lorem_ipsum_fp.close()
        outnames.append(lorem_ipsum_fp.name)

    files = []
    for fi, outname in enumerate(outnames):
        files.append(
            LocalFile(
                name=f"lorem_ipsum_{fi}.txt",
                file_path=outname,
                compression_method=consts.COMPRESSION_DEFLATE,
            ),
        )
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    assert zip_fly.calculate_archive_size() == multifile_archive_size

    for outname in outnames:
        Path.unlink(outname)

    outs = []
    with zipfile.ZipFile(fp.name, "r") as zfp:
        for zname in zfp.filelist:
            with zfp.open(zname.filename) as tfp:
                # We'll test asserts later so we can delete the tempfile
                # before any failed asserts might leave some junk
                outs.append(tfp.read())

    Path.unlink(fp.name)

    for out in outs:
        assert lorem_ipsum == out


@pytest.mark.asyncio
async def test_multifile_archive_async() -> None:
    """Test adding multiple files to an archive."""
    outnames = []
    n_files = 5
    for _ in range(n_files):
        lorem_ipsum_fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
        lorem_ipsum_fp.write(lorem_ipsum)
        lorem_ipsum_fp.close()
        outnames.append(lorem_ipsum_fp.name)

    files = []
    for fi, outname in enumerate(outnames):
        files.append(
            LocalFile(
                name=f"lorem_ipsum_{fi}.txt",
                file_path=outname,
                compression_method=consts.COMPRESSION_DEFLATE,
            ),
        )
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    assert zip_fly.calculate_archive_size() == multifile_archive_size

    for outname in outnames:
        Path.unlink(outname)

    outs = []
    with zipfile.ZipFile(fp.name, "r") as zfp:
        for zname in zfp.filelist:
            with zfp.open(zname.filename) as tfp:
                # We'll test asserts later so we can delete the tempfile
                # before any failed asserts might leave some junk
                outs.append(tfp.read())

    Path.unlink(fp.name)

    for out in outs:
        assert lorem_ipsum == out


def test_4GB_GenFile_COMPRESSION_DEFLATE() -> None:
    """Test GenFile with compression for a large file."""
    gb4plus = 2**32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        # Compressing all zeros is faster than lorem ipsum and we
        # only care that we can compress a big file.
        generator=sized_zeros_generator(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("zeros.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert len(out) == gb4plus


@pytest.mark.asyncio
async def test_4GB_GenFile_COMPRESSION_DEFLATE_async() -> None:
    """Test GenFile with compression for a large file."""
    gb4plus = 2**32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        # Compressing all zeros is faster than lorem ipsum and we
        # only care that we can compress a big file.
        generator=sized_zeros_generator_async(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("zeros.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert len(out) == gb4plus


def test_4GB_GenFile_NO_COMPRESSION() -> None:
    """Test GenFile without compression for a large file."""
    gb4plus = 2**32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        # Compressing all zeros is faster than lorem ipsum and we
        # only care that we can compress a big file.
        generator=sized_zeros_generator(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    for chunk in zip_fly.stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("zeros.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert len(out) == gb4plus


@pytest.mark.asyncio
async def test_4GB_GenFile_NO_COMPRESSION_async() -> None:
    """Test GenFile without compression for a large file."""
    gb4plus = 2**32 + 1024
    file1 = GenFile(
        name="zeros.txt",
        # Compressing all zeros is faster than lorem ipsum and we
        # only care that we can compress a big file.
        generator=sized_zeros_generator_async(gb4plus),
        modification_time=time.time(),
        size=gb4plus,
        compression_method=consts.NO_COMPRESSION,
    )
    files = [file1]
    zip_fly = ZipFly(files)
    fp = NamedTemporaryFile(delete=False)  # noqa: SIM115
    async for chunk in zip_fly.async_stream():
        fp.write(chunk)
    fp.close()

    with (
        zipfile.ZipFile(fp.name, "r") as zfp,
        zfp.open("zeros.txt") as tfp,
    ):
        out = tfp.read()

    Path.unlink(fp.name)

    assert len(out) == gb4plus
