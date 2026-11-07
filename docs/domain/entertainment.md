# Entertainment

## Purpose

A library of works you have seen or want to see, with tags, ratings, posters, and a period dashboard.

## Concepts

- **Title** — one work (film, series, book, podcast…).
- **Topic** — a user-defined tag (the SPA says *tag*).
- **Status** — `queued`, `in_progress`, `done`, `dropped`.

## Data model

### EntertainmentTopic

A user-defined tag on entertainment titles: finance, programming, physics, math, comfort-watch. Not a fixed enum. The SPA calls these tags. Attaching an unknown tag slug to a title creates it (name derived from the slug); attaching an archived one is rejected. Entertainment is a dedicated catalog of works you have seen or want to see. It does not dual-write entries and does not share tables with screen time. The screen category slug `entertainment` remains an app-minutes bucket.

| Field         | Type             | Notes                |
| ------------- | ---------------- | -------------------- |
| `id`          | int              | primary key          |
| `slug`        | str              | unique (`physics`)   |
| `name`        | str              |                      |
| `archived_at` | datetime \| None | UTC; never deleted   |

### EntertainmentTitle

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

An image is optional. Setting a remote URL clears the blob; uploading a file (≤2 MiB) clears the URL. On the wire, titles expose a single `image` field: the remote URL, `/entertainment/titles/{slug}/image` when a blob exists, or `null`.

### EntertainmentTitleTopic

Many-to-many link. Unique `(title_id, topic_id)`.

| Field      | Type | Notes                          |
| ---------- | ---- | ------------------------------ |
| `title_id` | int  | PK, FK to `EntertainmentTitle` |
| `topic_id` | int  | PK, FK to `EntertainmentTopic` |

## Rules and calculations

### Entertainment dashboard

`entertainment_dashboard_math` is a pure function of `EntertainmentTitleView` rows, `as_of`, and `period` (no wall clock, no image bytes). The current range is `bucket_for(as_of, period)` clipped so an in-progress week or month ends at `as_of`. Period mix uses `finished_on`. Library columns are the current catalog.

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
| `GET`    | `/entertainment/dashboard` | Period library dashboard (`period`, `as_of`)          | implemented |
| `GET`    | `/entertainment/topics`  | List subject tags                                       | implemented |
| `POST`   | `/entertainment/topics`  | Create a subject tag                                    | implemented |
| `GET`    | `/entertainment/topics/{slug}` | Get one subject tag                               | implemented |
| `PATCH`  | `/entertainment/topics/{slug}` | Update name                                       | implemented |
| `GET`    | `/entertainment/titles`  | List titles (`kind`, `status`, `topic`)                 | implemented |
| `POST`   | `/entertainment/titles`  | Add a work to the library                               | implemented |
| `GET`    | `/entertainment/titles/{slug}` | Get one title                                     | implemented |
| `PATCH`  | `/entertainment/titles/{slug}` | Update fields, status, rating, link, topics, or image URL | implemented |
| `DELETE` | `/entertainment/titles/{slug}` | Remove a title and its tag links                  | implemented |
| `POST`   | `/entertainment/lookup`  | Suggest name, kind, creator, poster for a link; `existing` slug if saved | implemented |
| `POST`   | `/entertainment/titles/from-link` | Look a link up and save it (`kind`, `status`, `topics`, `note` optional); 409 if saved | implemented |
| `PUT`    | `/entertainment/titles/{slug}/image` | Upload a poster blob                    | implemented |
| `DELETE` | `/entertainment/titles/{slug}/image` | Clear URL and blob                      | implemented |
| `GET`    | `/entertainment/titles/{slug}/image` | Serve the uploaded poster               | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_entertainment_topic` / `list_entertainment_topics` / `get_entertainment_topic` / `update_entertainment_topic` | Subject tags. `archived_at` is honored on list (`include_archived`) and import; there is no archive endpoint. |
| `create_entertainment_title` / `list_entertainment_titles` / `get_entertainment_title` / `update_entertainment_title` / `delete_entertainment_title` | Library titles. `list` can filter by `kind`, `status`, and `topic`. Marking `in_progress` stamps `started_on`; marking `done` stamps `finished_on`. `rating` is 1–5 or `None`; `link` must be http(s). Unknown tag slugs are created. Image URL and upload are mutually exclusive. Delete is hard and drops tag links. |
| `set_title_image` / `clear_title_image` / `get_title_image` | Upload (jpeg/png/webp/gif, ≤2 MiB), clear, or read the blob. |
| `lookup_link` / `create_title_from_link` | Link preview. Fetches the provider oEmbed JSON (YouTube, Vimeo, Spotify, SoundCloud) and, when title, author, or thumbnail is still missing, the page itself; `parse_page_meta` / `suggest_from_sources` (domain, pure) read Open Graph, Twitter card, `author`, and `<title>`. Kind comes from the host and path (Spotify episode/show → podcast, other Spotify → music, TMDB `/tv` → series, IMDb title → film, Goodreads → book…) and then `og:type`. Fetching is stdlib `urllib` (8 s timeout, 2 MiB cap) behind an injectable `Fetch`; the API takes it from `get_link_fetch` so tests override it. An unreachable page raises `UpstreamError` (HTTP 502). `create_title_from_link` refuses a link already saved (`AlreadyExistsError`) and derives a non-colliding slug (`-{kind}`, then `-{kind}-2`…). |
| `entertainment_dashboard` | Period dashboard from titles: finished/started in range, library columns, kind/topic mix, recently finished. |

## Screens

`/entertainment` is the library home: an add-from-link bar and one app-style icon per category (Videos = film/series/anime/video, Books, Podcasts, Music, Other; caption = saved count, red badge = in progress) above a dock with Everything and Insights. Icons are inline SVG (`CategoryIcon`), not image files. `/entertainment/:category` (`videos`, `books`, `podcasts`, `music`, `other`, or `all`) is a library table from `GET /entertainment/titles` with status chips, tag and minimum-rating filters, free-text search, and sortable columns (`?sort=` / `?dir=`). Status and rating are edited inline; the title opens an add/edit dialog (tags typed free-form, link, notes, poster, delete). Pasting a link into the dialog (or the home bar) calls `POST /entertainment/lookup` and prefills name, kind, creator, and poster; a link already saved is flagged. `/entertainment/insights` is the period dashboard from `GET /entertainment/dashboard`. Legacy `?cat=` and `?view=insights` URLs redirect. Category grouping, filtering, and sorting are client-side view logic in `web/src/lib/entertainment.ts`; counts on Insights stay server-computed.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_entertainment.py`, `tests/domain/test_entertainment_link.py`
- `tests/services/test_entertainment.py`, `tests/services/test_entertainment_lookup.py`
- `tests/api/test_entertainment.py`
- `web/src/lib/entertainment.test.ts`

## Status

Implemented.
