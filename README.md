# MuseScore Scraper

A MuseScore PDF scraper that serves as both a CLI and Python module. For non-subscription paying users.

## Set-up

Run `pip install musescore-scraper` in your terminal.

PyPI page for more details: [https://pypi.org/project/musescore-scraper/](https://pypi.org/project/musescore-scraper/)

## Usage

#### If as CLI

Execute `musescraper <urls>` with as many MuseScore score URLs as desired.

#### If as Python module

```python
from musescore_scraper import MuseScraper
with MuseScraper() as ms:
    ms.to_pdf( <url> )
```

### Custom Output Destination

#### If as CLI

Execute `musescraper <urls> -o <output destinations or just a shared directory>`

#### If as Python module

```python
from musescore_scraper import MuseScraper
with MuseScraper() as ms:
    ms.to_pdf( <url>, output= <output destination or just a shared directory> )
```

### Debugging

#### If as CLI

Execute `musescraper <urls> -d [<log file destination>]`

> Note that if a log file destination isn't provided, logs will be sent to stderr stream.

#### If as Python module

```python
from musescore_scraper import MuseScraper
with MuseScraper(debug_log= <log file destination> ) as ms:
    ms.to_pdf( <url> )
```

> Note that if a empty string is provided instead, logs will be sent to stderr stream.

### Asynchronous Python class

Useful if more than one score shall be downloaded.

```python
from musescore_scraper import AsyncMuseScraper
from typing import Optional, List
import asyncio
from functools import partial

urls: List[str] = [ <urls> ]
outputs: List[Optional[Path]] = [None] * len(urls)
def set_output(i: int, task: asyncio.Task) -> None:
    outputs[i] = task.result()

async def run():
    tasks: List[asyncio.Task] = []

    async with AsyncMuseScraper() as ms:
        for i in range(len(urls)):
            task: asyncio.Task = asyncio.create_task(ms.to_pdf(urls[i]))
            task.add_done_callback(partial(set_output, i))
            tasks.append(task)

        result = await asyncio.gather(*tasks)

    return result


asyncio.get_event_loop().run_until_complete(run())
```

# Documentation

Available at [https://musescore-scraper.readthedocs.io/en/stable/musescore_scraper.html#module-musescore_scraper.MuseScraper](https://musescore-scraper.readthedocs.io/en/stable/musescore_scraper.html#module-musescore_scraper.MuseScraper)
