import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
 
# Hardcoded lap times 
lap_times = {
    'Driver A': 90,
    'Driver B': 95,
    'Driver C': 100
}

# Normalize speeds so that the fastest driver has speed 1
min_lap_time = min(lap_times.values())
speeds = {driver: min_lap_time / time for driver, time in lap_times.items()}

# Set up the track (circle)
theta = np.linspace(0, 2 * np.pi, 1000)
track_radius = 5
x_track = track_radius * np.cos(theta)
y_track = track_radius * np.sin(theta)

# Set up figure
fig, ax = plt.subplots()
ax.plot(x_track, y_track, 'gray')  # the track
ax.set_aspect('equal')
ax.set_xlim(-6, 6)
ax.set_ylim(-6, 6)
ax.axis('off')

# Plot driver dots
dots = {driver: ax.plot([], [], 'o', label=driver)[0] for driver in lap_times}
colors = ['red', 'blue', 'green']
for dot, color in zip(dots.values(), colors):
    dot.set_color(color)

# Init function
def init():
    for dot in dots.values():
        dot.set_data([], [])
    return dots.values()

# Animation function
def animate(frame):
    time_elapsed = frame / 30  # Assuming 30 FPS
    for i, (driver, speed) in enumerate(speeds.items()):
        angle = (2 * np.pi * speed * time_elapsed) % (2 * np.pi)
        x = track_radius * np.cos(angle)
        y = track_radius * np.sin(angle)
        dots[driver].set_data([x], [y])
    return dots.values()

# Create animation
ani = FuncAnimation(fig, animate, frames=1000, init_func=init, blit=True, interval=33)

# Add legend
ax.legend(loc='upper right')

plt.show()
