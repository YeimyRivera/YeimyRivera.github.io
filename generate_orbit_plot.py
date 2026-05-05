#used this one
import numpy as np
import astropy.units as u
from sunpy.coordinates import get_horizons_coord
from sunpy.time import parse_time
import plotly.graph_objects as go

# 1. Setup Time
now = parse_time('now')
times = {'start': now - 10*u.day, 'stop': now + 10*u.day, 'step': '6h'}

# 2. Objects and Configuration
targets = {
    'Mercury': {'id': '199', 'color': 'gray', 'size': 4, 'symbol': 'circle'},
    'Venus': {'id': '299', 'color': 'orange', 'size': 9, 'symbol': 'circle'},
    'Earth': {'id': '399', 'color': 'blue', 'size': 10, 'symbol': 'circle'},
    'Mars': {'id': '499', 'color': 'red', 'size': 5, 'symbol': 'circle'},
    'Parker Solar Probe': {'id': '-96', 'color': 'purple', 'size': 4, 'symbol': 'diamond'},
    'Solar Orbiter': {'id': '-144', 'color': 'green', 'size': 4, 'symbol': 'diamond'},
    'STEREO-A': {'id': '-234', 'color': 'red', 'size': 4, 'symbol': 'diamond'}
}

fig = go.Figure()

# 3. Fetch and Plot
for name, info in targets.items():
    print(f"Fetching data for {name}...")
    orbit_coords = get_horizons_coord(info['id'], times)
    current_coord = get_horizons_coord(info['id'], now)

    # Scale to Solar Radii (R_sun)
    orbit_hgs = orbit_coords.heliographic_stonyhurst.cartesian
    ox, oy, oz = orbit_hgs.x.to(u.R_sun).value, orbit_hgs.y.to(u.R_sun).value, orbit_hgs.z.to(u.R_sun).value
    
    current_hgs = current_coord.heliographic_stonyhurst.cartesian
    cx, cy, cz = current_hgs.x.to(u.R_sun).value, current_hgs.y.to(u.R_sun).value, current_hgs.z.to(u.R_sun).value

    # Orbit Lines (Legend turned off)
    fig.add_trace(go.Scatter3d(x=ox, y=oy, z=oz, mode='lines', 
                             line=dict(color=info['color'], width=2), hoverinfo='skip'))

    # Current Position Markers with Text Labels
    fig.add_trace(go.Scatter3d(
        x=[cx], y=[cy], z=[cz],
        mode='markers+text',
        text=[name],
        textposition="top center",
        textfont=dict(size=10, color='white'),
        marker=dict(size=info['size'], color=info['color'], symbol=info['symbol'])
    ))

# 4. Sun at Center
fig.add_trace(go.Scatter3d(
    x=[0], y=[0], z=[0],
    mode='markers+text',
    text=['Sun'],
    textposition="bottom center",
    marker=dict(
        size=15, 
        symbol='circle', 
        color='gold', 
        line=dict(color='black', width=2)
    )
))

# 5. Layout with no legend
fig.update_layout(
    template="plotly_dark",
    showlegend=False,  # <--- This line removes the legend
    title=f"Spacecraft and Planet Positions (HEEQ) - {now.strftime('%Y-%m-%d')}",
    scene=dict(
        xaxis_title='X (solar radii)', yaxis_title='Y (solar radii)', zaxis_title='Z (solar radii)',
        aspectmode='data'
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)

fig.write_html("space_map.html")
# print("Map updated and legend removed.")
