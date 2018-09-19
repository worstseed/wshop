import pandas as pd
import cherrypy
import numpy as np


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
        self.DF_list.append(df.values)

    def take_moves(self):
        moves = []
        len = int(np.shape(self.DF_list[0])[0])
        dir = 1
        for s in range(len):
            move = self.DF_list[0][s]

            dir -= int(move[0])
            dir += int(move[1])

            if int(move[2]) == 1:
                if dir % 4 == 0:
                    moves.append("north")
                elif dir % 4 == 1:
                    moves.append("east")
                elif dir % 4 == 2:
                    moves.append("south")
                elif dir % 4 == 3:
                    moves.append("west")

        return moves

    def show_data(self):
        for i in self.DF_list:
            print i