"""
Simple CSRF-aware proxy server (Flask, single file)

Env vars (required):
  UPSTREAM_BASE_URL   e.g. https://internal.example.com
  AUTH_USERNAME       upstream username
  AUTH_PASSWORD       upstream password
  CSRF_INIT_PATH      path to get/login for CSRF (e.g. /csrf or /auth/login)
  FORWARD_PATH        path to forward data to (e.g. /api/submit)

Optional:
  CSRF_INIT_METHOD    GET or POST (default: GET)
  CSRF_HEADER_NAME    header to send token in (e.g. X-CSRF-Token)
  CSRF_JSON_FIELD     JSON field name containing token (e.g. csrfToken)
  TIMEOUT_SECONDS     default: 10
"""

import os
import json
from typing import Any, Dict, Optional

import requests
from flask import Flask, request, jsonify, Response, abort

from sosachb import TwoChannelClient as sosachb


# ------------ Config ------------

BASE_URL = os.getenv("UPSTREAM_BASE_URL", "http://flarum:8888/").rstrip("/")
#BASE_URL = os.getenv("UPSTREAM_BASE_URL", "http://127.0.0.1/").rstrip("/")
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "rRGXx5t1yZNX1JQ")
#CSRF_INIT_PATH = os.getenv("CSRF_INIT_PATH", "http://flarum:8888/")
#CSRF_INIT_PATH = os.getenv("CSRF_INIT_PATH", "http://127.0.0.1:80/")
FORWARD_PATH_POST = os.getenv("FORWARD_PATH_POST", "http://flarum:8888/api/posts")
FORWARD_PATH_DISS = os.getenv("FORWARD_PATH_POST_DISS", "http://flarum:8888/api/discussions")
#FORWARD_PATH = os.getenv("FORWARD_PATH", "http://127.0.0.1:80/api/posts")
CSRF_INIT_METHOD = os.getenv("CSRF_INIT_METHOD", "GET").upper()
CSRF_HEADER_NAME = os.getenv("CSRF_HEADER_NAME")  # optional
CSRF_JSON_FIELD = os.getenv("CSRF_JSON_FIELD")    # optional
TIMEOUT_SECONDS = float(os.getenv("TIMEOUT_SECONDS", "10"))

if not (BASE_URL  and FORWARD_PATH_POST and FORWARD_PATH_DISS and AUTH_USERNAME and AUTH_PASSWORD):
  raise SystemExit(
    "Missing env vars. Set: UPSTREAM_BASE_URL, AUTH_USERNAME, AUTH_PASSWORD, CSRF_INIT_PATH, FORWARD_PATH"
  )


# ------------ App ------------

app = Flask(__name__)

@app.get("/healthz")
def healthz():
  return jsonify(ok=True)

# ---- Helpers ----

def read_payload() -> Dict[str, Any]:
  ctype = request.headers.get("content-type", "")
  # JSON (or empty -> try JSON)
  if "application/json" in ctype or not ctype:
    try:
      data = request.get_json(force=False, silent=True) or {}
      if isinstance(data, dict):
        return data
    except Exception:
      pass
  # Forms
  if "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
    return {k: v for k, v in request.form.items()}
  abort(Response(json.dumps({"error": "unsupported_media_type"}), status=415, mimetype="application/json"))


# ---- Route ----

@app.post("/api/posts")
def posts():
  # 1) incoming data
  payload = read_payload()
  client = sosachb()

  # 2) same session for cookies + forwarding
  import random
  import string
  anon_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
  client = sosachb()
  client.login(username="admin",password="rRGXx5t1yZNX1JQ")
  client.get_token(username="admin",password="rRGXx5t1yZNX1JQ")
  if  client.check_user_exists(anon_name) == 404:
    print("CREATING  USER:",anon_name, )#"PARENT:",(post.num))
    client.add_user(username=anon_name,password="correcthorsebatterystaple",email=anon_name+"@gmail.com")

  user_data=client.login(username=anon_name,password="correcthorsebatterystaple")
  #print(user_data)

  with requests.Session() as sess:
    # sess.headers.update({"User-Agent": "csrf-proxy/1.0"})
    # try:
    #   token = fetch_csrf_token(sess)
    # except requests.RequestException:
    #   return jsonify(error="bootstrap_failed"), 502
    #
    # if CSRF_HEADER_NAME and not token:
    #   return jsonify(error="missing_csrf_token"), 502

    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
      'X-CSRF-Token': client.extract_auth_info()[1],
    }

    # 3) forward
    #print(FORWARD_PATH)
    try:
      upstream = sess.post(FORWARD_PATH_POST, json=payload, headers=headers, cookies=user_data, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
      return jsonify(error="upstream_unreachable"), 502

  # 4) pass-through upstream response
  return Response(
    response=upstream.content,
    status=upstream.status_code,
    mimetype=upstream.headers.get("content-type", "application/json"),
  )

@app.post("/api/discussions")
def discussions():
  # 1) incoming data
  payload = read_payload()
  client = sosachb()

  # 2) same session for cookies + forwarding
  import random
  import string
  anon_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
  client = sosachb()
  #TODO use XCSRF token from client to login
  client.login(username="admin",password="rRGXx5t1yZNX1JQ")
  client.get_token(username="admin",password="rRGXx5t1yZNX1JQ")
  if  client.check_user_exists(anon_name) == 404:
    print("CREATING  USER:",anon_name, )#"PARENT:",(post.num))
    client.add_user(username=anon_name,password="correcthorsebatterystaple",email=anon_name+"@gmail.com")

  user_data=client.login(username=anon_name,password="correcthorsebatterystaple")
  #print(user_data)

  with requests.Session() as sess:
    # sess.headers.update({"User-Agent": "csrf-proxy/1.0"})
    # try:
    #   token = fetch_csrf_token(sess)
    # except requests.RequestException:
    #   return jsonify(error="bootstrap_failed"), 502
    #
    # if CSRF_HEADER_NAME and not token:
    #   return jsonify(error="missing_csrf_token"), 502

    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
      'X-CSRF-Token': client.extract_auth_info()[1],
    }

    # 3) forward
    #print(FORWARD_PATH)
    try:
      upstream = sess.post(FORWARD_PATH_DISS, json=payload, headers=headers, cookies=user_data, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
      return jsonify(error="upstream_unreachable"), 502

  # 4) pass-through upstream response
  return Response(
    response=upstream.content,
    status=upstream.status_code,
    mimetype=upstream.headers.get("content-type", "application/json"),
  )

# Allow `python app.py`
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080)
