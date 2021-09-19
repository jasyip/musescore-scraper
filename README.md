# MuseScore Scraper

A MuseScore PDF scraper that serves as both a CLI and Python module. For non-subscription paying users. 

## Set-up

Run `pip install musescore-scraper` in your terminal.

## Usage

#### If as CLI

Execute `musescraper <url>`

#### If as Python module

```python
import musescore_scraper
musescore_scraper.to_pdf( <url> )
```

### Custom Output Destination

#### If as CLI

Execute `musescraper <url> -o <output destination>`

#### If as Python module

```python
import musescore_scraper
musescore_scraper.to_pdf( <url>, output= <output destination> )
```

### Debugging

#### If as CLI

Execute `musescraper <url> -d [<log file destination>]`

> Note that if a log file destination isn't provided, logs will be sent to stderr stream.

#### If as Python module

```python
import musescore_scraper
musescore_scraper.to_pdf( <url>, debug_log= <log file destination> )
```

> Note that if a empty string is provided instead, logs will be sent to stderr stream.
