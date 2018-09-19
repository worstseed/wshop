import ParticleFilter as pf
import mcpi.minecraft as minecraft
import geojson
import os
import numpy as np
import cherrypy
import Connection as con

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

number_of_expeditions = 1

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

# Create particles in possible positions in maze
n_particles = 1000
particles = pf.create_uniform_particles((maze_position[0] + 1, maze_position[0] + maze_length - 1),
                                     (maze_position[2] + 1, maze_position[2] + maze_width - 1), n_particles, coordinates)

# Create array of particles' weights
weights = np.zeros(particles.shape[0])
weights += 1


if __name__ == "__main__":
    data_storage = con.Data()
    for i in range(number_of_expeditions):
        cherrypy.config.update({'server.socket_host': "0.0.0.0",
                                'server.socket_port': 8181})

        cherry_connection = con.CherryPyConnection()
        cherrypy.quickstart(cherry_connection)

        print "Connection terminated. Expedition #" + str(i)
        # print cherry_connection.get_data()
        data_storage.add_data(cherry_connection.get_data())
        data_storage.show_data()
        moves = data_storage.take_moves()

for i in range(np.alen(moves)):
    # Move player with small error
    real_move = np.random.normal(loc=1.0, scale=0.05, size=None)
    dev = np.random.normal(loc=0.0, scale=0.05, size=None)

    player_position = mc.player.getPos()

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
    pf.predict(particles, moves[i], 0.05)

    # Calculate probability of every particle
    pf.update(particles, weights, 1, coordinates, mc.player.getPos())

    # Show mean and best value of particles
    mean, var = pf.estimate(particles, weights)

    max_weight_id = np.argmax(weights)
    prob_position = particles[max_weight_id, :].copy()

    # Fix the error if variance is low -> prob_position is ok
    if np.min(var) < 0.1:
        error = [prob_position[0] - np.floor(prob_position[0]) - 0.5, prob_position[1] - np.floor(prob_position[1]) - 0.5]

        if np.abs(error[0]) > 0.01:
            real_move = np.random.normal(loc=error[0], scale=np.abs(error[0]/20), size=None)
            player_position.x -= real_move
            pf.move_particles(particles, -np.random.randn(n_particles)*error[0], 0)

        if np.abs(error[1]) > 0.01:
            real_move = np.random.normal(loc=error[1], scale=np.abs(error[1]/20), size=None)
            player_position.z -= real_move
            pf.move_particles(particles, 0, -np.random.randn(n_particles)*error[1])

        pf.update(particles, weights, 1, coordinates, mc.player.getPos())

        max_weight_id = np.argmax(weights)
        prob_position = particles[max_weight_id, :].copy()

        mc.player.setPos(player_position)

    # Resample: create new particles based on old particles and give them the same weights
    pf.simple_resample(particles, weights)