import time
import math
import numpy as np
from scipy.stats import norm
from numpy.random import uniform
maze_width = 11
maze_length = 11
player_radius = 0.30000001192092896


def create_uniform_particles(x_range, z_range, N, coordinates):
    particles = np.empty((N, 2))
    i = 0
    while i < N:
        particles[i, 0] = uniform(x_range[0], x_range[1], size=1)
        particles[i, 1] = uniform(z_range[0], z_range[1], size=1)
        if find_distances(particles[i, :], coordinates) == [0, 0, 0, 0]:
            i -= 1
        i += 1
    return particles


def predict(particles, direction, std):
    N = len(particles)
    if direction == "north":
        move_particles(particles, 1 + np.random.randn(N) * std, np.random.randn(N) * std)
    elif direction == "east":
        move_particles(particles, np.random.randn(N) * std, 1 + np.random.randn(N) * std)
    elif direction == "south":
        move_particles(particles, -1 - np.random.randn(N) * std, np.random.randn(N) * std)
    elif direction == "west":
        move_particles(particles, np.random.randn(N) * std, -1 - np.random.randn(N) * std)


def move_particles(particles, x, z):
    particles[:, 0] += x
    particles[:, 1] += z


# Calculate particle's distances to walls in four directions based on given map. If particle is in impossible position
# then array of zeros is returned.
def find_distances(pos, coordinates):
    tilePos = [math.floor(pos[0]), math.floor(pos[1])]
    distances = [0, 0, 0, 0]

    if tilePos[0] <= 0 or tilePos[0] >= (maze_length - 1) or tilePos[1] <= 0 or tilePos[1] >= (maze_width - 1):
        return distances

    if [tilePos[0] - 1, tilePos[1] - 1] in coordinates:
        return distances

    distances = [maze_length - 1 - pos[0], maze_width - 1 - pos[1], pos[0] - 1, pos[1] - 1]

    for i in range(1, 9):
        if [tilePos[0] + i - 1, tilePos[1] - 1] in coordinates:
            distances[0] = tilePos[0] - pos[0] + i
            break

    for i in range(1, 9):
        if [tilePos[0] - 1, tilePos[1] + i - 1] in coordinates:
            distances[1] = tilePos[1] - pos[1] + i
            break

    for i in range(1, 9):
        if [tilePos[0] - i - 1, tilePos[1] - 1] in coordinates:
            distances[2] = pos[0] - tilePos[0] + i - 1
            break

    for i in range(1, 9):
        if [tilePos[0] - 1, tilePos[1] - i - 1] in coordinates:
            distances[3] = pos[1] - tilePos[1] + i - 1
            break

    if np.min(distances) < player_radius:
        return [0, 0, 0, 0]

    return distances


def update(particles, weights, std, coordinates, player_position):
    n = len(particles)
    player_distances = find_distances([player_position.x, player_position.z], coordinates)

    # Add small error to player's measurements
    for i in range(0, 4):
        player_distances[i] = np.random.normal(loc=player_distances[i], scale=0.01, size=None)

    # Calculate weights based on player's distances and particle's distances
    for i in range(0, n):
        distances = find_distances(particles[i, :], coordinates)
        if distances == [0, 0, 0, 0]:
            weights[i] = 0
        else:
            for d in range(0, 4):
                weights[i] *= norm(0, std).pdf(player_distances[d] - distances[d])

    #weights += 1.e-300      # avoid round-off to zero
    weights /= sum(weights) # normalize


def estimate(particles, weights):
    pos = particles[:, 0:2]
    mean = np.average(pos, weights=weights, axis=0)
    var = np.average((pos - mean) ** 2, weights=weights, axis=0)
    return mean, var


def simple_resample(particles, weights):
    N = len(particles)
    cumulative_sum = np.cumsum(weights)
    cumulative_sum[-1] = 1.  # avoid round-off error
    indexes = np.searchsorted(cumulative_sum, np.random.rand(N))

    # resample according to indexes
    particles[:] = particles[indexes]
    weights.fill(1.0 / N)