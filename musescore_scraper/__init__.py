#!/usr/bin/env python3

import argparse
from pathlib import Path
from urllib.parse import urlparse
from .MuseScraper import MuseScraper, AsyncMuseScraper





def main() -> list[Path]:
    """
    This main function is used as a CLI and gets its arguments from sys.argv

    :rtype: Output destinations as ``list[pathlib.Path]``.
    """
    parser = argparse.ArgumentParser(description="A MuseScore PDF scraper."
                                     + " Input a URL to a MuseScore score"
                                     + ", then outputs a multi-page PDF.")
    parser.add_argument("urls", nargs='+', type=urlparse,
                        help="an amount of valid MuseScore score URLs")
    parser.add_argument("-o", "--output", type=Path, help="file destination")
    parser.add_argument("-t", "--timeout", type=int, help=
                        "how many milliseconds should be given before aborting.")
    parser.add_argument("-d", "--debug-log", type=Path, nargs="?", const="",
                        help="receive debug messages, to a log file if destination provided."
                       )
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="stop receiving log messages in stdout."
                       )

    args = parser.parse_args()

    outputs = []

    with MuseScraper(**{ k : v for k, v in args.__dict__.items()
            if k in {"debug_log", "timeout", "quiet"} }) as musescraper:
        for url in args.urls:
            outputs.append(musescraper.to_pdf(url.path, args.output))

    return outputs



if __name__ == "__main__":
    main()
