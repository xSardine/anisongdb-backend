from .search_database import (
    get_anime_search_songs_list,
    get_ann_ids_songs_list,
    get_song_name_search_songs_list,
    get_artists_ids_songs_list,
    get_artists_search_songs_list,
    get_global_search_songs_list,
)
from .sql_calls import (
    connect_to_database,
    run_sql_command,
    extract_artist_database,
    add_logs,
)
from .utils import format_results, format_song_types_to_integer
from .io_classes import (
    Results,
    AnimeSearchParams,
    AnimeAnnIdSearchParams,
    ArtistIdSearchParams,
    SongSearchParams,
    ArtistSearchParams,
    GlobalSearch,
)

from random import randrange
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from decouple import config

"""
    This file contains the main FastAPI app
"""

description = """
## AnisongDB API

This is the documentation for AnisongDB's API.

## Contact

For any questions regarding this API, please contact xSardine#8168 on Discord.
For any technical questions, please create an issue on the corresponding repositories following <a href="https://github.com/xSardine/anisongDB-backend/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">guidelines</a>.

## Disclaimer

This API is still in development and is a work in progress.<br>
Be aware that even though I will try to keep incompatibilies between versions at a minimum, the API is subject to change.<br>
For performance reasons, the API is currently **limited to 350 results** per requests.<br>

## Endpoints

You will be able to:

* **Search songs by anime's ANN ID**.
* **Search songs by anime name**.
* **Search songs by song name**.
* **Search songs by artist name**.
* **Search songs by artist ID**.
* **Combine all the previous endpoints with different combinations using a global endpoint**.
"""

# Launch API
app = FastAPI(
    title="AnisongDB API",
    description=description,
    version="0.1.0",
    contact={"name": "xSardine#8168"},
)


# Get .env variables
# App
MAX_RESULTS_PER_SEARCH = config("MAX_RESULTS_PER_SEARCH", cast=int)
DATABASE_PATH = config("DATABASE_PATH")
LOGS_PATH = config("LOGS_PATH")

# Redis
REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT", cast=int)

print(
    f"""
    Config:
    - MAX_RESULTS_PER_SEARCH = {MAX_RESULTS_PER_SEARCH}
    - DATABASE_PATH = {DATABASE_PATH}
    - LOGS_PATH = {LOGS_PATH}
    - REDIS_HOST = {REDIS_HOST}
    - REDIS_PORT = {REDIS_PORT}
"""
)

# on app start_up, connect to redis for rate limiting


@app.on_event("startup")
async def startup():
    redis_db = redis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}/0", encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_db)


@app.post(
    "/api/get_50_random_songs",
    response_model=Results,
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def get_50_random_songs():
    cursor = connect_to_database()

    songIds = [randrange(39000) for _ in range(50)]

    artist_database = extract_artist_database()

    # Extract every song from song IDs
    get_songs_from_songs_ids = (
        f"SELECT * from songsFull WHERE songId IN ({','.join('?'*len(songIds))})"
    )
    songs = run_sql_command(cursor, get_songs_from_songs_ids, songIds)

    return format_results(artist_database, songs)


@app.post(
    "/api/anime_search",
    response_model=Results,
    description="""Search for songs by anime name<br>
    Anime name can be in English, Romaji, or some alternative name<br>
    <b>*However, only one of these names is updated regularly : the one available in Expand Library on AMQ</b><br>
    Not case sensitive, special characters are ignored.<br>
    To check the regex rules used, see https://github.com/xSardine/anisongDB-backend/blob/main/app/utils.py""",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def anime_search(body: AnimeSearchParams):
    start_time = time.time()
    if body.partial_match and len(body.anime_name) <= 3:
        raise HTTPException(
            status_code=400,
            detail="anime_name must be at least 4 characters long if partial_match is True",
        )

    song_types = format_song_types_to_integer(body.song_types)
    results = get_anime_search_songs_list(
        body.anime_name,
        body.partial_match,
        body.ignore_duplicates,
        song_types,
        body.song_categories,
        body.song_difficulty_range,
        body.anime_types,
        body.anime_seasons,
        body.anime_genres,
        body.anime_tags,
        MAX_RESULTS_PER_SEARCH,
    )

    add_logs(
        execution_time=time.time() - start_time,
        nb_results=len(results["songs"]),
        anime_name=body.anime_name,
        partial_match=body.partial_match,
        ignore_duplicates=body.ignore_duplicates,
        song_types=song_types,
        song_categories=body.song_categories,
        song_difficulty_range=body.song_difficulty_range,
        anime_types=body.anime_types,
        anime_seasons=body.anime_seasons,
        anime_genres=body.anime_genres,
        anime_tags=body.anime_tags,
        max_results_per_search=MAX_RESULTS_PER_SEARCH,
    )

    return results


@app.post(
    "/api/anime_annid_search",
    response_model=Results,
    description="Search for songs by ANN ID : ID of the anime in [Anime News Network](https://animenewsnetwork.com)",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def anime_ann_id_search(body: AnimeAnnIdSearchParams):
    start_time = time.time()
    song_types = format_song_types_to_integer(body.song_types)
    results = get_ann_ids_songs_list(
        [body.ann_id],
        body.ignore_duplicates,
        song_types,
        body.song_categories,
        body.song_difficulty_range,
        MAX_RESULTS_PER_SEARCH,
    )

    add_logs(
        execution_time=time.time() - start_time,
        nb_results=len(results["songs"]),
        ann_id=body.ann_id,
        ignore_duplicates=body.ignore_duplicates,
        song_types=song_types,
        song_categories=body.song_categories,
        song_difficulty_range=body.song_difficulty_range,
        max_results_per_search=MAX_RESULTS_PER_SEARCH,
    )

    return results


@app.post(
    "/api/song_name_search",
    response_model=Results,
    description="""Search for songs by song name<br>
    Not case sensitive, special characters are ignored.<br>
    To check the regex rules used, see https://github.com/xSardine/anisongDB-backend/blob/main/app/utils.py""",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def song_name_search(body: SongSearchParams):
    start_time = time.time()
    if body.partial_match and len(body.song_name) <= 3:
        raise HTTPException(
            status_code=400,
            detail="song_name must be at least 4 characters long if partial_match is True",
        )

    song_types = format_song_types_to_integer(body.song_types)
    results = get_song_name_search_songs_list(
        body.song_name,
        body.partial_match,
        body.ignore_duplicates,
        song_types,
        body.song_categories,
        body.song_difficulty_range,
        body.anime_types,
        body.anime_seasons,
        body.anime_genres,
        body.anime_tags,
        MAX_RESULTS_PER_SEARCH,
    )

    add_logs(
        execution_time=time.time() - start_time,
        nb_results=len(results["songs"]),
        song_name=body.song_name,
        partial_match=body.partial_match,
        ignore_duplicates=body.ignore_duplicates,
        song_types=song_types,
        song_categories=body.song_categories,
        song_difficulty_range=body.song_difficulty_range,
        anime_types=body.anime_types,
        anime_seasons=body.anime_seasons,
        anime_genres=body.anime_genres,
        anime_tags=body.anime_tags,
        max_results_per_search=MAX_RESULTS_PER_SEARCH,
    )

    return results


@app.post(
    "/api/artist_id_search",
    response_model=Results,
    description="Search for songs by artist ID",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def artist_Id_search(body: ArtistIdSearchParams):
    start_time = time.time()

    song_types = format_song_types_to_integer(body.song_types)
    results = get_artists_ids_songs_list(
        [body.artist_id],
        body.max_other_artists,
        body.group_granularity,
        body.credit_types,
        body.ignore_duplicates,
        song_types,
        body.song_categories,
        body.song_difficulty_range,
        body.anime_types,
        body.anime_seasons,
        body.anime_genres,
        body.anime_tags,
        MAX_RESULTS_PER_SEARCH,
    )

    add_logs(
        execution_time=time.time() - start_time,
        nb_results=len(results["songs"]),
        artist_id=body.artist_id,
        max_other_artists=body.max_other_artists,
        group_granularity=body.group_granularity,
        credit_types=body.credit_types,
        ignore_duplicates=body.ignore_duplicates,
        song_types=song_types,
        song_categories=body.song_categories,
        song_difficulty_range=body.song_difficulty_range,
        anime_types=body.anime_types,
        anime_seasons=body.anime_seasons,
        anime_genres=body.anime_genres,
        anime_tags=body.anime_tags,
        max_results_per_search=MAX_RESULTS_PER_SEARCH,
    )

    return results


@app.post(
    "/api/artist_search",
    response_model=Results,
    description="""Search for songs by artist name<br>
    Not case sensitive, special characters are ignored.<br>
    To check the regex rules used, see https://github.com/xSardine/anisongDB-backend/blob/main/app/utils.py""",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def artist_search(body: ArtistSearchParams):
    start_time = time.time()
    if body.partial_match and len(body.artist_name) <= 3:
        raise HTTPException(
            status_code=400,
            detail="artist_name must be at least 4 characters long if partial_match is True",
        )

    song_types = format_song_types_to_integer(body.song_types)
    results = get_artists_search_songs_list(
        body.artist_name,
        body.partial_match,
        body.max_other_artists,
        body.group_granularity,
        body.credit_types,
        body.ignore_duplicates,
        song_types,
        body.song_categories,
        body.song_difficulty_range,
        body.anime_types,
        body.anime_seasons,
        body.anime_genres,
        body.anime_tags,
        MAX_RESULTS_PER_SEARCH,
    )

    add_logs(
        execution_time=time.time() - start_time,
        nb_results=len(results["songs"]),
        artist_name=body.artist_name,
        partial_match=body.partial_match,
        max_other_artists=body.max_other_artists,
        group_granularity=body.group_granularity,
        credit_types=body.credit_types,
        ignore_duplicates=body.ignore_duplicates,
        song_types=song_types,
        song_categories=body.song_categories,
        song_difficulty_range=body.song_difficulty_range,
        anime_types=body.anime_types,
        anime_seasons=body.anime_seasons,
        anime_genres=body.anime_genres,
        anime_tags=body.anime_tags,
        max_results_per_search=MAX_RESULTS_PER_SEARCH,
    )

    return results


@app.post(
    "/api/global_search",
    response_model=Results,
    description="""Search for songs with a global search filter<br>
    Let you search with a combination of all other entry points. (Maximum 5)<br>
    The question is why would I do that ? Why don't I just get people to make multiple requests and do the combination of those themselves ?<br>
    The answer : I don't want to make multiple requests from the frontend of my website, which would means combining them with Javascript. And I'm bad at Javascript<br>
    This endpoint is basically here just so that I can do it in Python instead.<br>""",
    dependencies=[
        Depends(RateLimiter(times=5, seconds=15)),
        Depends(RateLimiter(times=20, seconds=90)),
    ],
)
async def global_search(body: GlobalSearch):
    if (
        not body.anime_searches
        and not body.song_name_searches
        and not body.artist_searches
        and not body.song_name_searches
        and not body.artist_searches
        and not body.song_name_searches
        and not body.artist_searches
    ):
        raise HTTPException(
            status_code=400,
            detail="You need to provide at least one search parameter",
        )

    if len(body.anime_searches + body.song_name_searches + body.artist_searches) > 5:
        raise HTTPException(
            status_code=400,
            detail="You can't provide more than 5 sub-search parameters",
        )

    for anime_search in body.anime_searches:
        if anime_search.partial_match and len(anime_search.anime_name) <= 3:
            raise HTTPException(
                status_code=400,
                detail="anime_name must be at least 4 characters long if partial_match is True",
            )

    for song_name_search in body.song_name_searches:
        if song_name_search.partial_match and len(song_name_search.song_name) <= 3:
            raise HTTPException(
                status_code=400,
                detail="song_name must be at least 4 characters long if partial_match is True",
            )

    for artist_search in body.artist_searches:
        if artist_search.partial_match and len(artist_search.artist_name) <= 3:
            raise HTTPException(
                status_code=400,
                detail="artist_name must be at least 4 characters long if partial_match is True",
            )

    songs_list = get_global_search_songs_list(
        body.anime_searches,
        body.song_name_searches,
        body.artist_searches,
        body.combination_logic,
    )

    return songs_list
