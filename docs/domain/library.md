# Library

## Purpose

A library of works you have seen or want to see, with tags, ratings, posters, and a period dashboard.

## Concepts

- **Title** — one work (film, series, book, podcast…).
- **Topic** — a user-defined tag (the SPA says *tag*).
- **Status** — `queued`, `in_progress`, `done`, `dropped`.

## Data model

### LibraryTopic

A user-defined tag on library titles: finance, programming, physics, math, comfort-watch. Not a fixed enum. The SPA calls these tags. Attaching an unknown tag slug to a title creates it (name derived from the slug); attaching an archived one is rejected. The library is a dedicated catalog of works you have seen or want to see. It does not dual-write entries and does not share tables with screen time. The screen category slug `entertainment` remains an app-minutes bucket.

| Field         | Type             | Notes                |
| ------------- | ---------------- | -------------------- |
| `id`          | int              | primary key          |
| `slug`        | str              | unique (`physics`)   |
| `name`        | str              |                      |
| `archived_at` | datetime \| None | UTC; never deleted   |

### LibraryTitle

One work in the library: a film, series, anime, video, book, podcast, album or track, or anything else. Status is user-asserted. Minutes belong on Screen Time, not here.

| Field            | Type             | Notes                                                                 |
| ---------------- | ---------------- | --------------------------------------------------------------------- |
| `id`             | int              | primary key                                                           |
| `slug`           | str              | unique (`interstellar`)                                               |
| `name`           | str              | display title                                                         |
| `kind`           | enum             | `film \| series \| anime \| video \| podcast \| book \| music \| other` |
| `creator`        | str \| None      | author, director, host, channel                                       |
| `recommended_by` | str \| None      | free text                                                             |
| `status`         | enum             | `queued \| in_progress \| done \| dropped`                            |
| `started_on`     | date \| None     | local; stamped to today when first moved to `in_progress` if unset    |
| `finished_on`    | date \| None     | local; stamped to today when marked `done` if unset                   |
| `progress`       | str \| None      | bookmark (`S2E5`, `ch. 12`), not time                                 |
| `note`           | str \| None      |                                                                       |
| `rating`         | int \| None      | 1–5; `None` is unrated                                                |
| `link`           | str \| None      | http(s) URL where the work lives (YouTube, Spotify, a drive folder)   |
| `image_url`      | str \| None      | remote poster URL                                                     |
| `image_bytes`    | bytes \| None    | uploaded poster in SQLite; mutually exclusive with `image_url`        |
| `image_media_type` | str \| None    | `image/jpeg`, `image/png`, `image/webp`, or `image/gif`               |
| `archived_at`    | datetime \| None | UTC                                                                   |
| `created_at`     | datetime         | UTC                                                                   |

Titles are removed with a hard delete (their tag links go with them), so the slug can be reused. `archived_at` is honored on list and import only.

An image is optional. Setting a remote URL clears the blob; uploading a file (≤2 MiB) clears the URL. On the wire, titles expose a single `image` field: the remote URL, `/library/titles/{slug}/image` when a blob exists, or `null`.

### LibraryTitleTopic

Many-to-many link. Unique `(title_id, topic_id)`.

| Field      | Type | Notes                          |
| ---------- | ---- | ------------------------------ |
| `title_id` | int  | PK, FK to `LibraryTitle` |
| `topic_id` | int  | PK, FK to `LibraryTopic` |

## Rules and calculations

### Library dashboard

`library_dashboard_math` is a pure function of `LibraryTitleView` rows, `as_of`, and `period` (no wall clock, no image bytes). The current range is `bucket_for(as_of, period)` clipped so an in-progress week or month ends at `as_of`. Period mix uses `finished_on`. Library columns are the current catalog.

- **Finished in range** — titles with `finished_on` in the clipped period.
- **Started in range** — titles with `started_on` in range.
- **Queued / in progress / done / dropped** — current library snapshot counts.
- **By kind / by topic** — counts of titles finished in range, with share of that finished set.
- **Recently finished** — latest `finished_on` on or before `as_of` (up to 8).
- **Library** — titles grouped by status.

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/library/dashboard` | Period library dashboard (`period`, `as_of`)          | implemented |
| `GET`    | `/library/topics`  | List subject tags                                       | implemented |
| `POST`   | `/library/topics`  | Create a subject tag                                    | implemented |
| `GET`    | `/library/topics/{slug}` | Get one subject tag                               | implemented |
| `PATCH`  | `/library/topics/{slug}` | Update name                                       | implemented |
| `GET`    | `/library/titles`  | List titles (`kind`, `status`, `topic`)                 | implemented |
| `POST`   | `/library/titles`  | Add a work to the library                               | implemented |
| `GET`    | `/library/titles/{slug}` | Get one title                                     | implemented |
| `PATCH`  | `/library/titles/{slug}` | Update fields, status, rating, link, topics, or image URL | implemented |
| `DELETE` | `/library/titles/{slug}` | Remove a title and its tag links                  | implemented |
| `POST`   | `/library/lookup`  | Suggest name, kind, creator, poster for a link; `existing` slug if saved | implemented |
| `POST`   | `/library/titles/from-link` | Look a link up and save it (`kind`, `status`, `topics`, `note` optional); 409 if saved | implemented |
| `PUT`    | `/library/titles/{slug}/image` | Upload a poster blob                    | implemented |
| `DELETE` | `/library/titles/{slug}/image` | Clear URL and blob                      | implemented |
| `GET`    | `/library/titles/{slug}/image` | Serve the uploaded poster               | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_library_topic` / `list_library_topics` / `get_library_topic` / `update_library_topic` | Subject tags. `archived_at` is honored on list (`include_archived`) and import; there is no archive endpoint. |
| `create_library_title` / `list_library_titles` / `get_library_title` / `update_library_title` / `delete_library_title` | Library titles. `list` can filter by `kind`, `status`, and `topic`. Marking `in_progress` stamps `started_on`; marking `done` stamps `finished_on`. `rating` is 1–5 or `None`; `link` must be http(s). Unknown tag slugs are created. Image URL and upload are mutually exclusive. Delete is hard and drops tag links. |
| `set_title_image` / `clear_title_image` / `get_title_image` | Upload (jpeg/png/webp/gif, ≤2 MiB), clear, or read the blob. |
| `lookup_link` / `create_title_from_link` | Link preview. Fetches the provider oEmbed JSON (YouTube, Vimeo, Spotify, SoundCloud) and, when title, author, or thumbnail is still missing, the page itself; `parse_page_meta` / `suggest_from_sources` (domain, pure) read Open Graph, Twitter card, `author`, and `<title>`. Kind comes from the host and path (Spotify episode/show → podcast, other Spotify → music, TMDB `/tv` → series, IMDb title → film, Goodreads → book…) and then `og:type`. Fetching is stdlib `urllib` (8 s timeout, 2 MiB cap) behind an injectable `Fetch`; the API takes it from `get_link_fetch` so tests override it. An unreachable page raises `UpstreamError` (HTTP 502). `create_title_from_link` refuses a link already saved (`AlreadyExistsError`) and derives a non-colliding slug (`-{kind}`, then `-{kind}-2`…). |
| `library_dashboard` | Period dashboard from titles: finished/started in range, library columns, kind/topic mix, recently finished. |

## Screens

The section is **Library** at `/library`, the same name as its API (`/library/…`) and code; the old `/entertainment/…` addresses redirect. `/library` is the library home: an add-from-link bar and one app-style icon per category (Videos = film/series/anime/video, Books, Podcasts, Music, Other; caption = saved count, red badge = in progress) above a dock with Everything and Insights. Icons are inline SVG (`CategoryIcon`), not image files. `/library/:category` (`videos`, `books`, `podcasts`, `music`, `other`, or `all`) is a library table from `GET /library/titles` with status chips, tag and minimum-rating filters, free-text search, and sortable columns (`?sort=` / `?dir=`). Status and rating are edited inline; the title opens an add/edit dialog (tags typed free-form, link, notes, poster, delete). Pasting a link into the dialog (or the home bar) calls `POST /library/lookup` and prefills name, kind, creator, and poster; a link already saved is flagged. `/library/insights` is the period dashboard from `GET /library/dashboard`. Legacy `?cat=` and `?view=insights` URLs redirect. Category grouping, filtering, and sorting are client-side view logic in `web/src/lib/library.ts`; counts on Insights stay server-computed.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_library.py`, `tests/domain/test_library_link.py`
- `tests/services/test_library.py`, `tests/services/test_library_lookup.py`
- `tests/api/test_library.py`
- `web/src/lib/library.test.ts`

## Status

Implemented.
