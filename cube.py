# cube.py
#
# Author: Christopher Yu
# Email: chrisdtyu@gmail.com
#
# Code to create the cube.

import traceback
from dataclasses import dataclass
from queue import SimpleQueue
from random import choice

import numpy as np
from vpython import *

from solve import (FACE_COLORS, FACE_ORDER, FACELET_POSITIONS, parse_solution, rotations_to_default,
                   solve)

STEPS_PER_TURN = 20 # animation frames in a quarter turn
TURN_ANGLE = np.pi / 2 / STEPS_PER_TURN     
SLAB_THRESHOLD = 0.4 # how far from a layer's centre a tile can be and still turn with it
DRAG_THRESHOLD = 0.3 # how far to drag (in tile widths) before a turn starts
CANVAS_WIDTH = 900                          
POLE_COSINE = 0.5                          

AMBIENT_LIGHT = 0.5
LIGHTS = [((0, 0, 1), 0.5), ((0, 0, -1), 0.5), ((1, 0, 0), 0.45), ((-1, 0, 0), 0.45),
          ((0, 1, 0), 0.4), ((0, -1, 0), 0.4)]

CANVAS_SCALE = 0.75

PAGE_SETUP = (
    "<style>#glowscript{text-align:center}</style>"
    "<script>(function(){"
    "function fit(){try{"
    "var c=window.__context.canvas_selected||(window.__context.canvas_all||[])[0];"
    "if(!c)return false;"
    "var h=Math.max(300,Math.round((window.innerHeight-150)*" + str(CANVAS_SCALE) + "));"
    "var w=Math.max(640,Math.min(window.innerWidth-24,Math.round(h*1.7)));"
    "c.width=w;c.height=h;return true}catch(e){return false}}"
    "var tries=0;"
    "(function start(){if(!fit()&&tries++<50)setTimeout(start,100)})();"
    "window.addEventListener('resize',fit)"
    "})();</script>"
)

FACE_AXES = {
    'F': vector(0, 0, 1),
    'R': vector(1, 0, 0),
    'B': vector(0, 0, -1),
    'L': vector(-1, 0, 0),
    'U': vector(0, 1, 0),
    'D': vector(0, -1, 0),
}
OPPOSITE = {'F': 'B', 'B': 'F', 'R': 'L', 'L': 'R', 'U': 'D', 'D': 'U'}

POSSIBLE_MOVES = [face + turn for turn in ("", "'") for face in "FRBLUD"]

HIDE_SOLUTION = "hide solution"

CUBE_ROTATIONS = {'x': FACE_AXES['R'], 'y': FACE_AXES['U'], 'z': FACE_AXES['F']}
ROTATION_MOVES = [axis + turn for axis in "xyz" for turn in ("", "'")]
FACE_OF_ROTATION = {'x': 'R', 'y': 'U', 'z': 'F'}
ROTATION_OF_FACE = {'R': 'x', 'L': 'x', 'U': 'y', 'D': 'y', 'F': 'z', 'B': 'z'}

# tiles on the sides of the cube start flat so these are turned to face outwards
TILE_TWIST = {
    'R': (np.pi / 2, vector(0, 1, 0)),
    'L': (np.pi / 2, vector(0, 1, 0)),
    'U': (np.pi / 2, vector(1, 0, 0)),
    'D': (np.pi / 2, vector(1, 0, 0)),
}


def face_normal(pos):
    components = [pos.x, pos.y, pos.z]
    axis = max(range(3), key=lambda i: abs(components[i]))
    normal = [0, 0, 0]
    normal[axis] = 1 if components[axis] > 0 else -1
    return vector(*normal)


def mouse_on_plane(normal, point):
    ray = scene.mouse.ray
    camera = scene.camera.pos
    facing = normal.dot(ray)
    if facing == 0:
        return None
    distance = (normal.dot(point) - normal.dot(camera)) / facing
    return camera + ray * distance


def facing(direction, faces="FRBLUD"):
    # the face of the cube whose outward axis points closest to this direction
    return max(faces, key=lambda face: FACE_AXES[face].dot(direction))


def view_faces(forward, up):
    # which face of the cube the viewer sees as F (toward them), U (toward the top of the screen), etc
    front = facing(forward * -1)
    sideways = [face for face in "FRBLUD" if abs(FACE_AXES[face].dot(FACE_AXES[front])) < 0.5]
    top = facing(up, sideways)
    right = facing(FACE_AXES[top].cross(FACE_AXES[front]))
    return {'F': front, 'B': OPPOSITE[front], 'U': top, 'D': OPPOSITE[top],
            'R': right, 'L': OPPOSITE[right]}


def whole_cube_rotation(face, prime):
    flipped = prime != (face in "LDB")
    return ROTATION_OF_FACE[face] + ("'" if flipped else "")


def to_world(move, faces):
    #  translate a move from the viewer's POV into the cube's POV
    letter, prime = move[0], move.endswith("'")
    if letter in FACE_OF_ROTATION:
        return whole_cube_rotation(faces[FACE_OF_ROTATION[letter]], prime)
    return faces[letter] + ("'" if prime else "")


def to_view(move, faces):
    # the reverse of to_world, translate a move from the cube's POV into the viewer's POV
    letter, prime = move[0], move.endswith("'")
    viewer_letter = {face: view for view, face in faces.items()}
    if letter in FACE_OF_ROTATION:
        return whole_cube_rotation(viewer_letter[FACE_OF_ROTATION[letter]], prime)
    return viewer_letter[letter] + ("'" if prime else "")


def solution_in_view(solution, faces):
    # rewrite a solution from the viewer's POV
    words = []
    for word in solution.split():
        single = word[0] + ("'" if word.endswith("'") else "")
        words.append(to_view(single, faces) + ("2" if word.endswith("2") else ""))
    return " ".join(words)


@dataclass
class Turn:
    pieces: list # the tiles that are turning
    axis: vector
    angle: float # angle to rotate each frame
    frames_left: int


@dataclass
class Grab:
    # a tile the mouse has pressed on and is waiting to be dragged
    tile: object
    normal: vector    
    start: vector # where the mouse pressed


class Rubiks_Cube():
    def __init__(self):
        self.running = True
        self.tiles = []
        self.moves = []     
        self.turn = None # the Turn currently being animated
        self.grab = None # the Grab currently being dragged
        self.version = 0 # goes up each time a turn finishes so that changes to the cube can be noticed

        self.requests = SimpleQueue()

        self.solution_shown = False
        self.solution_stamp = None      
        self.message_text = ""
        self.message_shown = ""       

        scene.width = CANVAS_WIDTH
        self.set_lights()

        # draw the centre of the cube
        sphere(pos=vector(0, 0, 0), size=vector(3, 3, 3), color=vector(0, 0, 0))

        # draw individual tiles on cube
        for index, pos in enumerate(FACELET_POSITIONS):
            face = FACE_ORDER[index // 9]
            tile = box(pos=vector(*pos), size=vector(0.98, 0.98, 0.1),
                       color=vector(*FACE_COLORS[face]))
            if face in TILE_TWIST:
                angle, axis = TILE_TWIST[face]
                tile.rotate(angle=angle, axis=axis)
            self.tiles.append(tile)


    def set_lights(self):
        scene.lights = []
        scene.ambient = color.gray(AMBIENT_LIGHT)
        for direction, brightness in LIGHTS:
            distant_light(direction=vector(*direction), color=color.gray(brightness))


    def busy(self):
        # whether the cube is turning or has moves waiting to be played
        return self.turn is not None or len(self.moves) > 0


    def start_layer_turn(self, axis, layer, direction):
        if self.turn is not None:
            return
        if layer is None:
            pieces = list(self.tiles)
        elif layer == 0:
            pieces = [tile for tile in self.tiles if abs(tile.pos.dot(axis)) < SLAB_THRESHOLD]
        else:
            pieces = [tile for tile in self.tiles if tile.pos.dot(axis) * layer > SLAB_THRESHOLD]
        self.turn = Turn(pieces, axis, direction * TURN_ANGLE, STEPS_PER_TURN)


    def start_turn(self, move):
        direction = 1 if move.endswith("'") else -1
        if move[0] in CUBE_ROTATIONS:
            self.start_layer_turn(CUBE_ROTATIONS[move[0]], None, direction)
        else:
            self.start_layer_turn(FACE_AXES[move[0]], 1, direction)


    def view_faces(self):
        return view_faces(scene.forward, scene.up)


    def press(self, move):
        self.start_turn(to_world(move, self.view_faces()))


    def animations(self):
        if self.turn is None:
            return
        for tile in self.turn.pieces:
            tile.rotate(angle=self.turn.angle, axis=self.turn.axis, origin=vector(0, 0, 0))
        self.turn.frames_left -= 1
        if self.turn.frames_left == 0:
            self.turn = None
            self.version += 1


    def move(self):
        if self.turn is None and len(self.moves) > 0:
            move = self.moves.pop(0)
            if move == HIDE_SOLUTION:
                self.set_solution_shown(False)
            else:
                self.start_turn(move)


    def mouse_down(self, evt):
        # start a drag on the tile under the mouse
        self.grab = None
        if self.busy():
            return
        picked = scene.mouse.pick
        tile = next((t for t in self.tiles if t is picked), None)
        if tile is None:
            return
        normal = face_normal(tile.pos)
        start = mouse_on_plane(normal, tile.pos)
        if start is not None:
            self.grab = Grab(tile, normal, start)


    def mouse_move(self, evt):
        if self.grab is None:
            return
        if self.busy():
            self.grab = None
            return
        point = mouse_on_plane(self.grab.normal, self.grab.tile.pos)
        if point is None:
            return
        drag = point - self.grab.start
        if drag.mag >= DRAG_THRESHOLD:
            grab, self.grab = self.grab, None
            self.request(self.drag_turn, grab, drag)


    def mouse_up(self, evt):
        self.grab = None


    def drag_turn(self, grab, drag):
        # turn the layer that the grabbed tile is in so that the tile moves the way it was dragged
        axes = [vector(1, 0, 0), vector(0, 1, 0), vector(0, 0, 1)]
        in_plane = [axis for axis in axes if abs(axis.dot(grab.normal)) < 0.5]
        direction = max(in_plane, key=lambda axis: abs(drag.dot(axis)))
        if drag.dot(direction) < 0:
            direction = direction * -1
    
        axis = grab.normal.cross(direction)
        layer = round(grab.tile.pos.dot(axis))
        self.start_layer_turn(axis, layer, 1)


    def scramble(self):
        # generate a random scramble 
        for i in range(30):
            self.moves.append(choice(POSSIBLE_MOVES))


    def show(self, text):
        # set the message shown below the buttons 
        self.message_text = text


    def work_out_solution(self):
        return solve(self.tiles), rotations_to_default(self.tiles)


    def set_solution_shown(self, shown):
        self.solution_shown = shown
        self.solution_stamp = None
        self.reveal_button.text = "hide solution" if shown else "reveal solution"
        if not shown:
            self.show("")


    def toggle_solution(self):
        self.set_solution_shown(not self.solution_shown)


    def refresh_solution(self):
        # automatically update the solution on screen to match turns in real time
        if not self.solution_shown or self.busy():
            return
        faces = self.view_faces()
        stamp = (self.version, tuple(sorted(faces.items())))
        if stamp == self.solution_stamp:
            return
        self.solution_stamp = stamp
        try:
            solution = solve(self.tiles)
        except ValueError as error:
            self.show(f"Could not solve the cube: {error}")
            return
        if not solution:
            self.set_solution_shown(False)
            return
        self.show(solution_in_view(solution, faces))


    def solve_cube(self):
        if self.busy():
            self.show("Wait for the cube to finish turning.")
            return
        try:
            solution, rotations = self.work_out_solution()
        except ValueError as error:
            self.show(f"Could not solve the cube: {error}")
            return
        self.moves.extend(parse_solution(solution) + [HIDE_SOLUTION] + rotations)
        self.set_solution_shown(True)


    def request(self, action, *args):
        # ask update() to carry out an action 
        self.requests.put((action, args))


    def process_requests(self):
        # carry out the requests 
        while not self.requests.empty():
            action, args = self.requests.get()
            try:
                action(*args)
            except Exception:
                traceback.print_exc()


    def flush_message(self):
        # put the message on screen if it has changed
        if self.message_text != self.message_shown:
            self.message_shown = self.message_text
            self.message.text = "\n" + self.message_text if self.message_text else ""


    def control(self):
        # define GUI controls for cube manipulation
        scene.append_to_caption(PAGE_SETUP)
        for move in POSSIBLE_MOVES + ROTATION_MOVES:
            button(bind=lambda _, move=move: self.request(self.press, move), text=move)
        button(bind=lambda _: self.request(self.scramble), text='scramble')
        self.reveal_button = button(bind=lambda _: self.request(self.toggle_solution),
                                    text='reveal solution')
        button(bind=lambda _: self.request(self.solve_cube), text='solve cube')
        self.message = wtext(text="")

        scene.bind('mousedown', self.mouse_down)
        scene.bind('mousemove', self.mouse_move)
        scene.bind('mouseup', self.mouse_up)


    def free_rotation(self):
        forward = scene.forward.hat
        up = scene.up
        if abs(forward.dot(up.hat)) > POLE_COSINE:
            scene.up = (up - forward * forward.dot(up)).hat


    def update(self):
        # Update the cube's state in each frame
        rate(60)
        self.process_requests()
        self.free_rotation()
        self.animations()
        self.move()
        self.refresh_solution()
        self.flush_message()


    def start(self):
        # Note: an error in one frame is shown in the terminal but it doesn't stop the cube
        self.control()
        while self.running:
            try:
                self.update()
            except Exception:
                traceback.print_exc()
