# solve.py
#
# Author: Christopher Yu
# Email: chrisdtyu@gmail.com
#
# Code to get solution to the cube.

import kociemba

FACE_ORDER = "URFDLB"

FACE_COLORS = {
    'F': (0, 1, 0),        # green
    'R': (1, 0, 0),        # red
    'B': (0, 0, 1),        # blue
    'L': (1, 0.647, 0),    # orange
    'U': (1, 1, 1),        # white
    'D': (1, 1, 0),        # yellow
}
SOLVED_CUBE = "".join(face * 9 for face in FACE_ORDER)

# position of each tile on the solved cube
_THREE = (-1, 0, 1)
FACELET_POSITIONS = (
    [(x, 1.5, z) for z in _THREE for x in _THREE]                          # U
    + [(1.5, y, z) for y in reversed(_THREE) for z in reversed(_THREE)]    # R
    + [(x, y, 1.5) for y in reversed(_THREE) for x in _THREE]              # F
    + [(x, -1.5, z) for z in reversed(_THREE) for x in _THREE]             # D
    + [(-1.5, y, z) for y in reversed(_THREE) for z in _THREE]             # L
    + [(x, y, -1.5) for y in reversed(_THREE) for x in reversed(_THREE)]   # B
)

# rotating the entire cube
ROTATION_CYCLES = {'x': "FUBD", 'y': "FLBR", 'z': "URDL"}
ROTATION_MOVES = ["x", "x'", "y", "y'", "z", "z'"]


def proximity(pos, target, delta=0.2):
    return all(abs(p - t) < delta for p, t in zip((pos.x, pos.y, pos.z), target))


def read_colors(tiles):
    # the colour of the tile at each position
    colors = []
    for target in FACELET_POSITIONS:
        tile = next((t for t in tiles if proximity(t.pos, target)), None)
        if tile is None:
            raise ValueError("the cube is not in a fixed position (is a turn still in progress?)")
        colors.append((tile.color.x, tile.color.y, tile.color.z))
    return colors


def read_centers(tiles):
    colors = read_colors(tiles)
    return {face: colors[9 * index + 4] for index, face in enumerate(FACE_ORDER)}


def decode_position(tiles):
    colors = read_colors(tiles)
    face_of_color = {colors[9 * index + 4]: face for index, face in enumerate(FACE_ORDER)}
    return "".join(face_of_color[color] for color in colors)


def rotate_centers(centers, move):
    cycle = ROTATION_CYCLES[move[0]]
    step = -1 if move.endswith("'") else 1
    rotated = dict(centers)
    for index, face in enumerate(cycle):
        rotated[cycle[(index + step) % len(cycle)]] = centers[face]
    return rotated


def rotations_to_default(tiles):
    goal = dict(FACE_COLORS)
    start = read_centers(tiles)
    queue = [(start, [])]
    seen = {tuple(sorted(start.items()))}
    for centers, path in queue:
        if centers == goal:
            return path
        for move in ROTATION_MOVES:
            rotated = rotate_centers(centers, move)
            key = tuple(sorted(rotated.items()))
            if key not in seen and len(path) < 4:
                seen.add(key)
                queue.append((rotated, path + [move]))
    return []


def solve(tiles):
    # returns the solution as a string of moves (algorithm) 
    cube = decode_position(tiles)
    if cube == SOLVED_CUBE:
        return ""
    return kociemba.solve(cube)


def parse_solution(solution):
    moves = []
    for move in solution.split():
        if move.endswith('2'):
            moves += [move[0]] * 2
        else:
            moves.append(move)
    return moves
