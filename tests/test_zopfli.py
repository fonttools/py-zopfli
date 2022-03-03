#!/usr/bin/env python

import gzip
import shutil
import subprocess
import sys
import zlib
from io import BytesIO
from pathlib import Path

import zopfli.gzip
import zopfli.zlib
import zopfli.png

import pytest


class BaseTests(object):
    data = (Path(__file__).parent.parent / "README.rst").read_bytes()

    def test_reversible(self):
        data = self.data
        assert self.decompress(self.compress(data)) == data

    def test_iterations_help(self):
        data = self.data
        assert len(self.compress(data, numiterations=1)) > len(
            self.compress(data, numiterations=1000)
        )


class TestZlib(BaseTests):
    compress = staticmethod(zopfli.zlib.compress)
    decompress = staticmethod(zlib.decompress)


class TestGzip(BaseTests):

    compress = staticmethod(zopfli.gzip.compress)

    def decompress(self, s):
        return gzip.GzipFile(fileobj=BytesIO(s)).read()


# The first eight bytes of a PNG file always contain the following (decimal) values:
#   137 80 78 71 13 10 26 10
# https://www.w3.org/TR/PNG-Structure.html
PNG_HEADER = b"\x89PNG\r\n\x1a\n"

DATA_DIR = Path(__file__).parent / "data"


class TestPngOptimize:
    @staticmethod
    def assert_valid_png_header(data):
        assert len(data) >= 8
        assert data[:8] == PNG_HEADER

    @pytest.fixture(params=list(DATA_DIR.glob("*.png")))
    def png_file(self, request):
        return request.param

    @pytest.fixture
    def png_data(self, png_file):
        png = png_file.read_bytes()
        self.assert_valid_png_header(png)
        return png

    @pytest.mark.parametrize(
        "kwargs",
        [
            {},  # default
            {"verbose": True},
            {"lossy_transparent": True},
            {"lossy_8bit": True},
            {"use_zopfli": False},
            {"filter_strategies": "01234mepb"},
            {"keepchunks": ["gAMA", "bKGD"]},
            {"num_iterations": 30},
            {"num_iterations_large": 10},
        ],
    )
    def test_optimize_with_arguments(self, png_data, kwargs):
        result_png = zopfli.png.optimize(png_data, **kwargs)

        self.assert_valid_png_header(result_png)
        assert len(result_png) < len(png_data)

    @pytest.mark.parametrize(
        "options",
        [
            [],  # default
            ["-v"],
            ["-m"],
            ["--lossy_transparent", "--lossy_8bit"],
            ["-q"],
            ["--always_zopflify"],
            ["--iterations", "20"],
            ["--filters", "0me"],
            ["--keepchunks", "sBIT,bKGD"],
        ],
    )
    def test_cli(self, png_file, tmp_path, options):
        output_file = tmp_path / png_file.name
        cmd = (
            [sys.executable, "-m", "zopfli.png"]
            + options
            + [str(png_file), str(output_file)]
        )
        p = subprocess.run(cmd, check=True, capture_output=True)
        if "-v" in options:
            assert "Result is smaller" in p.stdout.decode()
        assert output_file.exists()
        assert output_file.stat().st_size < png_file.stat().st_size

    @pytest.mark.parametrize(
        "overwrite, answer", [(True, ""), (False, "y"), (False, "N")]
    )
    def test_cli_overwrite(self, tmp_path, answer, overwrite):
        input_file = next(DATA_DIR.glob("*.png"))
        output_file = tmp_path / input_file.name
        shutil.copy(input_file, output_file)
        cmd = (
            [sys.executable, "-m", "zopfli.png", "-v"]
            + (["-y"] if overwrite else [])
            + [str(input_file), str(output_file)]
        )

        p = subprocess.run(cmd, input=answer.encode(), check=True, capture_output=True)

        stdout = p.stdout.decode()

        assert "Result is smaller" in stdout
        assert ("exists, overwrite? (y/N)" in stdout) ^ overwrite

        if overwrite or answer == "y":
            assert output_file.stat().st_size < input_file.stat().st_size
        elif not overwrite and answer == "N":
            assert output_file.stat().st_size == input_file.stat().st_size


if __name__ == "__main__":
    import sys

    pytest.main(sys.argv)
