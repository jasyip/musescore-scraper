from urllib.parse import urlparse

def _valid_url(url: str) -> bool:
    final_url = urlparse(url + '/' * int(not url.endswith('/')))
    return (all([final_url.scheme, final_url.netloc, final_url.path])
            and '.' in final_url.netloc)
