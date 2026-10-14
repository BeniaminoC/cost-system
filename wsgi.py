"""Punto de entrada para Vercel (Flask). Toda la logica vive en backend/server.py (dispatch)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from flask import Flask, request, Response
import server

app = Flask(__name__, static_folder=None)


@app.route("/", defaults={"p": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:p>", methods=["GET", "POST", "PUT", "DELETE"])
def todo(p):
    code, ctype, body, headers = server.dispatch(request.method, "/" + p, request.args.to_dict(),
                                                 request.headers.get("Authorization", ""), request.get_data())
    r = Response(body, status=code, content_type=ctype)
    for k, v in headers.items():
        r.headers[k] = v
    return r
