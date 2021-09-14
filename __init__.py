#!/usr/bin/env python

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


async def pyppeteer_main(url, output = None):
    browser = await pyppeteer.launch()
    page = await browser.newPage()
    await page.setViewport({'width': 1000, 'height': 1000})
    await page.goto(url)
    #await page.screenshot({'path': 'muse1.png'})


    if not isinstance(output, str):
        debug_type = output
        output = await (await (await page.querySelector("h1")).getProperty("innerText")
                        ).jsonValue()
        if debug_type:
            pdfFolder = pathlib.Path("PDFs")
            if not pdfFolder.is_dir():
                pdfFolder.mkdir()
            output = (pdfFolder /
                (time.strftime("%Y%m%d-%H%M%S") + '_' + re.sub(r"\s", '_', output))
            ).with_suffix(".pdf")

    with open("script.js", 'r') as f:
        svgs = await page.evaluate(f.read())

    await browser.close()


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

    if isinstance(output, str):
        output = pathlib.Path(output).with_suffix(".pdf")

    with output.open(mode='wb') as o:
        merger.write(o)


    

def to_pdf(*args):

    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-o", "--output", default=None)
    group.add_argument("-ao", "--auto-output", action="store_true")

    args = parser.parse_args(args)


    asyncio.get_event_loop().run_until_complete(pyppeteer_main(args.url, args.output or args.auto_output))

    """
    with open("script.js", 'r') as f:
        print(html.render(script=f.read(), timeout=60, sleep=5))
    """

    
if __name__ == "__main__":
    to_pdf(*sys.argv[1:])
