# MuseScore Scraper

A MuseScore PDF scraper that serves as both a CLI and Python module. For non-subscription paying users. 

## Set-up

Run `pip install musescore-scraper` in your terminal.

## Usage

#### If as CLI

Execute `musescraper <url>`

#### If as Python module

```python
from musescore_scraper import MuseScraper
with MuseScraper() as ms:
    ms.to_pdf( <url> )
```

### Custom Output Destination

#### If as CLI

Execute `musescraper <url> -o <output destination>`

#### If as Python module

```python
from musescore_scraper import MuseScraper
with MuseScraper() as ms:
    ms.to_pdf( <url>, output= <output destination> )
```

### Debugging

#### If as CLI

Execute `musescraper <url> -d [<log file destination>]`

> Note that if a log file destination isn't provided, logs will be sent to stderr stream.

#### If as Python module

```python
from musescore_scraper import MuseScraper
with MuseScraper(debug_log= <log file destination> ) as ms:
    ms.to_pdf( <url> )
```

> Note that if a empty string is provided instead, logs will be sent to stderr stream.
