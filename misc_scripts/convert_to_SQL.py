"""
Convert the mapping in JSON generated by process_artists scripts to an SQL database for production use
"""

import sqlite3
import json
from pathlib import Path

database = Path("../app/data/enhanced_amq_database.sqlite")
nerfedDatabase = Path("../app/data/enhanced_amq_databas_nerfed.sqlite")
song_DATABASE_PATH = Path("../app/data/song_database.json")
group_DATABASE_PATH = Path("../app/data/song_database.json")
artist_DATABASE_PATH = Path("../app/data/artist_database.json")

with open(song_DATABASE_PATH, encoding="utf-8") as json_file:
    song_database = json.load(json_file)
with open(artist_DATABASE_PATH, encoding="utf-8") as json_file:
    artist_database = json.load(json_file)

RESET_DB_SQL = """PRAGMA foreign_keys = 0;
DROP TABLE IF EXISTS animes;
DROP TABLE IF EXISTS link_artist_name;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS line_ups;
DROP TABLE IF EXISTS link_artist_line_up;
DROP TABLE IF EXISTS link_song_artist;
DROP TABLE IF EXISTS link_anime_genre;
DROP TABLE IF EXISTS link_anime_tag;
DROP TABLE IF EXISTS link_anime_alt_name;
DROP TABLE IF EXISTS songs;
DROP VIEW IF EXISTS artistsNames;
DROP VIEW IF EXISTS artistsMembers;
DROP VIEW IF EXISTS artistsGroups;
DROP VIEW IF EXISTS animesFull;
DROP VIEW IF EXISTS songsAnimes;
DROP VIEW IF EXISTS songsArtists;
DROP VIEW IF EXISTS songsComposers;
DROP VIEW IF EXISTS songsArrangers;
DROP VIEW IF EXISTS songsFull;

PRAGMA foreign_keys = 1;

CREATE TABLE animes (
    "ann_id" INTEGER NOT NULL PRIMARY KEY,
    "anime_expand_name" VARCHAR(255) NOT NULL, 
    "anime_en_name" VARCHAR(255),
    "anime_jp_name" VARCHAR(255),
    "anime_season" VARCHAR(255),
    "anime_type" VARCHAR(255)
);

CREATE TABLE songs (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "ann_song_id" INTEGER,
    "ann_id" INTEGER NOT NULL,
    "song_type" INTEGER NOT NULL,
    "song_number" INTEGER NOT NULL,
    "song_name" VARCHAR(255) NOT NULL,
    "song_artist" VARCHAR(255) NOT NULL,
    "song_difficulty" FLOAT,
    "song_category" VARCHAR(255),
    "HQ" VARCHAR(255),
    "MQ" VARCHAR(255),
    "audio" VARCHAR(255),
    FOREIGN KEY ("ann_id")
        REFERENCES animes ("ann_id")
);

CREATE TABLE artists (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "is_vocalist" BIT NOT NULL,
    "is_performer" BIT NOT NULL,
    "is_composer" BIT NOT NULL,
    "is_arranger" BIT NOT NULL
);

CREATE TABLE line_ups (
    "artist_id" INTEGER NOT NULL,
    "line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    PRIMARY KEY (artist_id, line_up_id)
);

CREATE TABLE link_song_artist (
    "song_id" INTEGER NOT NULL,
    "artist_id" INTEGER NOT NULL,
    "artist_line_up_id" INTEGER NOT NULL,
    "role_type" TEXT CHECK(role_type IN ('vocalist', 'backing_vocalist', 'performer', 'composer', 'arranger')) NOT NULL,
    FOREIGN KEY ("song_id")
        REFERENCES songs ("id"),
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    FOREIGN KEY ("artist_line_up_id")
        REFERENCES line_ups ("line_up_id"),
    PRIMARY KEY (song_id, artist_id, artist_line_up_id, role_type)
);

create TABLE link_artist_line_up (
    "artist_id" INTEGER NOT NULL,
    "artist_line_up_id" INTEGER NOT NULL,
    "artist_role_type" TEXT CHECK(artist_role_type IN ('vocalist', 'backing_vocalist', 'performer', 'composer', 'arranger')) NOT NULL,
    "group_id" INTEGER NOT NULL,
    "group_line_up_id" INTEGER NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artists ("id"),
    FOREIGN KEY ("artist_line_up_id")
        REFERENCES line_ups ("line_up_id"),
    FOREIGN KEY ("group_id")
        REFERENCES line_ups ("artist_id"),
    FOREIGN KEY ("group_line_up_id")
        REFERENCES line_ups ("line_up_id"),
    PRIMARY KEY (artist_id, artist_line_up_id, artist_role_type, group_id, group_line_up_id)
);

create TABLE link_anime_genre (
    "ann_id" INTEGER NOT NULL,
    "genre" VARCHAR(255),
    FOREIGN KEY ("ann_id")
        REFERENCES animes ("ann_id"),
    PRIMARY KEY (ann_id, genre)
);

create TABLE link_anime_tag (
    "ann_id" INTEGER NOT NULL,
    "tag" VARCHAR(255),
    FOREIGN KEY ("ann_id")
        REFERENCES animes ("ann_id"),
    PRIMARY KEY (ann_id, tag)
);

CREATE TABLE link_artist_name (
    "inserted_order" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    "artist_id" INTEGER NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    FOREIGN KEY ("artist_id")
        REFERENCES artist ("id"),
    UNIQUE (artist_id, name)
);

create TABLE link_anime_alt_name (
    "ann_id" INTEGER NOT NULL,
    "name" VARCHAR(255),
    FOREIGN KEY ("ann_id")
        REFERENCES animes ("ann_id"),
    PRIMARY KEY (ann_id, name)
);


CREATE VIEW 
    artistsNames AS 
SELECT 
    orderedNames.inserted_order, 
    artists.id, 
    group_concat(orderedNames.name, "\$") AS names, 
    artists.is_vocalist, 
    artists.is_performer, 
    artists.is_composer,
    artists.is_arranger
FROM 
    artists
LEFT JOIN 
    (SELECT * FROM link_artist_name ORDER BY link_artist_name.inserted_order) AS orderedNames
ON artists.id = 
    orderedNames.artist_id
GROUP BY 
    artists.id;

CREATE VIEW 
    artistsMembers AS 
SELECT 
    artists.id, 
    link_artist_line_up.group_line_up_id,
    group_concat(link_artist_line_up.artist_role_type) as member_role_type, 
    group_concat(link_artist_line_up.artist_id) AS members, 
    group_concat(link_artist_line_up.artist_line_up_id) as members_line_up 
FROM 
    artists
LEFT JOIN 
    link_artist_line_up ON artists.id = link_artist_line_up.group_id 
GROUP BY 
    artists.id, 
    link_artist_line_up.group_line_up_id;

CREATE VIEW 
    artistsGroups AS 
SELECT 
    artists.id,
    group_concat(link_artist_line_up.artist_role_type) as groups_role_types,
    group_concat(link_artist_line_up.group_id) AS groups_ids,
    group_concat(link_artist_line_up.group_line_up_id) as groups_line_ups
FROM 
    artists 
LEFT JOIN 
    link_artist_line_up ON artists.id = link_artist_line_up.artist_id 
GROUP BY 
    artists.id,
    link_artist_line_up.artist_role_type;

CREATE VIEW 
    animesFull AS
SELECT 
    animes.ann_id, 
    animes.anime_expand_name, 
    animes.anime_jp_name, 
    animes.anime_en_name, 
    group_concat(link_anime_alt_name.name, "\$") AS anime_alt_names, 
    animes.anime_type, 
    animes.anime_season
FROM 
    animes
LEFT JOIN 
    link_anime_alt_name ON animes.ann_id = link_anime_alt_name.ann_id
GROUP BY 
    animes.ann_id;

CREATE VIEW 
    songsAnimes AS
SELECT 
    animesFull.ann_id, 
    animesFull.anime_expand_name, 
    animesFull.anime_jp_name, 
    animesFull.anime_en_name, 
    animesFull.anime_alt_names, 
    animesFull.anime_season, 
    animesFull.anime_type, 
    songs.id as song_id, 
    songs.ann_song_id, 
    songs.song_type, 
    songs.song_number, 
    songs.song_name, 
    songs.song_artist, 
    songs.song_difficulty, 
    songs.song_category, 
    songs.HQ, 
    songs.MQ, 
    songs.audio
FROM 
    animesFull
LEFT JOIN 
    songs ON animesFull.ann_id = songs.ann_id;

CREATE VIEW 
    songsArtists AS
SELECT 
    songs.id as song_id, 
    group_concat(link_song_artist.artist_id) AS artists,
    link_song_artist.role_type,
    group_concat(link_song_artist.artist_line_up_id) AS artist_line_up_id
FROM 
    songs 
LEFT JOIN 
    link_song_artist ON songs.id = link_song_artist.song_id
GROUP BY 
    songs.id,
    link_song_artist.role_type;

CREATE VIEW 
    songsFull AS
SELECT 
    songsAnimes.ann_id, 
    songsAnimes.anime_expand_name,
    songsAnimes.anime_jp_name, 
    songsAnimes.anime_en_name, 
    songsAnimes.anime_alt_names, 
    songsAnimes.anime_season, 
    songsAnimes.anime_type, 
    songsAnimes.song_id, 
    songsAnimes.ann_song_id, 
    songsAnimes.song_type, 
    songsAnimes.song_number, 
    songsAnimes.song_name, 
    songsAnimes.song_artist, 
    songsAnimes.song_difficulty, 
    songsAnimes.song_category, 
    MAX(CASE WHEN songsArtists.role_type = 'vocalist' THEN songsArtists.artists ELSE NULL END) AS vocalists, 
    MAX(CASE WHEN songsArtists.role_type = 'vocalist' THEN songsArtists.artist_line_up_id ELSE NULL END) AS vocalists_line_up, 
    MAX(CASE WHEN songsArtists.role_type = 'backing_vocalist' THEN songsArtists.artists ELSE NULL END) AS backing_vocalists, 
    MAX(CASE WHEN songsArtists.role_type = 'backing_vocalist' THEN songsArtists.artist_line_up_id ELSE NULL END) AS backing_vocalists_line_up, 
    MAX(CASE WHEN songsArtists.role_type = 'performer' THEN songsArtists.artists ELSE NULL END) AS performers, 
    MAX(CASE WHEN songsArtists.role_type = 'performer' THEN songsArtists.artist_line_up_id ELSE NULL END) AS performers_line_up, 
    MAX(CASE WHEN songsArtists.role_type = 'composer' THEN songsArtists.artists ELSE NULL END) AS composers, 
    MAX(CASE WHEN songsArtists.role_type = 'composer' THEN songsArtists.artist_line_up_id ELSE NULL END) AS composers_line_up, 
    MAX(CASE WHEN songsArtists.role_type = 'arranger' THEN songsArtists.artists ELSE NULL END) AS arrangers, 
    MAX(CASE WHEN songsArtists.role_type = 'arranger' THEN songsArtists.artist_line_up_id ELSE NULL END) AS arrangers_line_up, 
    songsAnimes.HQ, 
    songsAnimes.MQ, 
    songsAnimes.audio
FROM 
    songsAnimes
INNER JOIN 
    songsArtists ON songsAnimes.song_id = songsArtists.song_id
GROUP BY
    songsAnimes.song_id;
"""


def run_sql_command(cursor, sql_command, data=None):
    """
    Run the SQL command with nice looking print when failed (no)

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    sql_command : str
        The SQL command to run
    data : tuple, optional
        The data to insert in the command, by default None

    Returns
    -------
    list
        The result of the command
    """

    try:
        if data is not None:
            cursor.execute(sql_command, data)
        else:
            cursor.execute(sql_command)

        record = cursor.fetchall()

        return record

    except sqlite3.Error as error:
        if data is not None:
            for param in data:
                if type(param) == str:
                    sql_command = sql_command.replace("?", '"' + str(param) + '"', 1)
                else:
                    sql_command = sql_command.replace("?", str(param), 1)

        print(
            f"\n{error}\nError while running this command: {sql_command}\nData: {data}\n"
        )
        exit()


"""    try:
        cursor.execute(sql_command, data)
        record = cursor.fetchall()
        return record

    except sqlite3.Error as error:
        print(
            f"\nError while running this command: \n{sql_command}\n{error}\nData: {data}\n"
        )
        exit()

"""


def insert_new_artist(cursor, id, is_vocalist, is_performer, is_composer, is_arranger):
    """
    Insert a new artist in the database

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    id : int
        The id of the artist
    is_vocalist : bool
        True if the artist is a vocalist
    is_performer : bool
        True if the artist is a performer
    is_composer : bool
        True if the artist is a composer
    is_arranger: bool
        True if the artist is an arranger

    Returns
    -------
    int
        The id of the last row inserted
    """

    sql_insert_artist = "INSERT INTO artists(id, is_vocalist, is_performer, is_composer, is_arranger) VALUES(?, ?, ?, ?, ?);"

    run_sql_command(
        cursor,
        sql_insert_artist,
        [id, is_vocalist, is_performer, is_composer, is_arranger],
    )

    return cursor.lastrowid


def insert_new_line_up(cursor, artist_id, line_up_id):
    """
    Add a new line up configuration

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    artist_id : int
        The id of the artist
    line_up_id : int
        The id of the line up

    Returns
    -------
    int
        The id of the last row inserted
    """

    command = "INSERT INTO line_ups(artist_id, line_up_id) VALUES(?, ?);"
    run_sql_command(cursor, command, [artist_id, line_up_id])


def insert_artist_alt_name(cursor, id, name):
    """
    Add a new name to an artist

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    id : int
        The id of the artist
    name : str
        The name to add

    Returns
    -------
    None
    """

    sql_insert_artist_name = (
        "INSERT INTO link_artist_name(artist_id, name) VALUES(?, ?);"
    )

    run_sql_command(cursor, sql_insert_artist_name, (id, name))


def add_artist_to_line_up(
    cursor,
    artist_id,
    artist_line_up_id,
    artist_role_type,
    group_id,
    group_line_up_id,
):
    """
    Add an artist to a line up

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    artist_id : int
        The id of the artist
    artist_line_up_id : int
        The id of the line up of the artist
    artist_role_type : str
        The role of the artist in the group line up (vocalist, backing_vocalist, performer, composer or arranger)
    group_id : int
        The id of the group
    group_line_up_id : int
        The id of the line up of the group

    Returns
    -------
    None
    """

    sql_add_artist_to_group = "INSERT INTO link_artist_line_up(artist_id, artist_line_up_id, artist_role_type, group_id, group_line_up_id) VALUES(?, ?, ?, ?, ?)"

    run_sql_command(
        cursor,
        sql_add_artist_to_group,
        (
            artist_id,
            artist_line_up_id,
            artist_role_type,
            group_id,
            group_line_up_id,
        ),
    )


def insert_anime(
    cursor,
    ann_id,
    anime_expand_name,
    anime_en_name,
    anime_jp_name,
    anime_season,
    anime_type,
):
    """
    Insert a new anime in the database

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    ann_id : int
        The id of the anime on ANN
    anime_expand_name : str
        The name of the anime in expand database on AMQ
    anime_en_name : str
        The english name of the anime
    anime_jp_name : str
        The japanese name of the anime
    anime_season : str
        The season of the anime
    anime_type : str
        The type of the anime (TV, OVA, Movie, etc.)

    Returns
    -------
    None
    """

    sql_insert_anime = "INSERT INTO animes(ann_id, anime_expand_name, anime_en_name, anime_jp_name, anime_season, anime_type) VALUES(?, ?, ?, ?, ?, ?);"

    run_sql_command(
        cursor,
        sql_insert_anime,
        (
            ann_id,
            anime_expand_name,
            anime_en_name,
            anime_jp_name,
            anime_season,
            anime_type,
        ),
    )


def insert_song(
    cursor,
    ann_song_id,
    ann_id,
    song_type,
    song_number,
    song_name,
    song_artist,
    song_difficulty,
    song_category,
    HQ=-1,
    MQ=-1,
    audio=-1,
):
    """
    Insert a new song in the database and return the newly created song ID

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    ann_song_id : int
        The id of the song on AMQ
    ann_id : int
        The id of the anime on ANN
    song_type : str
        The type of the song (OP, ED, Insert, etc.)
    song_number : int
        The number of the song
    song_name : str
        The name of the song
    song_artist : str
        The artist of the song
    song_difficulty : str
        The difficulty of the song on AMQ
    song_category : str
        The category of the song (standard, character, chanting, etc.)
    HQ : int, optional
        The id of the HQ file, by default -1 (i.e not uploaded)
    MQ : int, optional
        The id of the MQ file, by default -1 (i.e not uploaded)
    audio : int, optional
        The id of the audio file, by default -1 (i.e not uploaded)
    """

    data = [
        ann_song_id,
        ann_id,
        song_type,
        song_number,
        song_name,
        song_artist,
        song_difficulty,
        song_category,
    ]

    sql_insert_song = "INSERT INTO songs (ann_song_id, ann_id, song_type, song_number, song_name, song_artist, song_difficulty, song_category"
    if HQ != -1:
        sql_insert_song += ", HQ, MQ, audio) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        data.extend([HQ, MQ, audio])
    else:
        sql_insert_song += ") VALUES(?, ?, ?, ?, ?, ?, ?, ?)"

    run_sql_command(cursor, sql_insert_song, list(data))

    return cursor.lastrowid


def link_song_artist(cursor, song_id, artist_id, artist_line_up_id, role_type):
    """
    Add a new link between a song and an artist

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    song_id : int
        The id of the song
    artist_id : int
        The id of the artist
    artist_line_up_id : int
        The id of the line up of the artist
    role_type: str
        The role of the artist in the song (vocalist, backing_vocalist, performer, composer or arranger)

    Returns
    -------
    None
    """

    sql_link_song_artist = "INSERT INTO link_song_artist(song_id, artist_id, artist_line_up_id, role_type) VALUES(?, ?, ?, ?);"

    run_sql_command(
        cursor,
        sql_link_song_artist,
        (song_id, artist_id, artist_line_up_id, role_type),
    )


def link_anime_tag(cursor, ann_id, tag):
    """
    Add a new link between an anime and a tag

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    ann_id : int
        The id of the anime on ANN
    tag : str
        The tag of the anime

    Returns
    -------
    None
    """

    sql_link_anime_tag = "INSERT INTO link_anime_tag(ann_id, tag) VALUES(?, ?);"

    run_sql_command(cursor, sql_link_anime_tag, (ann_id, tag))


def link_anime_genre(cursor, ann_id, genre):
    """
    Add a new link between an anime and a genre

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    ann_id : int
        The id of the anime on ANN
    genre : str
        The genre of the anime

    Returns
    -------
    None
    """

    sql_link_anime_genre = "INSERT INTO link_anime_genre(ann_id, genre) VALUES(?, ?);"

    run_sql_command(cursor, sql_link_anime_genre, (ann_id, genre))


def link_anime_alt_name(cursor, ann_id, altName):
    """
    Add a new link between an anime and an alternative name (i.e not Expand, JP or EN)

    Parameters
    ----------
    cursor : sqlite3.Cursor
        The cursor to run the command
    ann_id : int
        The id of the anime on ANN
    altName : str
        The alternative name of the anime

    Returns
    -------
    None
    """

    sql_link_anime_altName = (
        "INSERT INTO link_anime_alt_name(ann_id, name) VALUES(?, ?);"
    )

    run_sql_command(cursor, sql_link_anime_altName, (ann_id, altName))


# Databases reset
try:
    sqliteConnection = sqlite3.connect(database)
    cursor = sqliteConnection.cursor()
    for command in RESET_DB_SQL.split(";"):
        run_sql_command(cursor, command)
    sqliteConnection.commit()
    cursor.close()
    sqliteConnection.close()
except sqlite3.Error as error:
    print("\n", error, "\n")

try:
    sqliteConnection2 = sqlite3.connect(nerfedDatabase)
    cursor2 = sqliteConnection2.cursor()
    for command in RESET_DB_SQL.split(";"):
        run_sql_command(cursor2, command)
    sqliteConnection2.commit()
    cursor2.close()
    sqliteConnection2.close()
except sqlite3.Error as error:
    print("\n", error, "\n")

print("Reset successful :)")

# Databases connection
try:
    sqliteConnection = sqlite3.connect(database)
    cursor = sqliteConnection.cursor()
except sqlite3.Error as error:
    print("\n", error, "\n")

try:
    sqliteConnection2 = sqlite3.connect(nerfedDatabase)
    cursor2 = sqliteConnection2.cursor()
except sqlite3.Error as error:
    print("\n", error, "\n")

print("Connection successful :)")

# Database population with artist_database
for artist_id in artist_database:
    new_artist_id = insert_new_artist(
        cursor,
        artist_id,
        artist_database[artist_id]["is_vocalist"],
        artist_database[artist_id]["is_performer"],
        artist_database[artist_id]["is_composer"],
        artist_database[artist_id]["is_arranger"],
    )

    for name in (
        artist_database[artist_id]["artist_amq_names"]
        + artist_database[artist_id]["artist_alt_names"]
    ):
        insert_artist_alt_name(cursor, new_artist_id, name)
        insert_artist_alt_name(cursor2, new_artist_id, name)

    line_up_id = 0
    if len(artist_database[artist_id]["line_ups"]):
        for line_up in artist_database[artist_id]["line_ups"]:
            insert_new_line_up(cursor, new_artist_id, line_up_id)
            insert_new_line_up(cursor2, new_artist_id, line_up_id)
            for member in line_up["members"]:
                add_artist_to_line_up(
                    cursor,
                    member["id"],
                    member["line_up_id"],
                    member["role_type"],
                    new_artist_id,
                    line_up_id,
                )
                add_artist_to_line_up(
                    cursor2,
                    member["id"],
                    member["line_up_id"],
                    member["role_type"],
                    new_artist_id,
                    line_up_id,
                )
            line_up_id += 1

# Database population with song_database
for anime_ann_id in song_database:
    anime = song_database[anime_ann_id]

    insert_anime(
        cursor,
        anime_ann_id,
        anime["anime_expand_name"],
        anime["anime_en_name"] if "anime_en_name" in anime else None,
        anime["anime_jp_name"] if "anime_jp_name" in anime else None,
        anime["anime_season"] if "anime_season" in anime else None,
        anime["anime_type"] if "anime_type" in anime else None,
    )

    insert_anime(
        cursor2,
        anime_ann_id,
        anime["anime_expand_name"],
        anime["anime_en_name"] if "anime_en_name" in anime else None,
        anime["anime_jp_name"] if "anime_jp_name" in anime else None,
        anime["anime_season"] if "anime_season" in anime else None,
        anime["anime_type"] if "anime_type" in anime else None,
    )

    for tag in anime["anime_tags"]:
        link_anime_tag(cursor, anime_ann_id, tag)
        link_anime_tag(cursor2, anime_ann_id, tag)

    for genre in anime["anime_genres"]:
        link_anime_genre(cursor, anime_ann_id, genre)
        link_anime_genre(cursor2, anime_ann_id, genre)

    for altName in anime["anime_alt_names"]:
        link_anime_alt_name(cursor, anime_ann_id, altName)
        link_anime_alt_name(cursor2, anime_ann_id, altName)

    for song in anime["songs"]:
        links = song["links"]

        song_id = insert_song(
            cursor,
            song["ann_song_id"],
            anime_ann_id,
            song["song_type"],
            song["song_number"],
            song["song_name"],
            song["song_artist"],
            song["song_difficulty"] if "song_difficulty" in song else None,
            song["song_category"] if "song_category" in song else None,
            links["HQ"] if "HQ" in links.keys() else None,
            links["MQ"] if "MQ" in links.keys() else None,
            links["audio"] if "audio" in links.keys() else None,
        )

        song_id = insert_song(
            cursor2,
            song["ann_song_id"],
            anime_ann_id,
            song["song_type"],
            song["song_number"],
            song["song_name"],
            song["song_artist"],
            song["song_difficulty"] if "song_difficulty" in song else None,
            song["song_category"] if "song_category" in song else None,
            None,
            None,
            None,
        )

        if "vocalists" in song and song["vocalists"]:
            for artist in song["vocalists"]:
                link_song_artist(
                    cursor,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "vocalist",
                )
                link_song_artist(
                    cursor2,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "vocalist",
                )

        if "backing_vocalists" in song and song["backing_vocalists"]:
            for artist in song["backing_vocalists"]:
                link_song_artist(
                    cursor,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "backing_vocalist",
                )
                link_song_artist(
                    cursor2,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "backing_vocalist",
                )

        if "performers" in song and song["performers"]:
            for artist in song["performers"]:
                link_song_artist(
                    cursor,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "performer",
                )
                link_song_artist(
                    cursor2,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "performer",
                )

        if "composers" in song and song["composers"]:
            for artist in song["composers"]:
                link_song_artist(
                    cursor,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "composer",
                )
                link_song_artist(
                    cursor2,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "composer",
                )

        if "arrangers" in song and song["arrangers"]:
            for artist in song["arrangers"]:
                link_song_artist(
                    cursor,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "arranger",
                )
                link_song_artist(
                    cursor2,
                    song_id,
                    int(artist["id"]),
                    artist["line_up_id"],
                    "arranger",
                )


sqliteConnection.commit()
cursor.close()
sqliteConnection.close()

sqliteConnection2.commit()
cursor2.close()
sqliteConnection2.close()
print("Database population successful :)")