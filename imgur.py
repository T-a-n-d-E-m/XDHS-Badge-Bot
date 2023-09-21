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

# Upload an image to the Imgur hosting service and return the url of the uploaded image.

import os
import requests
import base64
import time
from config import config

IMGUR_CLIENT_SECRET = config['IMGUR']['CLIENT_SECRET']
IMGUR_API_URL = 'https://api.imgur.com/3/image'

def upload_to_imgur(img, filename):
  header = {
    'Authorization': 'Client-ID ' + IMGUR_CLIENT_SECRET,
  }

  payload = {
    "image": base64.b64encode(img),
    "type" : "base64",
    "name" : filename
  }

  attempts = 0;
  while attempts < 10:
    result = requests.post(IMGUR_API_URL, headers=header, data=payload)
    if result.status_code == 200:
      return result.json()['data']['link']
    else:
      logging.error(F"upload_to_imgur: error {result.status_code} : {result.json()['data']['error']}")
      attempts = attempts + 1;
      time.sleep(attempts/10)
  
  logging.error(F"upload_to_imgur: error uploading to Imgur")
  # TODO: Now what? This isn't that uncommon, so it needs to be handled gracefully...
  return None
