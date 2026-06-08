"""
run_server.py
─────────────
Lightweight Flask server that lets the orbit-viewer HTML page
regenerate the plot without re-running the full script.

Usage:
    pip install flask
    python run_server.py          # serves on http://localhost:5000
    python run_server.py --port 8080

Then open  space_map.html  in a browser; the "Regenerate" button
will contact this server for updated orbit data.
"""

import argparse
import json
import astropy.units as u
from sunpy.coordinates import get_horizons_coord
from sunpy.time import parse_time
from flask import Flask, request, jsonify, send_from_directory

# ── Targets (keep in sync with generate_orbit_plot.py) ────────────────────────
TARGETS = {
    'Mercury':            {'id': '199',  'color': '#aaaaaa', 'size': 4,  'symbol': 'circle'},
    'Venus':              {'id': '299',  'color': '#e8a045', 'size': 9,  'symbol': 'circle'},
    'Earth':              {'id': '399',  'color': '#4fa3e0', 'size': 10, 'symbol': 'circle'},
    'Mars':               {'id': '499',  'color': '#c1440e', 'size': 5,  'symbol': 'circle'},
    'Parker Solar Probe': {'id': '-96',  'color': '#bf7fff', 'size': 4,  'symbol': 'diamond'},
    'Solar Orbiter':      {'id': '-144', 'color': '#4ecdc4', 'size': 4,  'symbol': 'diamond'},
    'STEREO-A':           {'id': '-234', 'color': '#ff6b6b', 'size': 4,  'symbol': 'diamond'},
}

app = Flask(__name__, static_folder='.')


@app.route('/')
def index():
    return send_from_directory('.', 'space_map.html')


@app.route('/orbit_data')
def orbit_data():
    """
    Query params:
        days_back  (float, default 10)
        days_ahead (float, default 10)
        step       (str,   default '6h')
        center     (ISO date string, default 'now')
    Returns JSON list of body dicts.
    """
    days_back  = float(request.args.get('days_back',  10))
    days_ahead = float(request.args.get('days_ahead', 10))
    step       = request.args.get('step',   '6h')
    center_str = request.args.get('center', None)

    try:
        now = parse_time(center_str) if center_str else parse_time('now')
    except Exception:
        now = parse_time('now')

    times = {
        'start': now - days_back  * u.day,
        'stop':  now + days_ahead * u.day,
        'step':  step,
    }

    results = []
    for name, info in TARGETS.items():
        print(f"  Fetching {name}…")
        try:
            orbit   = get_horizons_coord(info['id'], times)
            current = get_horizons_coord(info['id'], now)

            ohgs = orbit.heliographic_stonyhurst.cartesian
            chgs = current.heliographic_stonyhurst.cartesian

            results.append({
                'name':   name,
                'color':  info['color'],
                'size':   info['size'],
                'symbol': info['symbol'],
                'ox': ohgs.x.to(u.R_sun).value.tolist(),
                'oy': ohgs.y.to(u.R_sun).value.tolist(),
                'oz': ohgs.z.to(u.R_sun).value.tolist(),
                'cx': float(chgs.x.to(u.R_sun).value),
                'cy': float(chgs.y.to(u.R_sun).value),
                'cz': float(chgs.z.to(u.R_sun).value),
            })
        except Exception as exc:
            print(f"    ⚠  Skipped {name}: {exc}")

    return jsonify(results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Orbit viewer live-data server')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', type=str, default='127.0.0.1')
    args = parser.parse_args()

    print(f"Starting orbit server on http://{args.host}:{args.port}")
    print("Open space_map.html in a browser to use the control panel.")
    app.run(host=args.host, port=args.port, debug=False)
