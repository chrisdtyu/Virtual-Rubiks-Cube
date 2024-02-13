# cube.py
#
# Author: Christopher Yu
# Email: chrisdtyu@gmail.com
#
# Code to create the cube.

from vpython import *
import numpy as np
from random import choice
from solve import *


class Rubiks_Cube():
    def __init__(self):
        self.running = True
        self.tiles = []
        self.dA = np.pi/40 # delta angle
        self.method_called = False

        # draw the centre of the cube
        sphere(pos=vector(0, 0, 0), size=vector(3, 3, 3), color=vector(0, 0, 0))
        
        # define positions of individual tiles on each face of the cube
        tile_pos = [
            [vector(-1, 1, 1.5), vector(0, 1, 1.5), vector(1, 1, 1.5),            # front
            vector(-1, 0, 1.5), vector(0, 0, 1.5), vector(1, 0, 1.5), 
            vector(-1, -1, 1.5), vector(0, -1, 1.5), vector(1, -1, 1.5), ], 
            [vector(1.5, 1, -1), vector(1.5, 1, 0), vector(1.5, 1, 1),            # right
            vector(1.5, 0, -1), vector(1.5, 0, 0), vector(1.5, 0, 1), 
            vector(1.5, -1, -1), vector(1.5, -1, 0), vector(1.5, -1, 1), ], 
            [vector(-1, 1, -1.5), vector(0, 1, -1.5), vector(1, 1, -1.5),         # back
            vector(-1, 0, -1.5), vector(0, 0, -1.5), vector(1, 0, -1.5), 
            vector(-1, -1, -1.5), vector(0, -1, -1.5), vector(1, -1, -1.5), ], 
            [vector(-1.5, 1, -1), vector(-1.5, 1, 0), vector(-1.5, 1, 1),         # left
            vector(-1.5, 0, -1), vector(-1.5, 0, 0), vector(-1.5, 0, 1), 
            vector(-1.5, -1, -1), vector(-1.5, -1, 0), vector(-1.5, -1, 1), ], 
            [vector(-1, 1.5, -1), vector(0, 1.5, -1), vector(1, 1.5, -1),         # top
            vector(-1, 1.5, 0), vector(0, 1.5, 0), vector(1, 1.5, 0), 
            vector(-1, 1.5, 1), vector(0, 1.5, 1), vector(1, 1.5, 1), ], 
            [vector(-1, -1.5, -1), vector(0, -1.5, -1), vector(1, -1.5, -1),      # bottom
            vector(-1, -1.5, 0), vector(0, -1.5, 0), vector(1, -1.5, 0), 
            vector(-1, -1.5, 1), vector(0, -1.5, 1), vector(1, -1.5, 1), ], 
        ]

        # colors: blue, red, green, orange, yellow, white
        colors = [vector(0, 0, 1), vector(1, 0, 0), vector(0, 1, 0), vector(1, 0.647, 0), vector(1, 1, 0), vector(1, 1, 1)]
        
        # define initial orientations for each face of the cube
        angle = [(0, vector(0, 0, 0)), (np.pi/2, vector(0, 1, 0)), (0, vector(0, 0, 0)), (np.pi/2, vector(0, 1, 0)), \
                 (np.pi/2, vector(1, 0, 0)), (np.pi/2, vector(1, 0, 0))]
        
        # draw individual tiles on cube
        for rank, side in enumerate(tile_pos):
            for vec in side:
                tile = box(pos = vec, size = vector(0.98, 0.98, 0.1), color = colors[rank])
                tile.rotate(angle = angle[rank][0], axis = angle[rank][1])
                self.tiles.append(tile)
       
        # define initial positions of tiles on each face
        self.positions = {'front':[], 'right':[], 'back':[], 'left':[], 'top':[], 'bottom':[]}
        
        # initialize variables for rotation
        self.rotate = [None, 0, 0]
        self.moves = []


    def reset_positions(self):
        self.positions = {'front': [], 'right': [], 'back': [], 'left': [], 'top': [], 'bottom': []}
        for tile in self.tiles:
            if tile.pos.z > 0.4:
                self.positions['front'].append(tile)
            if tile.pos.x > 0.4:
                self.positions['right'].append(tile)
            if tile.pos.z < -0.4:
                self.positions['back'].append(tile)
            if tile.pos.x < -0.4:
                self.positions['left'].append(tile)
            if tile.pos.y > 0.4:
                self.positions['top'].append(tile)
            if tile.pos.y < -0.4:
                self.positions['bottom'].append(tile)
        for key in self.positions.keys():
            self.positions[key] = set(self.positions[key])


    def animations(self):
        # Perform animations for cube turns
        if self.rotate[0] == 'front_ccw':
            pieces = self.positions['front']
            for tile in pieces:
                tile.rotate(angle=self.dA, axis=vector(0, 0, 1), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'right_ccw':
            pieces = self.positions['right']
            for tile in pieces:
                tile.rotate(angle=(self.dA), axis=vector(1, 0, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'back_ccw':
            pieces = self.positions['back']
            for tile in pieces:
                tile.rotate(angle=(self.dA), axis=vector(0, 0, -1), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'left_ccw':
            pieces = self.positions['left']
            for tile in pieces:
                tile.rotate(angle=(self.dA), axis=vector(-1, 0, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'top_ccw':
            pieces = self.positions['top']
            for tile in pieces:
                tile.rotate(angle=(self.dA), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'bottom_ccw':
            pieces = self.positions['bottom']
            for tile in pieces:
                tile.rotate(angle=(self.dA), axis=vector(0, -1, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'front_cw':
            pieces = self.positions['front']
            for tile in pieces:
                tile.rotate(angle=(-self.dA), axis=vector(0, 0, 1), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'right_cw':
            pieces = self.positions['right']
            for tile in pieces:
                tile.rotate(angle=(-self.dA), axis=vector(1, 0, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'back_cw':
            pieces = self.positions['back']
            for tile in pieces:
                tile.rotate(angle=(-self.dA), axis=vector(0, 0, -1), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'left_cw':
            pieces = self.positions['left']
            for tile in pieces:
                tile.rotate(angle=(-self.dA), axis=vector(-1, 0, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'top_cw':
            pieces = self.positions['top']
            for tile in pieces:
                tile.rotate(angle=(-self.dA), axis=vector(0, 1, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA
        elif self.rotate[0] == 'bottom_cw':
            pieces = self.positions['bottom']
            for tile in pieces:
                tile.rotate(angle=(-self.dA), axis=vector(0, -1, 0), origin=vector(0, 0, 0))
            self.rotate[1] += self.dA

        if self.rotate[1] + self.dA/2 > self.rotate[2] and \
                self.rotate[1] - self.dA/2 < self.rotate[2]:
            self.rotate = [None, 0, 0]
            self.reset_positions()



    # rotate inidividual faces clockwise (cw) or counterclockwise (ccw)
    def rotate_front_ccw(self):
        if self.rotate[0] == None:
            self.rotate = ['front_ccw', 0, np.pi/2]

    def rotate_right_ccw(self):
        if self.rotate[0] == None:
            self.rotate = ['right_ccw', 0, np.pi/2]

    def rotate_back_ccw(self):
        if self.rotate[0] == None:
            self.rotate = ['back_ccw', 0, np.pi/2]

    def rotate_left_ccw(self):
        if self.rotate[0] == None:
            self.rotate = ['left_ccw', 0, np.pi/2]

    def rotate_top_ccw(self):
        if self.rotate[0] == None:
            self.rotate = ['top_ccw', 0, np.pi/2]

    def rotate_bottom_ccw(self):
        if self.rotate[0] == None:
            self.rotate = ['bottom_ccw', 0, np.pi/2]

    def rotate_front_cw(self):
        if self.rotate[0] == None:
            self.rotate = ['front_cw', 0, np.pi/2]

    def rotate_right_cw(self):
        if self.rotate[0] == None:
            self.rotate = ['right_cw', 0, np.pi/2]

    def rotate_back_cw(self):
        if self.rotate[0] == None:
            self.rotate = ['back_cw', 0, np.pi/2]

    def rotate_left_cw(self):
        if self.rotate[0] == None:
            self.rotate = ['left_cw', 0, np.pi/2]

    def rotate_top_cw(self):
        if self.rotate[0] == None:
            self.rotate = ['top_cw', 0, np.pi/2]

    def rotate_bottom_cw(self):
        if self.rotate[0] == None:
            self.rotate = ['bottom_cw', 0, np.pi/2]


    def move(self):
        # perform moves based on the stored sequence
        possible_moves = ["F", "R", "B", "L", "U", "D", "F'", "R'", "B'", "L'", "U'", "D'"]
        if self.rotate[0] == None and len(self.moves) > 0:
            if self.moves[0] == possible_moves[0]:
                self.rotate_front_cw()
            elif self.moves[0] == possible_moves[1]:
                self.rotate_right_cw()
            elif self.moves[0] == possible_moves[2]:
                self.rotate_back_cw()
            elif self.moves[0] == possible_moves[3]:
                self.rotate_left_cw()
            elif self.moves[0] == possible_moves[4]:
                self.rotate_top_cw()
            elif self.moves[0] == possible_moves[5]:
                self.rotate_bottom_cw()
            elif self.moves[0] == possible_moves[6]:
                self.rotate_front_ccw()
            elif self.moves[0] == possible_moves[7]:
                self.rotate_right_ccw()
            elif self.moves[0] == possible_moves[8]:
                self.rotate_back_ccw()
            elif self.moves[0] == possible_moves[9]:
                self.rotate_left_ccw()
            elif self.moves[0] == possible_moves[10]:
                self.rotate_top_ccw()
            elif self.moves[0] == possible_moves[11]:
                self.rotate_bottom_ccw()
            self.moves.pop(0)


    def scramble(self):
        # generate a random scramble sequence to scramble the cube
        possible_moves = ["F", "R", "B", "L", "U", "D", "F'", "R'", "B'", "L'", "U'", "D'"]
        for i in range(30):
            self.moves.append(choice(possible_moves))
    

    def solution(self):
        # display the solution to the cube 
        solve(self.tiles)
        if self.method_called:
            old_caption = scene.caption
            scene.caption = ""
            self.control()
            scene.append_to_caption(old_caption)
        self.method_called = True


    def solve(self):
        # solve the cube and store the solution moves
        values = solve(self.tiles)
        values = list(values.split(" "))
        for value in values:
            lis_value = list(value)
            if lis_value[-1] == '2':
                lis_value.pop(-1)
                value = ''.join(lis_value)
                self.moves.append(value)
                self.moves.append(value)
            else:
                self.moves.append(value)
        if self.method_called:
            old_caption = scene.caption
            scene.caption = ""
            self.control()
            scene.append_to_caption(old_caption)
        self.method_called = True
    

    def control(self):
        # define GUI controls for cube manipulation
        button(bind=self.rotate_front_cw, text='F')
        button(bind=self.rotate_front_ccw, text="F'")
        button(bind=self.rotate_right_cw, text='R')
        button(bind=self.rotate_right_ccw, text="R'")
        button(bind=self.rotate_back_cw, text='B')
        button(bind=self.rotate_back_ccw, text="B'")
        button(bind=self.rotate_left_cw, text='L')
        button(bind=self.rotate_left_ccw, text="L'")
        button(bind=self.rotate_top_cw, text='U')
        button(bind=self.rotate_top_ccw, text="U'")
        button(bind=self.rotate_bottom_cw, text='D')
        button(bind=self.rotate_bottom_ccw, text="D'")
        button(bind=self.scramble, text='scramble')
        button(bind=self.solution, text='reveal solution')
        button(bind=self.solve, text='solve cube')
        

    def update(self):
        # Update the cube's state in each frame
        rate(60)
        self.animations()
        self.move()



    def start(self):
        # Initialize and run the virtual Rubik's Cube 
        self.reset_positions()
        self.control()
        while self.running:
            self.update()
