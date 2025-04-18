import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.interpolate import interp1d
import pandas as pd

# TODO: Get driver times by reading in csv (pandas?) and then take averages in intervals and show laps (i.e. for 74 actual laps, run 7.4 laps)
# TODO: Get driver names in 3 letters

is_paused = {'state': False}

# Read in CSV to raw_df
filepath = "data/final_f1_dataset.csv"
raw_df = pd.read_csv(filepath)
raw_df['driver_code'] = raw_df['driver'].apply(lambda name: name.split()[-1][:3].upper())

# Create df (cleaned)
df = raw_df[['driver_code', 'lap_number', 'lap_time', 'position', 'team']]
df['cumulative_time'] = (
    df.sort_values(by=['driver_code', 'lap_number'])
      .groupby('driver_code')['lap_time']
      .cumsum()
)

num_laps = df['lap_number'].max()

# Normalize cumulative race times
max_cumulative_time = df['cumulative_time'].max()
# Generate 2000 timesteps 
timesteps = np.linespace(0, max_cumulative_time, 2000)

# lap_times = averaged_df.set_index('driver_code')['avg_lap_time'].to_dict()

# Normalize speeds
# min_lap = min(lap_times.values())
# speeds = {driver: min_lap / time for driver, time in lap_times.items()}

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

# Get all drivers, make dots and labels
drivers = df['driver_code'].unique()
dots = {driver: ax.plot([], [], 'o', label=driver)[0] for driver in drivers}
labels = {driver: ax.text(0, 0, driver, fontsize=9, ha='center') for driver in drivers}
colors = plt.cm.get_cmap('tab20', len(drivers))
for i, driver in enumerate(drivers):
    dots[driver].set_color(colors(i))

def init():
    for dot in dots.values():
        dot.set_data([], [])
    for label in labels.values():
        label.set_position((-100, -100))  # move offscreen initially
    return list(dots.values()) + list(labels.values())

def on_key(event):
    if event.key == ' ':
        is_paused['state'] = not is_paused['state']

def animate(frame):
    if is_paused['state']:
        return list(dots.values()) + list(labels.values())

    t = timesteps[frame]

    for driver in drivers:
        driver_df = df[df['driver_code'] == driver].sort_values(by='lap_number') # all laptimes for a driver
        past_laps_df = driver_df[driver_df['cumulative_time'] <= t]
        total_laps = len(driver_df)
        past_laps = len(past_laps_df)

        if past_laps == 0:
            s = 0
        elif past_laps >= total_laps:
            s = 1.0
        else:
            t1 = driver_df.iloc[past_laps - 1]['cumulative_time'] 
            t2 = driver_df.iloc[past_laps]['cumulative_time']
            dt = (t - t1) / (t2 - t1)
            s = (past_laps + dt) / total_laps
            lap_progress = past_laps + dt  # exact lap count (e.g., 17.42)
            s = lap_progress % 1.0           # current position within the lap
            lap_number = int(lap_progress)   # how many full laps completed

    time_elapsed = frame / 30  # seconds
    for driver, speed in speeds.items():
        s = (1/speed * time_elapsed * 0.2) % 1.0  # position along track TODO need to fix
        x = x_interp(s)
        y = y_interp(s)
        dots[driver].set_data([x], [y])
        labels[driver].set_position((x, y + 0.3))
    return list(dots.values()) + list(labels.values())
    # TODO : keep track of lap number and display it


fig.canvas.mpl_connect('key_press_event', on_key)
anim = FuncAnimation(fig, animate, frames=1000, init_func=init, blit=True, interval=33)
ax.legend(loc='upper right')
plt.show()
