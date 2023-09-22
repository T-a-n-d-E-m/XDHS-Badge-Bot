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

import os
import io
import uuid
import time
from flask import Flask, request, jsonify, abort, send_from_directory
from pdf2image import convert_from_bytes  # Note: Needs the poppler-utils package installed with `install-pkg poppler-utils`
from threading import Thread
import base64
import database
import logging
import json
from imgur import upload_to_imgur
from config import config
import database


API_KEY = config['FLASK']['API_KEY']  # Needs to be sent with the HTTP header or the request will be rejected TODO Needs a better name

app = Flask(__name__)


@app.route('/')
def main():
	return "up", 200


# TODO: Get rid of all static stuff and use imgur and Replit instead
@app.route('/static/<path:filename>', methods=['GET'])
def get_image(filename):
	try:
		return send_from_directory('/opt/XDHS-Badge-Bot/static', filename)
	except FileNotFoundError:
		abort(404)



@app.route("/pdf2png", methods=['POST'])
def pdf2png():
	if request.headers.get('API_KEY') == API_KEY:
		width = request.json['width']
		height = request.json['height']
		dpi = request.json['dpi']
		user_id = request.json['user_id']
		pdf = base64.b64decode(request.json['bytes'])
		images = convert_from_bytes(pdf_file=pdf, dpi=dpi)
		cropped = images[0].crop((0, 0, width, height))
		filename = str(uuid.uuid4()) + '.png'  # TODO: does .png need to be added?

		buffer = io.BytesIO()
		cropped.save(buffer, format='PNG')  #, poppler_path=POPPLER_PATH)
		url = upload_to_imgur(buffer.getvalue(), filename)

		logging.info(F"/pdf2png: width:{width} height:{height} dpi:{dpi} discord_id:{user_id} url:{url} timestamp:{int(time.time())}")

		# If the user_id field is set, this is a badge card. Add it to the database for use by the ?badges command.
		if user_id != "":
			database.upsert_badge_card(user_id, url)
			response = jsonify({'url': url})
			return response, 200
		else:
			return "", 403



#@app.route('/badge_thumbnails/<path:filename>', methods=['GET'])
#def get_badge_thumbnail(filename):
#	try:
#		return send_from_directory('/home/runner/XDHS/badge_thumbnails',
#								   filename)
#	except FileNotFoundError:
#		abort(404)



@app.route("/upload_leaderboard", methods=['POST'])
def upload_leaderboard():
	if request.headers.get('API_KEY') == API_KEY:
		data = request.get_json()

		season = int(data['season'])
		league = data['league']

		# NOTE: member_id is sent from the spreadsheet as a string as Javascript (being invented by dipshits) stores integers as doubles and member_id might get rounded if sent as a number...
		for row in data['rows']:
			database.upsert_leaderboard(league, season, int(row['member_id']), row['rank'], row['week_01'], row['week_02'], row['week_03'], row['week_04'], row['week_05'], row['week_06'], row['week_07'], row['week_08'], row['week_09'], row['week_10'], row['week_11'], row['week_12'], row['week_13'], row['points'], row['average'], row['drafts'], row['trophies'], row['win_rate'])

		return "", 200

	else:
		logging.warning("/upload_leaderboard: API_KEY not sent")
		return "", 403


@app.route("/upload_stats", methods=['POST'])
def upload_stats():
	if request.headers.get('API_KEY') == API_KEY:
		data = request.get_json()
		user_id = int(data['user_id'])

		discord_id = data['user_id']
		database.touch_stats(discord_id)
		database.upsert_devotion(discord_id, data['devotion']['name'], int(data['devotion']['value']), int(data['devotion']['next']))
		database.upsert_victory(discord_id, data['victory']['name'], int(data['victory']['value']), int(data['victory']['next']))
		database.upsert_trophies(discord_id, data['trophies']['name'], int(data['trophies']['value']), int(data['trophies']['next']))
		database.upsert_shark(discord_id, data['shark']['name'], int(data["shark"]["value"]), int(data["shark"]["next"]), bool(data["shark"]["is_shark"]))
		database.upsert_hero(discord_id, data['hero']['name'], int(data['hero']['value']), int(data['hero']['next']))
		database.upsert_win_rate_recent(discord_id, float(data['win_rate_recent']['league']), float(data['win_rate_recent']['bonus']), float(data['win_rate_recent']['overall']))
		database.upsert_win_rate_all_time( discord_id, float(data['win_rate_all_time']['league']), float(data['win_rate_all_time']['bonus']), float(data['win_rate_all_time']['overall']))

		logging.info(F"/upload_stats: discord_id:{user_id}")

		pod = database.get_pods(discord_id)
		if pod is None:
			# Member has not used the pod command yet
			database.set_pods(discord_id, 0, 0)
			pod = [0, 0]

		# Return the Pod roles for this user.
		retval = {
			'has_pod': True,
			'pod': {
				'desired': pod[0],
				'assigned': pod[1]
			}
		}
		return retval, 200
	else:
		logging.warning("/upload_stats: API_KEY not sent")
		return "", 403


@app.route("/upload_commands", methods=['POST'])
def upload_commands():
	if request.headers.get('API_KEY') == API_KEY:
		database.clear_commands()
		data = json.loads(request.get_json())
		for command in data:
			logging.info(F"/upload_commands: Adding user command '{command['name']}'")
			database.add_command(command['name'], bool(command['team']), command['text'])
		return "", 200
	else:
		logging.warning("/upload_stats: API_KEY not sent")
		return "", 403


"""
@app.route("/make_thumbnail", methods=['POST'])
def make_thumbnail():
	if request.headers.get('API_KEY') == API_KEY:
		url = request.json['url']
		# Check the cache - we might have already converted this.
		if database.has_thumbnail(url):
			#print(F"thumbnail image found in cache")
			return {'url': database.get_thumbnail(url)}, 200

		data = requests.get(url).content
		img = Image.open(io.BytesIO(data))
		img = img.resize((50, 50), Image.ANTIALIAS)
		buffer = io.BytesIO()
		img.save(buffer, format='PNG')
		thumb = upload_to_imgur(buffer.getvalue(),
								str(uuid.uuid4()) +
								'.png')  # TODO: does .png need to be added?
		#file_path = "badge_thumbnails/" + str(uuid.uuid4()) + ".png"
		#img.save(file_path, format='PNG')
		#thumb = "https://XDHS.repl.co/" + file_path
		if thumb is not None:
			database.insert_thumbnail(url, thumb)
		return {'url': thumb}, 200
	else:
		return "", 403
"""


@app.route("/cache_badge_card", methods=['POST'])
def cache_badge_card():
	if request.headers.get('API_KEY') == API_KEY:
		discord_id = request.json['discord_id']
		url = request.json['url']
		logging.info(F"/cache_badge_card: {discord_id} : {url}")
		database.upsert_badge_card(discord_id, url)
		return "", 200
	else:
		logging.warning("/upload_stats: API_KEY not sent")
		return "", 403


def run():
	app.run(host=config['FLASK']['BIND_ADDRESS'], port=config['FLASK']['BIND_PORT'])

def start_server():
	server = Thread(target=run)
	server.start()
