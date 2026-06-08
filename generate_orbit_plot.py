import numpy as np
import astropy.units as u
from sunpy.coordinates import get_horizons_coord
from sunpy.time import parse_time
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta

# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_DAYS_BACK  = 10
DEFAULT_DAYS_AHEAD = 10
DEFAULT_STEP       = "6h"   # must be a valid Horizons step string

TARGETS = {
    'Mercury':           {'id': '199',  'color': '#aaaaaa', 'size': 4,  'symbol': 'circle'},
    'Venus':             {'id': '299',  'color': '#e8a045', 'size': 9,  'symbol': 'circle'},
    'Earth':             {'id': '399',  'color': '#4fa3e0', 'size': 10, 'symbol': 'circle'},
    'Mars':              {'id': '499',  'color': '#c1440e', 'size': 5,  'symbol': 'circle'},
    'Parker Solar Probe':{'id': '-96',  'color': '#bf7fff', 'size': 4,  'symbol': 'diamond'},
    'Solar Orbiter':     {'id': '-144', 'color': '#4ecdc4', 'size': 4,  'symbol': 'diamond'},
    'STEREO-A':          {'id': '-234', 'color': '#ff6b6b', 'size': 4,  'symbol': 'diamond'},
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def fetch_body(body_id, times, now):
    """Return (ox, oy, oz, cx, cy, cz) all in solar radii."""
    orbit   = get_horizons_coord(body_id, times)
    current = get_horizons_coord(body_id, now)

    ohgs = orbit.heliographic_stonyhurst.cartesian
    chgs = current.heliographic_stonyhurst.cartesian

    ox = ohgs.x.to(u.R_sun).value.tolist()
    oy = ohgs.y.to(u.R_sun).value.tolist()
    oz = ohgs.z.to(u.R_sun).value.tolist()

    cx = float(chgs.x.to(u.R_sun).value)
    cy = float(chgs.y.to(u.R_sun).value)
    cz = float(chgs.z.to(u.R_sun).value)
    return ox, oy, oz, cx, cy, cz


def build_figure(days_back, days_ahead, step, now_str=None):
    """Fetch data and build a Plotly figure for the given window."""
    now   = parse_time(now_str) if now_str else parse_time('now')
    times = {
        'start': now - days_back  * u.day,
        'stop':  now + days_ahead * u.day,
        'step':  step,
    }

    fig = go.Figure()

    for name, info in TARGETS.items():
        print(f"  Fetching {name}…")
        try:
            ox, oy, oz, cx, cy, cz = fetch_body(info['id'], times, now)
        except Exception as exc:
            print(f"    ⚠  Skipped {name}: {exc}")
            continue

        # Orbit trail
        fig.add_trace(go.Scatter3d(
            x=ox, y=oy, z=oz,
            mode='lines',
            line=dict(color=info['color'], width=2),
            hoverinfo='skip',
            showlegend=False,
        ))

        # Current position
        fig.add_trace(go.Scatter3d(
            x=[cx], y=[cy], z=[cz],
            mode='markers+text',
            name=name,
            text=[name],
            textposition='top center',
            textfont=dict(size=10, color='white'),
            marker=dict(size=info['size'], color=info['color'], symbol=info['symbol']),
        ))

    # Sun
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        name='Sun',
        text=['Sun'],
        textposition='bottom center',
        marker=dict(size=15, color='gold', symbol='circle',
                    line=dict(color='black', width=2)),
    ))

    fig.update_layout(
        template='plotly_dark',
        showlegend=False,
        title=dict(
            text=f"Spacecraft & Planet Positions (HEEQ) — {now.strftime('%Y-%m-%d')}  "
                 f"[±{days_back}/{days_ahead} d, step {step}]",
            font=dict(size=14),
        ),
        scene=dict(
            xaxis_title='X (R☉)',
            yaxis_title='Y (R☉)',
            zaxis_title='Z (R☉)',
            aspectmode='data',
        ),
        margin=dict(l=0, r=0, b=0, t=50),
    )
    return fig


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(
    days_back=DEFAULT_DAYS_BACK,
    days_ahead=DEFAULT_DAYS_AHEAD,
    step=DEFAULT_STEP,
    output="space_map.html",
):
    print(f"Building plot: -{days_back}d … +{days_ahead}d, step={step}")
    fig = build_figure(days_back, days_ahead, step)

    # ── Inject an interactive control panel into the HTML ──────────────────
    plot_html = fig.to_html(include_plotlyjs='cdn', full_html=False)

    controls_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>Solar System Orbit Viewer</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #0a0a14;
    color: #e0e0f0;
    font-family: 'Courier New', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}

  /* ── Control bar ── */
  #controls {{
    background: linear-gradient(90deg, #0d0d22 0%, #12122a 100%);
    border-bottom: 1px solid #2a2a4a;
    padding: 12px 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    align-items: flex-end;
  }}

  #controls h2 {{
    width: 100%;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #6060aa;
    margin-bottom: -6px;
  }}

  .field {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}

  .field label {{
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #8080c0;
  }}

  .field input, .field select {{
    background: #16162e;
    border: 1px solid #30306a;
    color: #c8c8f0;
    padding: 5px 10px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 0.85rem;
    width: 110px;
    transition: border-color 0.2s;
  }}
  .field input:focus, .field select:focus {{
    outline: none;
    border-color: #5050cc;
  }}

  #replot-btn {{
    background: linear-gradient(135deg, #3030aa, #5050dd);
    color: #fff;
    border: none;
    padding: 7px 22px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    cursor: pointer;
    align-self: flex-end;
    transition: filter 0.2s, transform 0.1s;
  }}
  #replot-btn:hover  {{ filter: brightness(1.2); }}
  #replot-btn:active {{ transform: scale(0.97); }}
  #replot-btn:disabled {{ filter: brightness(0.5); cursor: not-allowed; }}

  #status {{
    align-self: flex-end;
    font-size: 0.72rem;
    color: #5a5a90;
    min-width: 180px;
  }}
  #status.busy  {{ color: #aaaa44; }}
  #status.error {{ color: #cc4444; }}
  #status.done  {{ color: #44cc88; }}

  /* ── Plot container ── */
  #plot-container {{
    flex: 1;
    min-height: 0;
  }}
  #plot-container > div {{
    height: calc(100vh - 90px) !important;
  }}
</style>
</head>
<body>

<div id="controls">
  <h2>⬡ Orbit viewer — adjust timeframe &amp; regenerate</h2>

  <div class="field">
    <label>Center date</label>
    <input type="date" id="center-date" value="{datetime.utcnow().strftime('%Y-%m-%d')}"/>
  </div>

  <div class="field">
    <label>Days before</label>
    <input type="number" id="days-back" value="{days_back}" min="1" max="365"/>
  </div>

  <div class="field">
    <label>Days ahead</label>
    <input type="number" id="days-ahead" value="{days_ahead}" min="1" max="365"/>
  </div>

  <div class="field">
    <label>Time step</label>
    <select id="step">
      <option value="1h">1 h</option>
      <option value="3h">3 h</option>
      <option value="6h" selected>6 h</option>
      <option value="12h">12 h</option>
      <option value="1d">1 day</option>
      <option value="7d">1 week</option>
    </select>
  </div>

  <button id="replot-btn" onclick="replot()">▶ Regenerate</button>
  <div id="status">Loaded — adjust controls &amp; click Regenerate</div>
</div>

<div id="plot-container">
  {plot_html}
</div>

<script>
// ── The "Regenerate" button can't re-run Python in the browser.
// ── It updates the plot using pre-embedded data for the initial window,
// ── and for other windows it delegates to a lightweight Python-served
// ── endpoint (if available) or informs the user to re-run the script.

function replot() {{
  const daysBack  = parseInt(document.getElementById('days-back').value)  || {days_back};
  const daysAhead = parseInt(document.getElementById('days-ahead').value) || {days_ahead};
  const step      = document.getElementById('step').value;
  const date      = document.getElementById('center-date').value;

  setStatus('busy', '⟳ Requesting new data…');
  document.getElementById('replot-btn').disabled = true;

  // Try the local Flask endpoint (started by run_server.py)
  fetch(`/orbit_data?days_back=${{daysBack}}&days_ahead=${{daysAhead}}&step=${{step}}&center=${{date}}`)
    .then(r => {{
      if (!r.ok) throw new Error('server_unavailable');
      return r.json();
    }})
    .then(data => {{
      updatePlot(data, date, daysBack, daysAhead, step);
      setStatus('done', '✓ Updated');
    }})
    .catch(() => {{
      // Server not running — tell the user how to regenerate
      setStatus('error',
        `⚠ No server found. Run: python generate_orbit_plot.py --back ${{daysBack}} --ahead ${{daysAhead}} --step ${{step}} --center ${{date}}`
      );
    }})
    .finally(() => {{
      document.getElementById('replot-btn').disabled = false;
    }});
}}

function setStatus(cls, msg) {{
  const el = document.getElementById('status');
  el.className = cls;
  el.textContent = msg;
}}

function updatePlot(data, center, back, ahead, step) {{
  const container = document.querySelector('#plot-container > div');
  const gd = container;

  // Rebuild traces from server-supplied JSON
  const traces = [];

  data.forEach(body => {{
    // Orbit line
    traces.push({{
      type: 'scatter3d',
      mode: 'lines',
      x: body.ox, y: body.oy, z: body.oz,
      line: {{ color: body.color, width: 2 }},
      hoverinfo: 'skip',
      showlegend: false,
    }});
    // Current position
    traces.push({{
      type: 'scatter3d',
      mode: 'markers+text',
      x: [body.cx], y: [body.cy], z: [body.cz],
      text: [body.name],
      textposition: 'top center',
      textfont: {{ size: 10, color: 'white' }},
      marker: {{ size: body.size, color: body.color, symbol: body.symbol }},
      showlegend: false,
    }});
  }});

  // Sun
  traces.push({{
    type: 'scatter3d', mode: 'markers+text',
    x: [0], y: [0], z: [0],
    text: ['Sun'], textposition: 'bottom center',
    marker: {{ size: 15, color: 'gold', symbol: 'circle', line: {{ color: 'black', width: 2 }} }},
    showlegend: false,
  }});

  Plotly.react(gd, traces, {{
    template: 'plotly_dark',
    showlegend: false,
    title: {{
      text: `Spacecraft & Planet Positions (HEEQ) — ${{center}}  [±${{back}}/${{ahead}} d, step ${{step}}]`,
      font: {{ size: 14 }},
    }},
    scene: {{
      xaxis_title: 'X (R☉)',
      yaxis_title: 'Y (R☉)',
      zaxis_title: 'Z (R☉)',
      aspectmode: 'data',
    }},
    margin: {{ l:0, r:0, b:0, t:50 }},
  }});
}}
</script>
</body>
</html>
"""

    with open(output, 'w', encoding='utf-8') as f:
        f.write(controls_html)

    print(f"✓  Saved → {output}")
    print()
    print("  To enable live regeneration in the browser, also run:")
    print("    python run_server.py")


# ─── CLI entry-point ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate an interactive 3-D solar-system orbit map.')
    parser.add_argument('--back',   type=float, default=DEFAULT_DAYS_BACK,
                        help='days before now to plot (default: %(default)s)')
    parser.add_argument('--ahead',  type=float, default=DEFAULT_DAYS_AHEAD,
                        help='days after  now to plot (default: %(default)s)')
    parser.add_argument('--step',   type=str,   default=DEFAULT_STEP,
                        help='Horizons time step, e.g. 6h 1d (default: %(default)s)')
    parser.add_argument('--center', type=str,   default=None,
                        help='ISO date for center of window, e.g. 2025-01-15 (default: now)')
    parser.add_argument('--output', type=str,   default='space_map.html',
                        help='output HTML filename (default: %(default)s)')
    args = parser.parse_args()

    main(
        days_back  = args.back,
        days_ahead = args.ahead,
        step       = args.step,
        output     = args.output,
    )
