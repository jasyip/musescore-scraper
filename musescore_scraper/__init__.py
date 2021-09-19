#!/usr/bin/env python3

from typing import Union, Optional

import os
import sys
import argparse
from pkgutil import get_data

import pyppeteer
import asyncio
import requests

import io
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from PyPDF2 import PdfFileMerger
from pathlib import Path
import platform

import time
import re
from urllib.parse import quote
import logging
from logging import StreamHandler





_logger: logging.Logger = logging.getLogger(__name__)


async def _pyppeteer_main(url: str, output: Union[None, str, Path], debug: bool, timeout: float):

    browser: pyppeteer.browser.Browser = await pyppeteer.launch()
    page: pyppeteer.page.Page = await browser.newPage()
    await page.setViewport({'width': 1000, 'height': 1000})
    await page.goto(url, timeout=timeout)
    #await page.screenshot({'path': 'muse1.png'})

    score_name: str = (
            await (await (await page.querySelector("h1")).getProperty("innerText")).jsonValue())

    async def get_score_creator() -> str:
        return await (await (await page.querySelector("h2")).getProperty("innerText")).jsonValue()

    async def get_score_release_date() -> int:
        for h2 in await page.querySelectorAll("aside h2"):
            match: Optional[re.Match] = re.fullmatch(
                r"Uploaded\son\s(?P<month>[A-Z][a-z]{2})\s(?P<day>\d{1,2}),\s(?P<year>\d{4})",
                await (await h2.getProperty("innerText")).jsonValue()
            )
            if match is not None:
                break
        return int(time.mktime(time.strptime(match.group("month")
                                         + ' ' + match.group("day").zfill(2)
                                         + ' ' + match.group("year"), "%b %d %Y")))

    async def get_score_tags() -> str:
        tags: list[str] = []
        for span in await page.querySelectorAll("aside section span"):
            text: str = await (await span.getProperty("innerText")).jsonValue()
            if ((await (await (await span.getProperty(
                    "parentElement")).getProperty(
                    "href")).jsonValue()) ==
                    "https://musescore.com/sheetmusic?tags=" + quote(text)):
                tags.append(text)
        return ','.join(tags)

    info_dict: dict[str, str] = {
        "Title": score_name,
        "Creator": await get_score_creator(),
        #"Date released": str(await get_score_release_date()),
        "Keywords": await get_score_tags(),
    }

    # svgs = await page.evaluate(bytes(get_data("musescore_scraper", "script.js"), "utf-8"))
    svgs: list[str] = await page.evaluate(str(get_data("musescore_scraper", "script.js"), "utf-8"))

    await browser.close()

    for k, v in info_dict.items():
        _logger.info(f'Collected "{k}" metadata from score: "{v}"')

    merger: PdfFileMerger = PdfFileMerger()
    for svg in svgs:
        merger.append(
            io.BytesIO(
                renderPDF.drawToString(
                    svg2rlg(
                        io.BytesIO(
                            requests.get(svg).content
                        )
                    )
                )
            )
        )

    merger.addMetadata({ ('/' + k): v for k, v in info_dict.items() })

    if not output:
        output = score_name

    if debug:
        output = time.strftime("%Y%m%d-%H%M%S") + ' ' + output


    def eval_expression(input_string) -> str:
        code: typing.Any = compile(input_string, "<string>", "eval")
        windows_regex: str = r"[0x00-0x1F\"*/:<>?\\|]"
        darwin_regex: str = r"[: ]"
        linux_regex: str = (r"[\x00/]" if os.environ.keys() & {"IS_WSL", "WSL_DISTRO_NAME"}
                        else windows_regex)
        allowed: dict[str, str] = { k : v for k, v in locals().items() if k.endswith("_regex") }
        if not (len(code.co_names) == 1 and set(allowed) >= set(code.co_names)):
            raise NameError("Invalid platform.")
        return eval(code, {"__builtins__": {}}, allowed)

    if isinstance(output, str):
        output = Path(re.sub(eval_expression(platform.system().lower() + "_regex"), '_', output))
    output = output.with_suffix(".pdf")
    
    if debug and Path(__file__).parent.parent in Path().resolve().parents:
        pdfs_folder: Path = Path("PDFs")
        if not pdfs_folder.is_dir():
            pdfs_folder.mkdir()
        output = Path("PDFs") / output

    will_rewrite: bool = output.is_file()
    with output.open(mode='wb') as o:
        merger.write(o)

    output = output.resolve()
    try:
        output = output.relative_to(Path().resolve())
    except ValueError:
        pass

    _logger.info(f'PDF { "over" * int(will_rewrite) }written to "{output}"')
    

def to_pdf(
        url: str,
        *,
        output: Union[None, str, Path]=None,
        debug_log: Union[None, str, Path]=None,
        timeout: float=120
) -> None:
    """
    Extracts the SVGs from a MuseScore score URL.
    Then converts each one to a PDF then merges each page into one multi-page PDF.

    Parameters
    ----------
    url : str
        MuseScore score URL to extract PDF from.
    output : Union[None, str, Path]
        File destination to write PDF to.
        If *None*, file name will be the extracted score title.
    debug_log : Union[None, str, Path]
        Whether to receive debug messages or not.
        If so, log will be written to destination, or to stderr if string is empty.
    timeout: float
        How many seconds should be given for the extraction of the SVGs before aborting.
            Will not abort if timeout=0
    """
    log_level: int = logging.INFO if debug_log is None else logging.DEBUG

    if debug_log:
        logging.basicConfig(level=log_level, filename=Path(debug_log))
        #Why the hell did pyppeteer set the handler for themselves? They should've used logging.basicConfig() for fuck's sake
        pyppeteer._logger.removeHandler(pyppeteer._log_handler)
        pyppeteer_log_handler: logging.FileHandler = logging.FileHandler(debug_log)
        pyppeteer_log_handler.setFormatter(pyppeteer._formatter)
        pyppeteer._logger.addHandler(pyppeteer_log_handler)
    else:
        logging.basicConfig(level=log_level)

    asyncio.get_event_loop().run_until_complete(_pyppeteer_main(url, output, debug_log is not None, timeout))

def main() -> None:
    """
    This main function is used as a CLI and gets its arguments from sys.argv
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-o", "--output")
    parser.add_argument("-d", "--debug-log", nargs="?", const="")
    parser.add_argument("-t", "--timeout", type=float)

    to_pdf(**parser.parse_args().__dict__)

if __name__ == "__main__":
    main()
