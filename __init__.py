#!/usr/bin/env python3

import sys
import argparse

import pyppeteer
import asyncio
import requests

import io
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from PyPDF2 import PdfFileMerger
import pathlib

import time
import re
from urllib.parse import quote
import logging
from logging import StreamHandler

logger = logging.getLogger(__name__)


async def _pyppeteer_main(url, output = None):

    debug = isinstance(output, bool) and output

    browser = await pyppeteer.launch()
    page = await browser.newPage()
    await page.setViewport({'width': 1000, 'height': 1000})
    await page.goto(url)
    #await page.screenshot({'path': 'muse1.png'})

    score_name = await (await (await page.querySelector("h1")).getProperty("innerText")).jsonValue()

    async def get_score_creator():
        return await (await (await page.querySelector("h2")).getProperty("innerText")).jsonValue()

    async def get_score_release_date():
        for h2 in await page.querySelectorAll("aside h2"):
            match = re.fullmatch(
                r"Uploaded\son\s(?P<month>[A-Z][a-z]{2})\s(?P<day>\d{1,2}),\s(?P<year>\d{4})",
                await (await h2.getProperty("innerText")).jsonValue()
            )
            if match is not None:
                break
        return int(time.mktime(time.strptime(match.group("month")
                                         + ' ' + match.group("day").zfill(2)
                                         + ' ' + match.group("year"), "%b %d %Y")))

    async def get_score_tags():
        tags = []
        for span in await page.querySelectorAll("aside section span"):
            text = await (await span.getProperty("innerText")).jsonValue()
            if ((await (await (await span.getProperty(
                    "parentElement")).getProperty(
                    "href")).jsonValue()) ==
                    "https://musescore.com/sheetmusic?tags=" + quote(text)):
                tags.append(text)
        return ','.join(tags)

    info_dict = {
        "Title": score_name,
        "Creator": await get_score_creator(),
        #"Date released": str(await get_score_release_date()),
        "Keywords": await get_score_tags(),
    }

    with open("script.js", 'r') as f:
        svgs = await page.evaluate(f.read())

    await browser.close()

    for k, v in info_dict.items():
        logger.info(f'Collected "{k}" metadata from score: "{v}"')

    merger = PdfFileMerger()
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

    if not isinstance(output, str):
        output = score_name
        if debug:
            pdfFolder = pathlib.Path("PDFs")
            if not pdfFolder.is_dir():
                pdfFolder.mkdir()
            output = (pdfFolder / (time.strftime("%Y%m%d-%H%M%S") + ' ' + output)
                     ).with_suffix(".pdf")
    if isinstance(output, str):
        output = pathlib.Path(output).with_suffix(".pdf")
    
    if debug and pathlib.Path() == pathlib.Path(__file__).parent:
        output = pathlib.Path("PDFs") / output

    will_rewrite = output.is_file()
    with output.open(mode='wb') as o:
        merger.write(o)

    logger.info(f'PDF { "over" * int(will_rewrite) }written to "{output.resolve()}"')
    

def to_pdf(*args):

    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-o", "--output", default=None)
    group.add_argument("-ao", "--auto-output", nargs="?", default=None, const="")

    args = parser.parse_args(args)

    log_level = logging.INFO if args.auto_output is None else logging.DEBUG

    if args.auto_output:
        logging.basicConfig(level=log_level, filename=args.auto_output)
        #Why the hell did pyppeteer set the handler for themselves? They should've used logging.basicConfig() for fuck's sake
        pyppeteer._logger.removeHandler(pyppeteer._log_handler)
        pyppeteer_log_handler = logging.FileHandler(args.auto_output)
        pyppeteer_log_handler.setFormatter(pyppeteer._formatter)
        pyppeteer._logger.addHandler(pyppeteer_log_handler)
    else:
        logging.basicConfig(level=log_level)

    asyncio.get_event_loop().run_until_complete(_pyppeteer_main(args.url,
                                                               args.output or
                                                                    isinstance(args.auto_output,
                                                                               str)
                                                              ))



if __name__ == "__main__":
    to_pdf(*sys.argv[1:])
