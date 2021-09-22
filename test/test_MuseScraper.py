#!/usr/bin/env python

import sys
from pathlib import Path
import asyncio
import json
from urllib.parse import urlparse
import pytest
from typing import Any
from tempfile import NamedTemporaryFile

sys.path.insert(0, str(Path(__file__).parents[1].resolve()))

from musescore_scraper import MuseScraper, AsyncMuseScraper


URL = "https://musescore.com/masonatcapricestudio/bully-calliope-mori-bully-ijimekko-bully-mori-calliope"

DATA_JSON = json.load(Path("testdata/pyppeteer_example_data.json").open('r'))
DATA_PDF = Path("testdata/conversion_example.pdf").read_bytes()



@pytest.mark.asyncio
async def test_pyppeteer_portion():
    async with AsyncMuseScraper() as musescraper:
        received_data: dict[str, Any] = await musescraper._pyppeteer_main(URL)

    assert received_data["info"] == DATA_JSON["info"]
    assert len(received_data["svgs"]) == len(DATA_JSON["svgs"])
    for r, e in zip(received_data["svgs"], DATA_JSON["svgs"]):
        assert urlparse(r).path == urlparse(e).path


@pytest.mark.asyncio
async def test_MuseScraperAsync():
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        fname: Path = Path(tf.name)
        async with AsyncMuseScraper() as musescraper:
            assert fname == await musescraper.to_pdf(URL, fname)

    assert fname.read_bytes() == DATA_PDF

    fname.unlink()


def test_MuseScraper():
    with NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        fname: Path = Path(tf.name)
        print("before con")
        with MuseScraper() as musescraper:
            print("after con")
            output = musescraper.to_pdf(URL, fname)
            print("after pdf generation")
            assert fname == output

    assert fname.read_bytes() == DATA_PDF

    fname.unlink()



def pytest_sessionfinish(session, exitstatus):
    asyncio.get_event_loop().close()
