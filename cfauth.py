"""
This module provides a way to get data from Chronis.
Used for scripts that require authentication.
Not to be used with web applications, as this runs its own flask server.
"""
import threading
import webbrowser
import time
import logging
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
ntoken = None # pylint: disable=invalid-name

def get_available_scopes() -> dict:
    """
    Gets the available scopes from the Chronis API.
    Returns a dictionary with keys being the scope names and values being the scope descriptions.
    """
    req = requests.get("https://class.trey7658.com/api/v2/scopes", timeout=5)
    if req.status_code == 200:
        return req.json()['scopes']
    logging.error("Failed to fetch scopes: %s - %s", req.status_code, req.text)
    return {}

def get_token(scopes: list = [], openbrowser: bool=True, port: int = 5000) -> str: #pylint: disable=dangerous-default-value
    """
    Gets the token from Chronis.
    """
    global ntoken # pylint: disable=global-statement
    ntoken = None
    if openbrowser:
        webbrowser.open(f"https://class.trey7658.com/auth?redirect_url=http://localhost:{str(port)}/callback&scopes=" + ",".join(scopes))
    else:
        logging.info(
            "Please open the following URL in your browser: https://class.trey7658.com/auth?redirect_url=http://localhost:%s/callback&scopes=%s",
            str(port),
            ",".join(scopes)
        )
    logging.info("Waiting for token...")
    server_thread = threading.Thread(target=run_server, args=(port,))
    server_thread.daemon = True
    server_thread.start()
    while ntoken is None:
        time.sleep(0.1)
    return ntoken

def run_server(port: int = 5000):
    """
    Runs the Flask server to get the token.
    """
    logging.info("Starting callback server on port %s", port)
    app.run(port=port, debug=False, use_reloader=False)

@app.route('/callback', methods=['GET'])
def callback():
    """
    This route is called when the user is redirected back to the application after logging in.
    """
    global ntoken # pylint: disable=global-statement
    code = request.args.get('token')
    if code:
        ntoken = code
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No token received"}), 400
