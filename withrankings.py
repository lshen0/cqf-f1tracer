import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.interpolate import interp1d

# Team colors
team_colors = {
    'Mercedes': '#00D2BE',
    'Red Bull Racing': '#1E41FF',
    'Ferrari': '#DC0000',
    'McLaren': '#FF8700',
    'Racing Point': '#F363B9',
    'Renault': '#FCD205',
    'Williams': '#005AFF',
    'AlphaTauri': '#2B4562',
    'Alfa Romeo': '#900000',
    'Haas': '#9E9E9E'
}

# Read CSV into raw_df
data_filepath = "data/final_f1_dataset.csv"
raw_df = pd.read_csv(data_filepath)
raw_df['driver_code'] = raw_df['driver'].apply(lambda name: name.split()[-1][:3].upper())

# Create df (cleaned)
df = raw_df[['driver_code', 'lap_number', 'lap_time', 'position', 'team']]

# Add cumulative times
df['cumulative_time'] = (
    df.sort_values(by=['driver_code', 'lap_number'])
      .groupby('driver_code')['lap_time']
      .cumsum()
)

# Determine max laps; normalize cumulative race times; generate timestep 
max_laps = df['lap_number'].max()
max_cumulative_time = df['cumulative_time'].max()
timesteps = np.linspace(0, max_cumulative_time, 20000)  # Less timesteps result in faster animation

# Hardcoded track
# track_x = np.array([0, 2, 4, 6, 7, 6, 4, 2, 0, -2, -4, -5, -4, -2, 0])
# track_y = np.array([0, 1, 2, 3, 5, 6, 7, 6, 5, 4, 3, 1, -1, -1, 0])
# track_pts = np.column_stack((track_x, track_y))

# Imported track
track_filepath = "tracks/Spielberg.csv"
track_df = pd.read_csv(track_filepath)
track_df['x'] = track_df['# x_m']
track_df['y'] = track_df['y_m']
track_df = track_df[['x', 'y']] # Drop other rows, such as track width

track_x = track_df['x'].to_numpy()
track_y = track_df['y'].to_numpy()
track_pts = np.column_stack((track_x, track_y))

# Calculate and normalize track segment lengths
deltas = np.diff(track_pts, axis=0)
segment_lengths = np.hypot(deltas[:, 0], deltas[:, 1])  
cumulative_lengths = np.insert(np.cumsum(segment_lengths), 0, 0) # Give each segment a cumulative length relative to start position
total_length = cumulative_lengths[-1]
s_vals = cumulative_lengths / total_length # Scale all cumulative distances to [0,1]

# Create interpolators that send [0, 1] to an interpolated x and y coordinate
x_interp = interp1d(s_vals, track_x, kind='linear', fill_value='extrapolate')
y_interp = interp1d(s_vals, track_y, kind='linear', fill_value='extrapolate')

# Set up plot
fig, ax = plt.subplots()
ax.plot(track_x, track_y, 'gray', linewidth=2)
ax.set_aspect('equal')
ax.axis('off')

# Make lap counter
lap_text = ax.text(0.02, 0.02, '', transform=ax.transAxes, fontsize=12, color='black', ha='left')
# Live leaderboard
leaderboard_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, fontsize=8, color='black', ha='left', va='top')

# Get all drivers, plot colored dots by team colors
drivers = df['driver_code'].unique()
teams = df[['driver_code', 'team']].set_index('driver_code')['team'].to_dict() # A dictionary of {driver_code, team}
dots = {}
for driver in drivers:
    team = teams[driver]
    color = team_colors.get(team, 'gray')  # fallback to gray if not found
    dot, = ax.plot([], [], 'o', label=driver, color=color)
    dots[driver] = dot

# Animation pause flag
is_paused = False

# Driver labels
labels = {driver: ax.text(0, 0, driver, fontsize=8, ha='center') for driver in drivers}

def init():
    for dot in dots.values():
        dot.set_data([], [])
    for label in labels.values():
        label.set_position((-100, -100))
    lap_text.set_text('')
    leaderboard_text.set_text('')
    return list(dots.values()) + list(labels.values()) + [lap_text, leaderboard_text]

# Animation update
def animate(frame):
    if is_paused:
        return list(dots.values()) + list(labels.values()) + [lap_text]
   
    t = timesteps[frame]
    max_lap_displayed = 0

    for driver in drivers:
        driver_df = df[df['driver_code'] == driver].sort_values(by='lap_number')
        past_laps = driver_df[driver_df['cumulative_time'] <= t]
        total_laps = len(driver_df)
        completed = len(past_laps)

        if completed == 0:
            s = 0
        elif completed >= total_laps:
            s = 1.0
        else:
            t1 = driver_df.iloc[completed - 1]['cumulative_time']
            t2 = driver_df.iloc[completed]['cumulative_time']
            frac = (t - t1) / (t2 - t1)
            lap_progress = completed + frac  # exact lap count (e.g., 17.42)
            s = lap_progress % 1.0           # current position within the lap

        x = x_interp(s % 1.0)
        y = y_interp(s % 1.0)
        dots[driver].set_data([x], [y])
        labels[driver].set_position((x, y + 0.2))

        if completed > max_lap_displayed:
            max_lap_displayed = completed

    lap_text.set_text(f"Lap: {max_lap_displayed}/{max_laps}")

   # Compute live leaderboard
    current_times = {}
    for driver in drivers:
        driver_df = df[df['driver_code'] == driver].sort_values(by='lap_number')
        past_laps = driver_df[driver_df['cumulative_time'] <= t]
        if len(past_laps) > 0:
            current_times[driver] = past_laps.iloc[-1]['cumulative_time']
        else:
            current_times[driver] = np.inf  # Driver hasn't started, put at bottom

    # Sort drivers by cumulative time
    sorted_drivers = sorted(current_times.items(), key=lambda x: x[1])
    leaderboard_str = '\n'.join([f"{i+1}. {drv}" for i, (drv, _) in enumerate(sorted_drivers)])
    leaderboard_text.set_text(leaderboard_str)

    all_finished = True
    for driver in drivers:
        driver_laps = df[df['driver_code'] == driver]
        completed = len(driver_laps[driver_laps['cumulative_time'] <= t])
        if completed < len(driver_laps):
            all_finished = False
            break

    if all_finished:
        anim.event_source.stop()


    return list(dots.values()) + list(labels.values()) + [lap_text, leaderboard_text]


anim = FuncAnimation(fig, animate, frames=len(timesteps), init_func=init, blit=True, interval=20)
plt.legend(fontsize=8, loc='upper right')

def on_key(event):
    global is_paused
    if event.key == ' ':  # spacebar toggles pause
        is_paused = not is_paused
fig.canvas.mpl_connect('key_press_event', on_key)

plt.show()