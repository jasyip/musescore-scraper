from urllib.parse import urlparse
import warnings

def _valid_url(url: str) -> bool:
    final_url = urlparse(url + '/' * int(not url.endswith('/')))
    if final_url.netloc != "musescore.com":
        warnings.warn('Network location is not "musescore.com".')
    elif re.fullmatch(r"\W+", final_url.path):
        warnings.warn('URL path is empty.')
    return (all([final_url.scheme, final_url.netloc, final_url.path])
            and '.' in final_url.netloc)
