import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.interpolate import interp1d
import pandas as pd

# TODO: Get driver times by reading in csv (pandas?) and then take averages in intervals and show laps (i.e. for 74 actual laps, run 7.4 laps)
# TODO: Get driver names in 3 letters

# Hardcoded lap times
lap_times = {
    'Driver A': 90,
    'Driver B': 95,
    'Driver C': 100
}

# Normalize speeds
min_lap = min(lap_times.values())
speeds = {driver: min_lap / time for driver, time in lap_times.items()}

# Create a custom track (TODO: load actual track data here)
track_x = np.array([0, 2, 4, 6, 7, 6, 4, 2, 0, -2, -4, -5, -4, -2, 0])
track_y = np.array([0, 1, 2, 3, 5, 6, 7, 6, 5, 4, 3, 1, -1, -1, 0])
track_points = np.column_stack((track_x, track_y))

# Compute distance along track
deltas = np.diff(track_points, axis=0)
segment_lengths = np.hypot(deltas[:, 0], deltas[:, 1])
cumulative_lengths = np.insert(np.cumsum(segment_lengths), 0, 0)
total_length = cumulative_lengths[-1]
s_vals = cumulative_lengths / total_length  # normalized [0, 1]

# Interpolators for x(s) and y(s)
x_interp = interp1d(s_vals, track_x, kind='linear', fill_value='extrapolate')
y_interp = interp1d(s_vals, track_y, kind='linear', fill_value='extrapolate')

# Set up figure
fig, ax = plt.subplots()
ax.plot(track_x, track_y, 'gray', linewidth=2)
ax.set_aspect('equal')
ax.set_xlim(track_x.min() - 1, track_x.max() + 1)
ax.set_ylim(track_y.min() - 1, track_y.max() + 1)
ax.axis('off')

dots = {driver: ax.plot([], [], 'o', label=driver)[0] for driver in lap_times}
colors = ['red', 'blue', 'green']
for dot, color in zip(dots.values(), colors):
    dot.set_color(color)

def init():
    for dot in dots.values():
        dot.set_data([], [])
    return dots.values()

def animate(frame):
    time_elapsed = frame / 30  # seconds
    for driver, speed in speeds.items():
        s = (speed * time_elapsed) % 1.0  # position along track
        x = x_interp(s)
        y = y_interp(s)
        dots[driver].set_data([x], [y])
    return dots.values()

ani = FuncAnimation(fig, animate, frames=1000, init_func=init, blit=True, interval=33)
ax.legend(loc='upper right')
plt.show()
