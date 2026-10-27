"""Turn a pasted link into suggested library fields.

Pure: callers fetch the oEmbed JSON and page HTML; these functions only read them.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

from atlas.domain.enums import EntertainmentKind

_OEMBED_PROVIDERS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("youtube.com", "youtu.be"), "https://www.youtube.com/oembed?format=json&url="),
    (("vimeo.com",), "https://vimeo.com/api/oembed.json?url="),
    (("open.spotify.com",), "https://open.spotify.com/oembed?url="),
    (("soundcloud.com",), "https://soundcloud.com/oembed?format=json&url="),
)

_HOST_KINDS: tuple[tuple[str, EntertainmentKind], ...] = (
    ("youtube.com", EntertainmentKind.VIDEO),
    ("youtu.be", EntertainmentKind.VIDEO),
    ("vimeo.com", EntertainmentKind.VIDEO),
    ("twitch.tv", EntertainmentKind.VIDEO),
    ("podcasts.apple.com", EntertainmentKind.PODCAST),
    ("overcast.fm", EntertainmentKind.PODCAST),
    ("pca.st", EntertainmentKind.PODCAST),
    ("music.apple.com", EntertainmentKind.MUSIC),
    ("music.youtube.com", EntertainmentKind.MUSIC),
    ("soundcloud.com", EntertainmentKind.MUSIC),
    ("bandcamp.com", EntertainmentKind.MUSIC),
    ("goodreads.com", EntertainmentKind.BOOK),
    ("openlibrary.org", EntertainmentKind.BOOK),
    ("books.google.com", EntertainmentKind.BOOK),
    ("letterboxd.com", EntertainmentKind.FILM),
    ("myanimelist.net", EntertainmentKind.ANIME),
    ("anilist.co", EntertainmentKind.ANIME),
)

_OG_TYPE_KINDS: dict[str, EntertainmentKind] = {
    "video.movie": EntertainmentKind.FILM,
    "video.tv_show": EntertainmentKind.SERIES,
    "video.episode": EntertainmentKind.SERIES,
    "video.other": EntertainmentKind.VIDEO,
    "video": EntertainmentKind.VIDEO,
    "music.song": EntertainmentKind.MUSIC,
    "music.album": EntertainmentKind.MUSIC,
    "music.playlist": EntertainmentKind.MUSIC,
    "music.radio_station": EntertainmentKind.MUSIC,
    "book": EntertainmentKind.BOOK,
    "books.book": EntertainmentKind.BOOK,
}

_TITLE_SEPARATORS = (" - ", " | ", " · ", " — ", " – ")


@dataclass(frozen=True, slots=True)
class LinkSuggestion:
    link: str
    name: str | None = None
    kind: EntertainmentKind | None = None
    creator: str | None = None
    image_url: str | None = None


def host_of(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host.removeprefix("www.").removeprefix("m.")


def _matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def oembed_url(url: str) -> str | None:
    """The provider oEmbed endpoint for a link, when the host offers one."""
    host = host_of(url)
    for domains, endpoint in _OEMBED_PROVIDERS:
        if any(_matches(host, domain) for domain in domains):
            return endpoint + quote(url, safe="")
    return None


def kind_from_url(url: str) -> EntertainmentKind | None:
    host = host_of(url)
    path = urlsplit(url).path.lower()
    if _matches(host, "open.spotify.com"):
        if path.startswith(("/episode", "/show")):
            return EntertainmentKind.PODCAST
        return EntertainmentKind.MUSIC
    if _matches(host, "imdb.com") and path.startswith("/title"):
        return EntertainmentKind.FILM
    if _matches(host, "themoviedb.org"):
        if path.startswith("/tv"):
            return EntertainmentKind.SERIES
        if path.startswith("/movie"):
            return EntertainmentKind.FILM
    for domain, kind in _HOST_KINDS:
        if _matches(host, domain):
            return kind
    return None


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self._in_title = False
        self._title: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in attrs if value is not None}
        if tag == "title":
            self._in_title = True
            return
        if tag != "meta":
            return
        key = (values.get("property") or values.get("name") or "").strip().lower()
        content = (values.get("content") or "").strip()
        if key and content and key not in self.meta:
            self.meta[key] = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title.append(data)

    def result(self) -> dict[str, str]:
        title = " ".join("".join(self._title).split())
        if title and "title" not in self.meta:
            self.meta["title"] = title
        return self.meta


def parse_page_meta(html: str) -> dict[str, str]:
    """Open Graph, Twitter card, author, and `<title>` values keyed by lowercase name."""
    parser = _MetaParser()
    parser.feed(html)
    parser.close()
    return parser.result()


def suggest_from_sources(
    url: str,
    *,
    oembed: Mapping[str, Any] | None = None,
    meta: Mapping[str, str] | None = None,
) -> LinkSuggestion:
    """Merge oEmbed (preferred) and page meta into one suggestion for `url`."""
    oembed = oembed or {}
    meta = meta or {}
    site = _text(meta.get("og:site_name")) or _text(oembed.get("provider_name"))
    name = (
        _text(oembed.get("title"))
        or _text(meta.get("og:title"))
        or _text(meta.get("twitter:title"))
        or _text(meta.get("title"))
    )
    creator = (
        _text(oembed.get("author_name"))
        or _text(meta.get("music:musician_description"))
        or _plain_author(meta.get("author"))
        or _plain_author(meta.get("book:author"))
        or _plain_author(meta.get("article:author"))
    )
    image = (
        _text(oembed.get("thumbnail_url"))
        or _text(meta.get("og:image:secure_url"))
        or _text(meta.get("og:image"))
        or _text(meta.get("twitter:image"))
    )
    kind = kind_from_url(url) or _OG_TYPE_KINDS.get((meta.get("og:type") or "").strip().lower())
    return LinkSuggestion(
        link=url,
        name=_strip_site_suffix(name, site) if name else None,
        kind=kind,
        creator=creator,
        image_url=_absolute_http(url, image) if image else None,
    )


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _plain_author(value: object) -> str | None:
    text = _text(value)
    if text is None or text.startswith(("http://", "https://")):
        return None
    return text


def _strip_site_suffix(name: str, site: str | None) -> str:
    candidates = [site] if site else []
    candidates += ["YouTube", "Spotify", "Goodreads", "IMDb", "Letterboxd", "SoundCloud"]
    for candidate in candidates:
        for separator in _TITLE_SEPARATORS:
            suffix = f"{separator}{candidate}"
            if name.lower().endswith(suffix.lower()) and len(name) > len(suffix):
                return name[: -len(suffix)].strip()
    return name


def _absolute_http(base: str, value: str) -> str | None:
    resolved = urljoin(base, value)
    return resolved if resolved.startswith(("http://", "https://")) else None
