#!/usr/bin/env python3

from typing import Union, Optional, Any

import os
import sys
from pkgutil import get_data

from abc import ABC

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
import warnings
from operator import itemgetter




class BaseMuseScraper(ABC):

    def __init__(
            self,
            *,
            debug_log: Union[None, str, Path] = None,
            timeout: int = 120 * 1000,
            quiet: bool = False,
    ):
        self._debug: bool = debug_log is not None
        self.timeout: int = timeout
        self.closed: bool = False

        logging_kwargs: dict[str, Any] = {}
        
        log_level: int = (logging.DEBUG if debug_log else
                          logging.INFO if not quiet else
                          logging.WARNING
                         )
        logging_kwargs["level"] = log_level

        if debug_log:
            logging_kwargs["filename"] = Path(debug_log)
            # Why the hell did pyppeteer set the handler for themselves?
            # They should've used logging.basicConfig() for fuck's sake
            pyppeteer._logger.removeHandler(pyppeteer._log_handler)
            pyppeteer_log_handler: logging.FileHandler = logging.FileHandler(debug_log)
            pyppeteer_log_handler.setFormatter(pyppeteer._formatter)
            pyppeteer._logger.addHandler(pyppeteer_log_handler)

        logging.basicConfig(**logging_kwargs)

        self._logger: logging.Logger = logging.getLogger(__name__)


    async def close(self) -> None:
        if not self.closed:
            await self._browser.close()
            self.closed = True
        else:
            warnings.warn("Already closed.", RuntimeWarning)


    async def _pyppeteer_main(
            self,
            url: str,
    ) -> list[str]:

        page: pyppeteer.page.Page = await self._browser.newPage()
        await page.setViewport({ "width" : 1000, "height" : 1000 } )
        await page.goto(url)

        score_name: str = (
                await (await (
                        await page.querySelector("h1")).getProperty("innerText")).jsonValue())
        score_creator: str = await (await (
                await page.querySelector("h2")).getProperty("innerText")).jsonValue()

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
            "Creator": score_creator,
            # "Date released": str(await get_score_release_date()),
            "Keywords": await get_score_tags(),
        }
        
        # svgs = await page.evaluate(bytes(get_data("musescore_scraper", "script.js"), "utf-8"))
        svgs: list[str] = await page.evaluate(str(get_data("musescore_scraper",
                                                           "script.js",
                                                          ), "utf-8"))

        await page.close()


        return {
            "svgs" : svgs,
            "info": info_dict,
        }


    def _convert(self, output: Union[None, str, Path], data: dict[str, Any]) -> str:
        svgs, info_dict = itemgetter("svgs", "info")(data)


        for k, v in info_dict.items():
            self._logger.info(f'Collected "{k}" metadata from score: "{v}"')

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


        def eval_expression(input_string: str) -> str:
            windows_regex: str = r"[0x00-0x1f\"*/:<>?\\|]"
            darwin_regex: str = r"[: ]"
            linux_regex: str = (r"[\x00/]" if os.environ.keys() & {"is_wsl", "wsl_distro_name"}
                            else windows_regex)
            return locals()[input_string]

        if not output:
            output = re.sub(eval_expression(
                    platform.system().lower() + "_regex"), '_', info_dict["Title"])

        if isinstance(output, str):
            output = Path(output)
        output = output.with_suffix(".pdf")
        
        if self._debug and Path().resolve().is_relative_to(Path(__file__).parents[1]):
            pdfs_folder: Path = Path("PDFs")
            if not pdfs_folder.is_dir():
                pdfs_folder.mkdir()
            output = Path("PDFs") / output

        if self._debug:
            output = output.with_stem(time.strftime("%Y%m%d-%H%M%S") + ' ' + output.stem)

        will_rewrite: bool = output.is_file()

        with output.open("wb") as o:
            merger.write(o)

        output = output.resolve()
        log_message: str = f'PDF { "over" * int(will_rewrite) }written to'
        try:
            self._logger.info(f'{log_message} "{output.relative_to(Path().resolve())}"')
        except ValueError:
            self._logger.info(f'{log_message} "{output}"')


        return output



class AsyncMuseScraper(BaseMuseScraper):

    async def _check_browser(self) -> None:
        for task in asyncio.all_tasks():
            if task.get_name() == str(id(self)):
                self._browser = await asyncio.wait_for(task, self.timeout)
                break

    def __init__(
            self,
            *,
            debug_log: Union[None, str, Path] = None,
            timeout: int = 120 * 1000,
            quiet: bool = False,
    ):
        locs: dict[str, Any] = locals()
        super().__init__(**{ k : v for k, v in locs.items() if not re.match(r"_|self$", k) })

        task: asyncio.Task = asyncio.create_task(pyppeteer.launch(), name=id(self))


    async def _pyppeteer_main(
            self,
            url: str,
    ) -> list[str]:
        locs = locals()
        await self._check_browser()
        return await super()._pyppeteer_main(
                **{ k : v for k, v in locs.items() if not re.match(r"_|self$", k) })

    async def close(self) -> None:
        """
        Closes browser. Should be called after all uses.

        :rtype: ``None``
        """
        await self._check_browser()
        await super().close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback) -> None:
        await self.close()

    async def to_pdf(
            self,
            url: str,
            output: Union[None, str, Path] = None,
    ) -> Path:
        """
        Extracts the SVGs from a MuseScore score URL asynchronously.
        Then converts each one to a PDF then merges each page into one multi-page PDF.

        :param url: MuseScore score URL to extract PDF from.
        :type url: str

        :param output: File destination to write PDF to.
            If **None**, file name will be the extracted score title.
        :type output: Union[None, str, pathlib.Path] = None

        :rtype: Output destination as ``pathlib.Path`` object.
            May or may not differ depending on input arguments.
        """
        return self._convert(output, await asyncio.wait_for(
                self._pyppeteer_main(url), self.timeout
        ))




class MuseScraper(BaseMuseScraper):

    def __init__(
            self,
            *,
            debug_log: Union[None, str, Path] = None,
            timeout: int = 120 * 1000,
            quiet: bool = False,
    ):
        locs: dict[str, Any] = locals()
        super().__init__(**{ k : v for k, v in locs.items() if not re.match(r"_|self$", k) })
        self._browser: pyppeteer.browser.Browser = asyncio.get_event_loop().run_until_complete(
                asyncio.wait_for(pyppeteer.launch(), self.timeout)
        )


    def __enter__(self):
        return self

    def close(self) -> None:
        """
        Closes browser. Should be called after all uses.

        :rtype: ``None``
        """
        asyncio.get_event_loop().run_until_complete(super().close())


    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.close()


    def to_pdf(
            self,
            url: str,
            output: Union[None, str, Path] = None,
    ) -> Path:
        """
        Extracts the SVGs from a MuseScore score URL.
        Then converts each one to a PDF then merges each page into one multi-page PDF.

        :param url: MuseScore score URL to extract PDF from.
        :type url: str

        :param output: File destination to write PDF to.
            If **None**, file name will be the extracted score title.
        :type output: Union[None, str, pathlib.Path] = None

        :rtype: Output destination as ``pathlib.Path`` object.
            May or may not differ depending on input arguments.
        """
        return self._convert(output, asyncio.get_event_loop().run_until_complete(
                asyncio.wait_for(self._pyppeteer_main(url), self.timeout)
        ))
