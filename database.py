################################################################################
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# # OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>
################################################################################

import time
from datetime import datetime, timezone
from config import config
import mysql.connector

g_database = None

def connect():
    global g_database
    if g_database is not None and g_database.is_connected():
        #print("Database already connected")
        return g_database

    try:
        g_database = mysql.connector.connect(
            host = config['MYSQL']['ADDRESS'],
            user = config['MYSQL']['USERNAME'],
            password = config['MYSQL']['PASSWORD'],
            database = config['MYSQL']['DATABASE_NAME']
        )
        return g_database
    except Error as e:
        # TODO: If this fails, abort?
        logging.exception(e)
        return None


def add_member(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO badges (id) VALUES (%s)", (discord_id,))
    cursor.execute("REPLACE INTO stats (id) VALUES (%s)", (discord_id,))
    cursor.execute("REPLACE INTO devotion (id, name) VALUES (%s, %s)", (discord_id, ""))
    cursor.execute("REPLACE INTO victory (id, name) VALUES (%s, %s)", (discord_id, ""))
    cursor.execute("REPLACE INTO trophies (id, name) VALUES (%s, %s)", (discord_id, ""))
    cursor.execute("REPLACE INTO shark (id, name) VALUES (%s, %s)", (discord_id, ""))
    cursor.execute("REPLACE INTO win_rate_recent (id) VALUES (%s)", (discord_id,))
    cursor.execute("REPLACE INTO win_rate_all_time (id) VALUES (%s)", (discord_id,))
    cursor.execute("REPLACE INTO pod (id) VALUES (%s)", (discord_id,))
    database.commit()
    cursor.close()

def upsert_leaderboard(league, season, member_id, rank, week_01, week_02, week_03, week_04, week_05, week_06, week_07, week_08, week_09, week_10, week_11, week_12, week_13, total, average, drafts, trophies, win_rate):
	database = connect()
	cursor = database.cursor(prepared=True)
	cursor.execute("REPLACE INTO leaderboards (league, season, member_id, rank, week_01, week_02, week_03, week_04, week_05, week_06, week_07, week_08, week_09, week_10, week_11, week_12, week_13, points, average, drafts, trophies, win_rate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (league, season, member_id, rank, week_01, week_02, week_03, week_04, week_05, week_06, week_07, week_08, week_09, week_10, week_11, week_12, week_13, total, average, drafts, trophies, win_rate))
	database.commit()
	cursor.close()

def upsert_badge_card(discord_id, url):
    database = connect()
    cursor = database.cursor(prepared=True)
    timestamp = datetime.utcnow().timestamp()
    cursor.execute("REPLACE INTO badges (id, url, timestamp) VALUES (%s, %s, %s)", (discord_id, url, int(timestamp)))
    database.commit()
    cursor.close()

def get_badge_card(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT url, timestamp FROM badges WHERE id=%s", (discord_id,))
    badges = cursor.fetchone()
    if cursor.rowcount == 0:
        return None
    cursor.close()
    return badges

def upsert_badge_thumbnail(name, url):
    database = connect();
    cursor = database.cursor(prepared=True);
    cursor.execute("REPLACE INTO badge_thumbnails (name, url) VALUES (%s, %s)", (name, url));
    database.commit();
    cursor.close()

def get_badge_thumbnail(name):
    database = connect();
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT url FROM badge_thumbnails WHERE name=%s", (name,))
    thumb = cursor.fetchone()
    if(cursor.rowcount == 0):
        return None
    cursor.close()
    return thumb

def get_stats(discord_id):
    db = connect()
    cursor = db.cursor(prepared=True)
    cursor.execute("""
    SELECT
        stats.timestamp, -- 0
        devotion.name, devotion.value, devotion.next, -- 1, 2, 3
        victory.name, victory.value, victory.next, -- 4, 5, 6
        trophies.name, trophies.value, trophies.next, -- 7, 8, 9
        shark.name, shark.value, shark.next, -- 10, 11, 12
		hero.name, hero.value, hero.next, -- 13, 14, 15
        ROUND(win_rate_recent.league,2), ROUND(win_rate_recent.bonus,2), ROUND(win_rate_recent.overall,2), -- 16, 17, 18
        ROUND(win_rate_all_time.league,2), ROUND(win_rate_all_time.bonus,2), ROUND(win_rate_all_time.overall,2), -- 19, 20, 21
        pod.desired, pod.assigned -- 22, 23
    FROM stats
    INNER JOIN devotion ON stats.id = devotion.id
    INNER JOIN victory ON stats.id = victory.id
    INNER JOIN trophies ON stats.id = trophies.id
    INNER JOIN shark ON stats.id = shark.id
	INNER JOIN hero ON stats.id = hero.id
    INNER JOIN win_rate_recent ON stats.id = win_rate_recent.id
    INNER JOIN win_rate_all_time ON stats.id = win_rate_all_time.id
    INNER JOIN pod ON stats.id = pod.id
    WHERE stats.id=%s;
    """, (discord_id,))
    stats = cursor.fetchone()
    if cursor.rowcount == 0:
        return None
    cursor.close()
    return stats

def touch_stats(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    timestamp = datetime.utcnow().timestamp()
    cursor.execute("REPLACE INTO stats (id, timestamp) VALUES (%s, %s)", (discord_id, int(timestamp)))
    database.commit()
    cursor.close()

def upsert_devotion(discord_id, name, value, next):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO devotion (id, name, value, next) VALUES (%s, %s, %s, %s)", (discord_id, name, value, next))
    database.commit()
    cursor.close()

def upsert_victory(discord_id, name, value, next):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO victory (id, name, value, next) VALUES (%s, %s, %s, %s)", (discord_id, name, value, next))
    database.commit()
    cursor.close()

def upsert_trophies(discord_id, name, value, next):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO trophies (id, name, value, next) VALUES (%s, %s, %s, %s)", (discord_id, name, value, next))
    database.commit()
    cursor.close()

def upsert_shark(discord_id, name, value, next, is_shark):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO shark (id, name, value, next, is_shark) VALUES (%s, %s, %s, %s, %s)", (discord_id, name, value, next, is_shark))
    database.commit()
    cursor.close()

def upsert_hero(discord_id, name, value, next):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO hero (id, name, value, next) VALUES (%s, %s, %s, %s)", (discord_id, name, value, next))
    database.commit()
    cursor.close()

def upsert_win_rate_recent(discord_id, league, bonus, overall):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO win_rate_recent (id, league, bonus, overall) VALUES (%s, %s, %s, %s)", (discord_id, league, bonus, overall))
    database.commit()
    cursor.close

def upsert_win_rate_all_time(discord_id, league, bonus, overall):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO win_rate_all_time (id, league, bonus, overall) VALUES (%s, %s, %s, %s)", (discord_id, league, bonus, overall))
    database.commit()
    cursor.close

def set_assigned_pod(discord_id, pod):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("UPDATE pod SET assigned=%s WHERE id=%s", (pod, discord_id))
    database.commit()
    cursor.close()

def set_desired_pod(discord_id, pod):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("UPDATE pod SET desired=%s WHERE id=%s", (pod, discord_id))
    database.commit()
    cursor.close()

def clear_commands():
    database = connect()
    cursor = database.cursor();
    cursor.execute("TRUNCATE TABLE commands");
    database.commit()
    cursor.close()

def add_command(name, team, content):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("INSERT INTO commands (name, team, content) VALUES (%s, %s, %s)", (name, team, content))
    database.commit();
    cursor.close()

def get_command_by_name(name):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT team, content FROM commands WHERE name=%s", (name,))
    results = cursor.fetchone()
    if results is None:
        return None
    team = results[0]
    content = results[1]
    cursor.close()
    return (bool(team), content)

def get_pods(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT desired, assigned FROM pod WHERE id=%s", (discord_id,))
    results = cursor.fetchone()
    if cursor.rowcount != 1:
        return None
    desired = results[0];
    assigned = results[1];
    cursor.close()
    return (desired, assigned)

def get_desired_pod(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT desired FROM pod WHERE id=%s", (discord_id,))
    results = cursor.fetchone()
    if cursor.rowcount == 0:
        return None
    desired = results[0]
    cursor.close()
    return desired

def set_pods(discord_id, desired, assigned):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("REPLACE INTO pod (id, desired, assigned) VALUES (%s, %s, %s)", (discord_id, desired, assigned))
    database.commit()
    cursor.close()

def get_win_rate_recent(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT ROUND(league,2), ROUND(bonus,2), ROUND(overall,2) FROM win_rate_recent WHERE id=%s", (discord_id,))
    results = cursor.fetchone()
    if cursor.rowcount == 0:
        return None
    league = results[0]
    bonus = results[1]
    overall = results[2]
    cursor.close()
    return (league, bonus, overall)

def get_win_rate_all_time(discord_id):
    database = connect()
    cursor = database.cursor(prepared=True)
    cursor.execute("SELECT ROUND(league,2), ROUND(bonus,2), ROUND(overall,2) FROM win_rate_all_time WHERE id=%s", (discord_id,))
    results = cursor.fetchone()
    if cursor.rowcount == 0:
        return None
    league = results[0]
    bonus = results[1]
    overall = results[2]
    cursor.close()
    return (league, bonus, overall)

def get_all_pod_and_win_rates():
    database = connect()
    cursor = database.cursor()
    cursor.execute("SELECT pod.id, pod.desired, pod.assigned, ROUND(win_rate_recent.overall,2) FROM pod INNER JOIN win_rate_recent ON pod.id=win_rate_recent.id")
    results = cursor.fetchall()
    cursor.close()
    return results

def upsert_xmage_version(version):
    database = connect()
    cursor = database.cursor(prepared=True)
    timestamp = datetime.utcnow().timestamp()
    cursor.execute("REPLACE INTO xmage_version (version, timestamp) VALUES (%s, %s)", (version, int(timestamp)))
    database.commit()
    cursor.close()
