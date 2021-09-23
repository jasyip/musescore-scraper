#!/usr/bin/env python

import sys
from pathlib import Path
import asyncio
import json
from urllib.parse import urlparse
import pytest
from typing import Any
from tempfile import NamedTemporaryFile
import argparse

sys.path.insert(0, str(Path(__file__).parents[1].resolve()))

from musescore_scraper import _main


URLS = [
    "https://musescore.com/masonatcapricestudio/bully-calliope-mori-bully-ijimekko-bully-mori-calliope",
    "https://musescore.com/captainmeow/reflect-gawr-gura",
]

DATA_PDFS = [
    (Path(__file__).parent / path).read_bytes() for path in [
        "testdata/example1.pdf",
        "testdata/example2.pdf",
    ]
]



def test_main():
    for i in range(len(URLS)):
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            fname: Path = Path(tf.name)
            _main([URLS[i], "-o", str(fname)])

        assert fname.read_bytes() == DATA_PDFS[i]

        fname.unlink()


def test_main_multiple():
    temp_files = []
    for i in range(len(URLS)):
        temp_files.append(NamedTemporaryFile(suffix=".pdf", delete=False))
    tf_names = [tf.name for tf in temp_files]

    _main([*URLS, "-o", *tf_names])

    for i in range(len(URLS)):
        tf_path = Path(tf_names[i])
        assert tf_path.read_bytes() == DATA_PDFS[i]

        tf_path.unlink()


def test_invalid_opts():
    with NamedTemporaryFile(suffix=".pdf") as tf:
        with pytest.raises((argparse.ArgumentError, SystemExit)):
            _main([*URLS, "-o", tf.name])

    with pytest.raises((argparse.ArgumentTypeError, SystemExit)):
        _main(["foo"])
