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
df = raw_df[['driver_code', 'lap_number', 'lap_time', 'position', 'team']].copy()

# Add cumulative times
df['cumulative_time'] = (
    df.sort_values(by=['driver_code', 'lap_number'])
      .groupby('driver_code')['lap_time']
      .cumsum()
)
print(df.head())

# Determine max laps; normalize cumulative race times; generate timestep 
max_laps = df['lap_number'].max()
max_cumulative_time = df['cumulative_time'].max()
timesteps = np.linspace(0, max_cumulative_time, 20000)  # Less timesteps result in faster animation

# Hardcoded track
# track_x = np.array([0, 2, 4, 6, 7, 6, 4, 2, 0, -2, -4, -5, -4, -2, 0])
# track_y = np.array([0, 1, 2, 3, 5, 6, 7, 6, 5, 4, 3, 1, -1, -1, 0])
# track_pts = np.column_stack((track_x, track_y))

# Import track
track_filepath = "tracks/Spielberg.csv"
track_df = pd.read_csv(track_filepath)
track_df['x'] = track_df['# x_m']
track_df['y'] = track_df['y_m']
track_df = track_df[['x', 'y']] # Drop other rows, such as track width
track_x = track_df['x'].to_numpy()
track_y = track_df['y'].to_numpy()
track_pts = np.column_stack((track_x, track_y))

# Calculate and normalize track segment lengths
dxy = np.diff(track_pts, axis=0) # diff between points along track: dxy of (3, 4) and (6,6) is (3,2)
segment_lengths = np.hypot(dxy[:, 0], dxy[:, 1])  # dist formula on dxy
cumulative_lengths = np.insert(np.cumsum(segment_lengths), 0, 0) # give each segment a cumulative length relative to start position
print("cumulative_lengths:", cumulative_lengths)
total_length = cumulative_lengths[-1]
rel_lengths = cumulative_lengths / total_length # Scale all cumulative distances relative to [0,1]. Start is 0, end is 1

# Create interpolators that send any input in [0, 1] to an interpolated x and y coordinate
x_interp = interp1d(rel_lengths, track_x, kind='linear', fill_value='extrapolate')
y_interp = interp1d(rel_lengths, track_y, kind='linear', fill_value='extrapolate')

# Set up plot
fig, ax = plt.subplots()
ax.plot(track_x, track_y, 'gray', linewidth=2)
ax.set_aspect('equal')
ax.axis('off')

# Make lap counter (empty for now)
lap_text = ax.text(0.02, 0.02, '', transform=ax.transAxes, fontsize=12, color='black', ha='left')

# Get all drivers, plot colored dots by team colors
drivers = df['driver_code'].unique() # list of all unique driver codes
teams = df[['driver_code', 'team']].set_index('driver_code')['team'].to_dict() # A dictionary of {driver_code, team}
dots = {} # dict of matplot dot objects {driver_code, <dot>}
for driver in drivers:
    team = teams[driver] 
    color = team_colors.get(team, 'gray')  # fallback to gray if not found
    dot, = ax.plot([], [], 'o', label=driver, color=color) # make dot with empty initial position
    dots[driver] = dot # add to dots dictionary

# Animation pause flag
is_paused = False

# Driver labels
labels = {driver: ax.text(0, 0, driver, fontsize=8, ha='center') for driver in drivers}

def init():
    """
    Set animation initial state
    """
    for dot in dots.values():
        dot.set_data([], [])
    for label in labels.values():
        label.set_position((-100, -100)) 
    lap_text.set_text('') 
    return list(dots.values()) + list(labels.values()) + [lap_text]

# Animation update
def animate(frame):
    if is_paused:
        return list(dots.values()) + list(labels.values()) + [lap_text]
   
    t = timesteps[frame]
    max_lap_displayed = 0

    for driver in drivers:
        driver_df = df[df['driver_code'] == driver].sort_values(by='lap_number')
        # print("driver_df")
        # print(driver_df.head())
        past_laps = driver_df[driver_df['cumulative_time'] <= t] # time less than current time
        # print(driver, "max cumulative_time", driver_df['cumulative_time'].max()) 
        # print(past_laps.head())
        total_laps = len(driver_df)
        completed = len(past_laps)

        if completed == 0: # Race start
            s = 0
        elif completed >= total_laps: # Race end
            s = 1.0
        else: 
            t1 = driver_df.iloc[completed - 1]['cumulative_time'] # cumulative time at start of current lap
            t2 = driver_df.iloc[completed]['cumulative_time'] # cumulative time at end of current lap
            frac = (t - t1) / (t2 - t1) # how far into the current lap we are  (e.g. 0.42 way through)
            lap_progress = completed + frac  # exact lap count (e.g., 17.42)
            s = lap_progress % 1.0           # current position within the lap

        x = x_interp(s % 1.0)
        y = y_interp(s % 1.0)
        # Update positions
        dots[driver].set_data([x], [y]) 
        labels[driver].set_position((x, y + 0.2)) 

        # If driver has completed more laps than the lap number currently displayed, update display. 
        # So lap counter is updated when the *first* driver starts the next lap
        if completed > max_lap_displayed:
            max_lap_displayed = completed

    lap_text.set_text(f"Lap: {max_lap_displayed}/{int(max_laps)}")

    # Stop race if every driver is done
    all_finished = True
    for driver in drivers:
        driver_df = df[df['driver_code'] == driver].sort_values(by='lap_number')
        completed = len(driver_df[driver_df['cumulative_time'] <= t])
        if completed < len(driver_df):
            all_finished = False
            break
    if all_finished:
        anim.event_source.stop()

    return list(dots.values()) + list(labels.values()) + [lap_text]

anim = FuncAnimation(fig, animate, frames=len(timesteps), init_func=init, blit=True, interval=20)
plt.legend(fontsize=8, loc='upper right')

def on_key(event):
    global is_paused
    if event.key == ' ':  # spacebar toggles pause
        is_paused = not is_paused
fig.canvas.mpl_connect('key_press_event', on_key)

plt.show()