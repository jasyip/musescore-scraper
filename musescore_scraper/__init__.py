#!/usr/bin/env python3

import argparse

from pathlib import Path
from typing import Optional, Union, List
from .MuseScraper import MuseScraper, AsyncMuseScraper
from .helper import _valid_url
import asyncio
from functools import partial



def _url_parse(url: str) -> str:
    if not _valid_url(url):
        raise argparse.ArgumentTypeError("Invalid URL.")
    return url

def _debug_path(path: str) -> Union[Path, str]:
    return Path(path) if path else path



def _main(args: Union[None, List[str], str] = None) -> None:

    parser = argparse.ArgumentParser(description="A MuseScore PDF scraper."
                                     + " Input a URL to a MuseScore score"
                                     + ", then outputs a multi-page PDF."
                                    )
    parser.add_argument("urls", nargs='+', type=_url_parse,
                        help="an amount of valid MuseScore score URLs"
                       )
    parser.add_argument("-o", "--output", nargs='+', type=Path, help="file destination(s)")
    parser.add_argument("-t", "--timeout", type=float, default=120,
                        help="how many seconds should be given"
                        + " before aborting a score URL to PDF conversion."
                       )
    parser.add_argument("-d", "--debug-log", type=_debug_path, nargs="?", const="",
                        help="receive debug messages, to a log file if destination provided."
                       )
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="stop receiving log messages in stdout."
                       )
    parser.add_argument("-p", "--proxy-server",
                        help="proxy server to use when connecting to MuseScore"
                       )

    args = parser.parse_args(args)

    if not (not args.output
            or (len(args.output) == 1 and args.output[0].is_dir())
            or len(args.urls) == len(args.output)
            ):
        parser.error("# of outputs must match # of urls"
                     + " or have single output as path to directory"
                     + " or omit output flag."
                    )


    outputs: List[Optional[Path]] = [None] * len(args.urls)
    def set_output(i: int, task: asyncio.Task) -> None:
        outputs[i] = task.result()


    async def run():
        tasks: List[asyncio.Task] = []

        async with AsyncMuseScraper(**{ k : v for k, v in args.__dict__.items()
                                       if k in {"debug_log",
                                                "timeout",
                                                "quiet",
                                                "proxy_server",
                                               }
                                      }) as ms:
            for i in range(len(args.urls)):
                if args.output:
                    task: asyncio.Task = asyncio.create_task(
                            ms.to_pdf(args.urls[i], args.output[i])
                    )
                else:
                    task: asyncio.Task = asyncio.create_task(ms.to_pdf(args.urls[i]))
                task.add_done_callback(partial(set_output, i))
                tasks.append(task)

            result = await asyncio.gather(*tasks)

        return result


    asyncio.get_event_loop().run_until_complete(run())




if __name__ == "__main__":
    main()
