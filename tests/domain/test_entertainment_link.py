from atlas.domain import (
    EntertainmentKind,
    kind_from_url,
    oembed_url,
    parse_page_meta,
    suggest_from_sources,
)

GOODREADS_PAGE = """
<html><head>
  <title>Dune by Frank Herbert | Goodreads</title>
  <meta property="og:title" content="Dune">
  <meta property="og:type" content="books.book">
  <meta property="og:site_name" content="Goodreads">
  <meta property="og:image" content="/covers/dune.jpg">
  <meta name="author" content="Frank Herbert">
</head><body></body></html>
"""


def test_oembed_url_only_for_known_providers():
    assert oembed_url("https://youtu.be/abc").startswith("https://www.youtube.com/oembed")
    assert "url=https%3A%2F%2Fopen.spotify.com" in oembed_url("https://open.spotify.com/album/x")
    assert oembed_url("https://www.goodreads.com/book/show/234225") is None


def test_kind_from_url_reads_host_and_path():
    assert kind_from_url("https://www.youtube.com/watch?v=1") is EntertainmentKind.VIDEO
    assert kind_from_url("https://open.spotify.com/episode/1") is EntertainmentKind.PODCAST
    assert kind_from_url("https://open.spotify.com/album/1") is EntertainmentKind.MUSIC
    assert kind_from_url("https://www.themoviedb.org/tv/1399") is EntertainmentKind.SERIES
    assert kind_from_url("https://www.imdb.com/title/tt0816692/") is EntertainmentKind.FILM
    assert kind_from_url("https://example.com/post") is None


def test_page_meta_suggestion_resolves_relative_images():
    meta = parse_page_meta(GOODREADS_PAGE)
    assert meta["title"] == "Dune by Frank Herbert | Goodreads"
    suggestion = suggest_from_sources("https://www.goodreads.com/book/show/234225", meta=meta)
    assert suggestion.name == "Dune"
    assert suggestion.kind is EntertainmentKind.BOOK
    assert suggestion.creator == "Frank Herbert"
    assert suggestion.image_url == "https://www.goodreads.com/covers/dune.jpg"


def test_oembed_wins_and_site_suffix_is_stripped():
    suggestion = suggest_from_sources(
        "https://www.youtube.com/watch?v=abc",
        oembed={
            "title": "But what is a neural network?",
            "author_name": "3Blue1Brown",
            "thumbnail_url": "https://i.ytimg.com/vi/abc/hqdefault.jpg",
        },
        meta={"title": "Something else - YouTube", "og:type": "video.other"},
    )
    assert suggestion.name == "But what is a neural network?"
    assert suggestion.creator == "3Blue1Brown"
    assert suggestion.kind is EntertainmentKind.VIDEO
    title_only = suggest_from_sources(
        "https://example.com/watch", meta={"title": "Big Buck Bunny - YouTube"}
    )
    assert title_only.name == "Big Buck Bunny"
    assert title_only.kind is None


def test_og_type_maps_to_kind_and_url_authors_are_ignored():
    suggestion = suggest_from_sources(
        "https://example.com/movie",
        meta={
            "og:title": "Arrival",
            "og:type": "video.movie",
            "article:author": "https://example.com/people/villeneuve",
            "og:image": "data:image/png;base64,AAAA",
        },
    )
    assert suggestion.kind is EntertainmentKind.FILM
    assert suggestion.creator is None
    assert suggestion.image_url is None
