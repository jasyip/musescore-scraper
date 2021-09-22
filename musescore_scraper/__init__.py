#!/usr/bin/env python3

import argparse

from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Union
from .MuseScraper import MuseScraper, AsyncMuseScraper
import asyncio
from functools import partial

def _url_parse(url: str) -> str:
    tup = urlparse(url)
    return tup.scheme + "://" + tup.netloc + "/" + tup.path

def _debug_path(path: str) -> Union[Path, str]:
    return Path(path) if path else path

def _main(args: Union[None, list[str], str] = None) -> None:

    parser = argparse.ArgumentParser(description="A MuseScore PDF scraper."
                                     + " Input a URL to a MuseScore score"
                                     + ", then outputs a multi-page PDF.")
    parser.add_argument("urls", nargs='+', type=_url_parse,
                        help="an amount of valid MuseScore score URLs")
    parser.add_argument("-o", "--output", nargs='*', type=Path, help="file destination(s)")
    parser.add_argument("-t", "--timeout", type=int, help=
                        "how many milliseconds should be given before aborting.")
    parser.add_argument("-d", "--debug-log", type=_debug_path, nargs="?", const="",
                        help="receive debug messages, to a log file if destination provided."
                       )
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="stop receiving log messages in stdout."
                       )

    args = parser.parse_args(args)

    assert not args.output or len(args.urls) == len(args.output)

    outputs: list[Optional[Path]] = [None] * len(args.urls)
    def set_output(i: int, task: asyncio.Task) -> None:
        outputs[i] = task.result()


    async def run():
        tasks: list[asyncio.Task] = []

        async with AsyncMuseScraper(**{ k : v for k, v in args.__dict__.items()
                                       if k in {"debug_log", "timeout", "quiet"} }) as ms:
            for i in range(len(args.urls)):
                if args.output:
                    task: asyncio.Task = asyncio.create_task(
                            ms.to_pdf(args.urls[i], args.output[i])
                    )
                else:
                    task: asyncio.Task = asyncio.create_task(ms.to_pdf(args.urls[i]))
                task.add_done_callback(partial(set_output, i))
                tasks.append(task)

            result = await asyncio.wait_for(asyncio.gather(*tasks), args.timeout)

        return result


    asyncio.get_event_loop().run_until_complete(asyncio.wait_for(run(), args.timeout))




if __name__ == "__main__":
    main()
