########### LIBRARIES ############

import mcpi.minecraft as minecraft
import geojson
import os
import numpy
import time
import math
import numpy as np
from scipy.stats import norm
from numpy.random import uniform

##################################
########## CONSTANTS #############

cobblestone_block_id = 4
gold_block_id = 14
white_block_id = 155
black_block_id = 49
air_block_id = 0

default_name = "maciej"
default_address = "127.0.0.1"
default_height = 5

maze_length = 11
maze_width = 11

dirpath = os.getcwd()
maze_file = "maze-plan.geo.json"

player_radius = 0.30000001192092896

##################################

# Connect to minecraft server 127.0.0.1 as player 'maciej' (default)!
name = raw_input("Username (default: \"" + default_name + "\"): ")
address = raw_input("Minecraft server address (default: " + default_address + "): ")

# Set defaults.
if not name:
    name = default_name
if not address:
    address = default_address

# Connect!
mc = minecraft.Minecraft.create(address=address, name=name)

# Set world spawn in the minecraft world.
y = mc.getHeight(0, 0)
print('In your Server console, please run the following command:')
print('\tsetworldspawn 0 ' + str(y) + ' 0')

# Set position of maze
maze_position = [0, 30, 0]

# Get the plan of desired maze.
with open(dirpath + "/" + maze_file) as input_file:
    geojson_file = geojson.load(input_file)
coordinates = list(geojson_file['coordinates'])

# Clean the maze area
for x in range(0, maze_length):
    for z in range(0, maze_width):
        for y in range(-1, 5):
            mc.setBlock(maze_position[0] + x, maze_position[1] + y, maze_position[2] + z,
                    air_block_id)

# Create the maze area
for x in range(0, maze_length):
    for z in range(0, maze_width):
        mc.setBlock(maze_position[0] + x, maze_position[1] - 1, maze_position[2] + z,
                    white_block_id)
        if x == 0 or x == (maze_length - 1) or z == 0 or z == (maze_width - 1):
            mc.setBlock(maze_position[0] + x, maze_position[1], maze_position[2] + z,
                        black_block_id)

# Build the actual maze
for c in coordinates:
    mc.setBlock(maze_position[0] + c[0] + 1, maze_position[1], maze_position[2] + c[1] + 1,
                black_block_id)

# Move the player to the starting position in the maze.
mc.player.setPos(maze_position[0] + 2.5, maze_position[1], maze_position[2] + 5.5)

##################################################
################## FUNCTIONS #####################


def create_uniform_particles(x_range, z_range, N):
    particles = np.empty((N, 2))
    i = 0
    while i < N:
        particles[i, 0] = uniform(x_range[0], x_range[1], size=1)
        particles[i, 1] = uniform(z_range[0], z_range[1], size=1)
        if find_distances(particles[i, :]) == [0, 0, 0, 0]:
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
def find_distances(pos):
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

    if numpy.min(distances) < player_radius:
        return [0, 0, 0, 0]

    return distances


def update(particles, weights, std):
    n = len(particles)
    player_position = mc.player.getPos()
    player_distances = find_distances([player_position.x, player_position.z])

    # Add small error to player's measurements
    for i in range(0, 4):
        player_distances[i] = numpy.random.normal(loc=player_distances[i], scale=0.01, size=None)

    # Calculate weights based on player's distances and particle's distances
    for i in range(0, n):
        distances = find_distances(particles[i, :])
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
    indexes = np.searchsorted(cumulative_sum, numpy.random.rand(N))

    # resample according to indexes
    particles[:] = particles[indexes]
    weights.fill(1.0 / N)


##################################################

# Create particles in possible positions in maze
n_particles = 1000
particles = create_uniform_particles((maze_position[0] + 1, maze_position[0] + maze_length - 1),
                                     (maze_position[2] + 1, maze_position[2] + maze_width - 1), n_particles)

# Create array of particles' weights
weights = np.zeros(particles.shape[0])
weights += 1

# Array of player's moves
moves = ["west", "south", "west", "west", "north", "north", "west", "north", "north", "north", "east", "north", "north",
         "east", "north", "east", "east", "east", "south", "east", "east", "north", "east", "west", "south", "west",
         "west", "north", "west", "west", "west", "south", "west", "south", "south", "east", "east", "south", "south",
         "east", "east", "north", "north", "east", "east", "east"]

# Arrays for debugging
# real_moves = np.zeros(46)
# devs = np.zeros(46)
# positions = np.zeros([46, 2])
# positions_after = np.zeros([46, 2])

for i in range(0, 4):

    # Move player with small error
    real_move = numpy.random.normal(loc=1.0, scale=0.05, size=None)
    dev = numpy.random.normal(loc=0.0, scale=0.05, size=None)

    player_position = mc.player.getPos()

    # real_moves[i] = real_move
    # devs[i] = dev
    # positions[i] = [player_position.x, player_position.z]

    if moves[i] == "north":
        player_position.x += real_move
        player_position.z += dev
    elif moves[i] == "east":
        player_position.x += dev
        player_position.z += real_move
    elif moves[i] == "south":
        player_position.x -= real_move
        player_position.z += dev
    elif moves[i] == "west":
        player_position.x += dev
        player_position.z -= real_move

    mc.player.setPos(player_position)
    # positions_after[i] = [player_position.x, player_position.z]

    # Move all particles with small error
    predict(particles, moves[i], 0.05)

    # Calculate probability of every particle
    update(particles, weights, 1)

    # Show mean and best value of particles
    mean, var = estimate(particles, weights)

    max_weight_id = np.argmax(weights)
    prob_position = particles[max_weight_id, :].copy()

    # Fix the error if variance is low -> prob_position is ok
    if numpy.min(var) < 0.1:
        error = [prob_position[0] - np.floor(prob_position[0]) - 0.5, prob_position[1] - np.floor(prob_position[1]) - 0.5]

        if np.abs(error[0]) > 0.01:
            real_move = numpy.random.normal(loc=error[0], scale=np.abs(error[0]/20), size=None)
            player_position.x -= real_move
            move_particles(particles, -np.random.randn(n_particles)*error[0], 0)

        if np.abs(error[1]) > 0.01:
            real_move = numpy.random.normal(loc=error[1], scale=np.abs(error[1]/20), size=None)
            player_position.z -= real_move
            move_particles(particles, 0, -np.random.randn(n_particles)*error[1])

        update(particles, weights, 1)

        max_weight_id = np.argmax(weights)
        prob_position = particles[max_weight_id, :].copy()

        mc.player.setPos(player_position)

    # Resample: create new particles based on old particles and give them the same weights
    simple_resample(particles, weights)

while True:

    # pos = mc.player.getPos()
    # distances = find_distances([pos.x, pos.z])
    #
    # mc.postToChat(
    #     "Your position is: x:" + str(pos.x) + " y:" + str(pos.y) + "z: " + str(pos.z)
    #     + "n: " + str(distances[0]) + "e: " + str(distances[1]) + "s: " + str(distances[2])
    #     + "w: " + str(distances[3]))

    time.sleep(1)





