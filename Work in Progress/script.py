########### LIBRARIES ############
import mcpi.minecraft as minecraft
import geojson
import os
import cherrypy
from cherrypy import request
import pandas as pd
import numpy as np
import time
import sys

##################################
########## CONSTANTS #############
cobblestone_block_id = 4

default_name = "maciej"
default_address = "127.0.0.1"
default_height = 15

maze_height = 11
maze_width = 11

dirpath = os.getcwd()
maze_file = "maze-plan.geo.json"

number_of_expeditions = 2
number_of_steps = 5
##################################
########### CLASSES ##############


class CherryPyConnection:
    def __init__(self):
        self.df = pd.DataFrame({"# Right Turns": [], "# Left Turns": [], "Move": []})

    @cherrypy.expose
    def index(self, **params):
        # all the request parameters goes into the params dictionary.
        # in case that no port is defined return None
        post = params.get('port', None)
        if post[0] == "(":
            # print "POST: "
            # print post
            df2 = pd.DataFrame({"# Right Turns": [post[1]],
                                "# Left Turns": [post[4]],
                                "Move": [post[7]]})
            self.df = pd.concat([self.df, df2])
            # print self.df

        elif post == "Home":
            self.shutdown()

        return "Done"

    @staticmethod
    def shutdown():
        cherrypy.engine.stop()
        cherrypy.engine.exit()

    def get_data(self):
        return self.df


class Data:
    def __init__(self):
        self.DF_list = list()

    def add_data(self, df):
        self.DF_list.append(df)

    def show_data(self):
        for i in self.DF_list:
            print i


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
# y = mc.getHeight(0, 0)
# print('In your Server console, please run the following command:')
# print('\tsetworldspawn 0 ' + str(y) + ' 0')

# Get player's position.
player_position = mc.player.getTilePos()

# Get the plan of desired maze.
with open(dirpath + "/" + maze_file) as input_file:
    geojson_file = geojson.load(input_file)
coordinates = geojson_file['coordinates']

# Set how high the maze should be created in regard to player's position.
height = raw_input("Set height above the ground (default: " + str(default_height) + "): ")
if not height:
    height = default_height

# mc.setBlock(features[0], features[1], features[2], cobblestone_block_id)

# Create stairs to the maze area.
for i in range(0, height + 1):
    mc.setBlock(player_position.x + 1 + i, player_position.y + i, player_position.z, cobblestone_block_id)

# Create the maze area.
for x in range(0, maze_height):
    for z in range((maze_width - 1) / (-2), (maze_width + 1) / 2):
        mc.setBlock(player_position.x + height + 2 + x, player_position.y + height, player_position.z + z,
                    cobblestone_block_id)
        if x == 0 or x == (maze_height - 1) or z == (maze_width - 1) / (-2) or z == (maze_width - 1) / 2:
            mc.setBlock(player_position.x + height + 2 + x, player_position.y + height + 1, player_position.z + z,
                        cobblestone_block_id)

# Build the actual maze.
for c in coordinates:
    mc.setBlock(player_position.x + height + 3 + c[0], player_position.y + height + 1, player_position.z + c[1] - 4,
                cobblestone_block_id)

# Move the player to starting position in the maze.
mc.player.setPos(player_position.x + height + 4, player_position.y + height + 1, player_position.z + 0.5)

player_position = mc.player.getTilePos()
print(player_position)

if __name__ == "__main__":
    data_storage = Data()
    for i in range(number_of_expeditions):
        cherrypy.config.update({'server.socket_host': "0.0.0.0",
                                'server.socket_port': 8181})

        cherry_connection = CherryPyConnection()
        cherrypy.quickstart(cherry_connection)

        print "Connection terminated. Expedition #" + str(i)
        # print cherry_connection.get_data()
        data_storage.add_data(cherry_connection.get_data())
        data_storage.show_data()
