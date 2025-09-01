from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys

# -------------------- CONFIG / WORLD --------------------
# Note: gLen is the size of a maze cell. GRID_LENGTH will be derived from maze size.
gLen = 300
GRID_LENGTH = 600   # will be updated by build_wall_list() to match the maze extents
WALL_HEIGHT = 50
TANK_RADIUS = 40    # consistent spawn & movement radius for tanks

# camera and rendering
camera_pos = (500, 0, 600)
fovY = 120
level = 2

# world lists
grassList = []
treeList = []
wall = []           # AABB list [(xmin,xmax,ymin,ymax), ...]
cangle = 0
radius = 500

# -------------------- MAZES --------------------
maze_layout_one = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,1,0,1,1,0,1],
    [1,0,1,0,0,0,0,1,0,1],
    [1,0,1,1,1,1,0,1,0,1],
    [1,0,0,0,0,1,0,1,0,1],
    [1,1,1,1,0,1,0,1,0,1],
    [1,0,0,1,0,0,0,1,0,1],
    [1,0,0,0,0,1,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1]
]

maze_layout_two = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,0,1,0,1,0,1],
    [1,0,1,0,0,1,0,0,0,1],
    [1,0,1,0,1,1,1,1,0,1],
    [1,0,0,0,1,0,0,1,0,1],
    [1,1,1,0,1,0,1,1,0,1],
    [1,0,0,0,0,0,1,0,0,1],
    [1,0,1,1,1,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1]
]

maze_layout_three = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,1,0,0,1,0,0,1,1],
    [1,0,1,1,0,1,1,0,0,1],
    [1,0,0,0,0,0,1,1,0,1],
    [1,1,1,0,1,1,0,1,0,1],
    [1,0,0,0,1,0,0,1,0,1],
    [1,0,1,1,1,0,1,1,0,1],
    [1,0,0,0,0,0,1,0,0,1],
    [1,1,0,1,1,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1]
]

# -------------------- TANK CLASS --------------------
class Tank:
    def __init__(self, color_base, color_turret, bullet_color, spawn, name="Tank"):
        self.pos = [spawn[0], spawn[1], 0]
        self.rot = 0
        self.color_base = color_base
        self.color_turret = color_turret
        self.bullet_color = bullet_color
        self.bullets = []           # [x,y,z, dx,dy,dz, g]
        self.target_distance = 300
        self.score = 0
        self.name = name

    def muzzle_world_pos(self):
        rad = math.radians(self.rot)
        forward_x = -math.sin(rad)
        forward_y = math.cos(rad)
        x = self.pos[0] + forward_x * 30
        y = self.pos[1] + forward_y * 30
        z = 55
        return x, y, z

    def target_world_pos(self):
        rad = math.radians(self.rot)
        forward_x = -math.sin(rad)
        forward_y = math.cos(rad)
        tx = self.pos[0] + forward_x * self.target_distance
        ty = self.pos[1] + forward_y * self.target_distance
        return tx, ty, 0

    def draw(self):
        x, y, z = self.pos
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(self.rot + 90, 0, 0, 1)

        # base
        glPushMatrix()
        glColor3f(*self.color_base)
        gluCylinder(gluNewQuadric(), 70, 20, 60, 30, 30)
        glPopMatrix()

        # turret
        glPushMatrix()
        glColor3f(*self.color_turret)
        glTranslatef(0, 0, 50)
        glScalef(2.5, 2.0, 1.2)
        glutSolidCube(20)
        glPopMatrix()

        # gun
        glPushMatrix()
        glColor3f(0, 0, 0)
        glTranslatef(20, 0, 55)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 3, 3, 40, 10, 10)
        glPopMatrix()

        glPopMatrix()

    def draw_target_marker(self, r, g, b):
        tx, ty, tz = self.target_world_pos()
        draw_target_marker(tx, ty, tz, r, g, b)

    def straight_shoot(self):
        rad = math.radians(self.rot)
        speed = 8.0
        mx, my, mz = self.muzzle_world_pos()
        dx = speed * -math.sin(rad)
        dy = speed * math.cos(rad)
        dz = 0.0
        g_per_frame = 0.0
        self.bullets.extend([mx, my, mz, dx, dy, dz, g_per_frame])

    def mortar_shoot(self):
        mx, my, mz = self.muzzle_world_pos()
        tx, ty, tz = self.target_world_pos()
        g = -0.15
        T = 120.0
        dx = (tx - mx) / T
        dy = (ty - my) / T
        dz = (tz - mz - 0.5 * g * (T**2)) / T
        self.bullets.extend([mx, my, mz, dx, dy, dz, g])

    def move_forward(self):
        rad = math.radians(self.rot)
        speed = 10.0
        nx = self.pos[0] + speed * -math.sin(rad)
        ny = self.pos[1] + speed * math.cos(rad)

        # boundary check uses updated GRID_LENGTH which matches the maze extents
        if -GRID_LENGTH + 20 < nx < GRID_LENGTH - 20 and -GRID_LENGTH + 20 < ny < GRID_LENGTH - 20:
            if not wall_collision(nx, ny, TANK_RADIUS):
                self.pos[0], self.pos[1] = nx, ny

    def move_backward(self):
        rad = math.radians(self.rot)
        speed = 10.0
        nx = self.pos[0] - speed * -math.sin(rad)
        ny = self.pos[1] - speed * math.cos(rad)
        if -GRID_LENGTH + 20 < nx < GRID_LENGTH - 20 and -GRID_LENGTH + 20 < ny < GRID_LENGTH - 20:
            if not wall_collision(nx, ny, TANK_RADIUS):
                self.pos[0], self.pos[1] = nx, ny

    def rotate_left(self):
        self.rot = (self.rot + 5) % 360

    def rotate_right(self):
        self.rot = (self.rot - 5) % 360


# Tanks will be set after wall list is built
tank1 = None
tank2 = None

# -------------------- ENVIRONMENT (grass/trees) --------------------
def grass_init(row, col):
    global grassList
    if level == 0:
        maze = maze_layout_one
    elif level == 1:
        maze = maze_layout_two
    else:
        maze = maze_layout_three

    grassList = []
    i = 0
    attempts = 0
    while i < 1000 and attempts < 5000:
        attempts += 1
        c = random.randint(0, col - 1)
        r = random.randint(0, row - 1)
        if maze[r][c] == 0:
            cx = (c - col // 2) * gLen
            cy = (row // 2 - r) * gLen
            # random offset inside cell with margins
            x = cx - random.randint(20, gLen - 20)
            y = cy - random.randint(20, gLen - 20)
            g = random.uniform(0.7, 0.9)
            grassList.append((x, y, g))
            i += 1

def draw_grass():
    for i in grassList:
        x, y, g = i
        offset = [0, -5, 5]
        for j in range(3):
            h = random.randint(8, 15)
            glBegin(GL_LINES)
            glColor3f(0, g, 0)
            glVertex3d(x, y, 0)
            glVertex3d(x + offset[j], y + offset[j], h)
            glEnd()

def tree_init(row, col):
    global treeList
    if level == 0:
        maze = maze_layout_one
    elif level == 1:
        maze = maze_layout_two
    else:
        maze = maze_layout_three

    treeList = []
    i = 0
    attempts = 0
    while i < 20 and attempts < 2000:
        attempts += 1
        c = random.randint(0, col - 1)
        r = random.randint(0, row - 1)
        if maze[r][c] == 0:
            cx = (c - col // 2) * gLen
            cy = (row // 2 - r) * gLen
            x = cx - random.randint(20, gLen - 20)
            y = cy - random.randint(20, gLen - 20)
            g = random.uniform(0.7, 0.9)
            treeList.append((x, y, g))
            i += 1

def draw_tree():
    for i in treeList:
        x, y, g = i
        glColor3f(0.55, 0.27, 0.07)
        glPushMatrix()
        glTranslatef(x, y, 0)
        gluCylinder(gluNewQuadric(), 15, 15, 60, 12, 12)
        glPopMatrix()
        glColor3f(0, g, 0)
        glPushMatrix()
        glTranslatef(x, y, 60)
        glutSolidSphere(40, 40, 20)
        glPopMatrix()

# -------------------- BUILD WALL AABBs --------------------
def build_wall_list(maze, row, col):
    """Build AABB wall list exactly matching draw_layout() coordinates.
       Also update GRID_LENGTH so movement bounds match the maze size.
    """
    global wall, GRID_LENGTH
    wall = []
    rows = len(maze)
    cols = len(maze[0])

    gRow = gLen * (row // 2)
    gCol = gLen * (col // 2)

    # cell walls AABBs (each 1 cell)
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 1:
                x = (c - cols // 2) * gLen
                y = (rows // 2 - r) * gLen
                xmin = x - gLen
                xmax = x
                ymin = y - gLen
                ymax = y
                wall.append((xmin, xmax, ymin, ymax))

    # outer boundary thickness
    thickness = 5.0

    # Left boundary (matches draw_walls left x = -gRow - gLen)
    left_x = -gRow - gLen
    wall.append((left_x, left_x + thickness, -gCol, gCol))

    # Right boundary (matches draw_walls right x = gRow - gLen)
    right_x = gRow - gLen
    wall.append((right_x - thickness, right_x, -gCol, gCol))

    # Top boundary (y = gCol)
    top_y = gCol
    wall.append((-gRow - gLen, gRow - gLen, top_y, top_y + thickness))

    # Bottom boundary (y = -gCol)
    bottom_y = -gCol
    wall.append((-gRow - gLen, gRow - gLen, bottom_y - thickness, bottom_y))

    # Update GRID_LENGTH so other code uses the same extents as maze
    GRID_LENGTH = max(abs(left_x), abs(right_x), abs(top_y), abs(bottom_y)) + gLen
    # make GRID_LENGTH a positive int
    GRID_LENGTH = int(GRID_LENGTH)

# -------------------- DRAW MAZE --------------------
def draw_maze(row, col):
    gCol = gLen * (col // 2)
    gRow = gLen * (row // 2)

    # floor tiles
    y = 0
    for j in range(row):
        x = 0
        for i in range(col):
            glBegin(GL_QUADS)
            glColor3f(0.25, 0.6, 0.2)
            glVertex3f(0 - gRow + x, 0 + gCol - y, 0)
            glVertex3f(0 - gRow - gLen + x, 0 + gCol - y, 0)
            glVertex3f(0 - gRow - gLen + x, 0 + gCol - gLen - y, 0)
            glVertex3f(0 - gRow + x, 0 + gCol - gLen - y, 0)
            glEnd()
            x += gLen
        y += gLen

    # pick maze to draw
    if level == 0:
        maze = maze_layout_one
    elif level == 1:
        maze = maze_layout_two
    else:
        maze = maze_layout_three

    # ensure wall AABB list is in sync
    build_wall_list(maze, row, col)

    # draw outer walls & layout
    draw_walls(gRow, gCol, row)
    draw_layout(maze)

def draw_walls(gRow, gCol, row):
    glColor3f(0.4, 0.4, 0.45)
    wall_height = WALL_HEIGHT

    # left
    glBegin(GL_QUADS)
    glVertex3f(-gRow - gLen, gCol, 0)
    glVertex3f(-gRow - gLen, -gCol, 0)
    glVertex3f(-gRow - gLen, -gCol, wall_height)
    glVertex3f(-gRow - gLen, gCol, wall_height)
    glEnd()

    # top
    glBegin(GL_QUADS)
    glVertex3f(-gRow - gLen, gCol, 0)
    glVertex3f(gRow - gLen, gCol, 0)
    glVertex3f(gRow - gLen, gCol, wall_height)
    glVertex3f(-gRow - gLen, gCol, wall_height)
    glEnd()

    # bottom
    y = gCol - row * gLen
    glBegin(GL_QUADS)
    glVertex3f(-gRow - gLen, y, 0)
    glVertex3f(gRow - gLen, y, 0)
    glVertex3f(gRow - gLen, y, wall_height)
    glVertex3f(-gRow - gLen, y, wall_height)
    glEnd()

    # right
    glBegin(GL_QUADS)
    glVertex3f(gRow - gLen, gCol, 0)
    glVertex3f(gRow - gLen, -gCol, 0)
    glVertex3f(gRow - gLen, -gCol, wall_height)
    glVertex3f(gRow - gLen, gCol, wall_height)
    glEnd()

def draw_layout(maze):
    glColor3f(0.6, 0.6, 0.65)
    rows = len(maze)
    cols = len(maze[0])

    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 1:
                x = (c - cols // 2) * gLen
                y = (rows // 2 - r) * gLen
                xmin = x - gLen
                xmax = x
                ymin = y - gLen
                ymax = y
                z0 = 0
                z1 = WALL_HEIGHT

                # top face
                glBegin(GL_QUADS)
                glVertex3f(xmin, ymax, z1)
                glVertex3f(xmax, ymax, z1)
                glVertex3f(xmax, ymin, z1)
                glVertex3f(xmin, ymin, z1)
                glEnd()

                # front face (ymax)
                glBegin(GL_QUADS)
                glVertex3f(xmin, ymax, z0)
                glVertex3f(xmax, ymax, z0)
                glVertex3f(xmax, ymax, z1)
                glVertex3f(xmin, ymax, z1)
                glEnd()

                # back face (ymin)
                glBegin(GL_QUADS)
                glVertex3f(xmin, ymin, z0)
                glVertex3f(xmax, ymin, z0)
                glVertex3f(xmax, ymin, z1)
                glVertex3f(xmin, ymin, z1)
                glEnd()

                # left face (xmin)
                glBegin(GL_QUADS)
                glVertex3f(xmin, ymin, z0)
                glVertex3f(xmin, ymax, z0)
                glVertex3f(xmin, ymax, z1)
                glVertex3f(xmin, ymin, z1)
                glEnd()

                # right face (xmax)
                glBegin(GL_QUADS)
                glVertex3f(xmax, ymin, z0)
                glVertex3f(xmax, ymax, z0)
                glVertex3f(xmax, ymax, z1)
                glVertex3f(xmax, ymin, z1)
                glEnd()

# -------------------- COLLISION HELPERS --------------------
def point_inside_aabb(px, py, aabb):
    xmin, xmax, ymin, ymax = aabb
    return xmin <= px <= xmax and ymin <= py <= ymax

def wall_collision(nx, ny, radius):
    """Circle-AABB collision: check if tank (circle center nx,ny radius) intersects any wall."""
    for xmin, xmax, ymin, ymax in wall:
        # find closest point on AABB to circle center
        qx = min(max(nx, xmin), xmax)
        qy = min(max(ny, ymin), ymax)
        dx = nx - qx
        dy = ny - qy
        if dx * dx + dy * dy <= radius * radius:
            return True
    return False

def segment_intersects_aabb(p1, p2, aabb):
    (x1, y1) = p1
    (x2, y2) = p2
    # sample along the segment every ~5 units
    steps = max(1, int(math.hypot(x2 - x1, y2 - y1) / 5))
    for s in range(1, steps + 1):
        t = s / steps
        xs = x1 + (x2 - x1) * t
        ys = y1 + (y2 - y1) * t
        if point_inside_aabb(xs, ys, aabb):
            return True
    return False

def bullet_hits_wall(prev_pos, new_pos, z_height):
    """Return True if bullet path between prev_pos and new_pos hits any wall at or above its z height.
       Mortar bullets with z > WALL_HEIGHT can pass above walls.
    """
    px, py = prev_pos
    nx, ny = new_pos
    for aabb in wall:
        # only consider collision if bullet is at or below wall height
        if z_height <= WALL_HEIGHT:
            if segment_intersects_aabb((px, py), (nx, ny), aabb):
                return True
    return False

# -------------------- HELPERS --------------------
def draw_target_marker(x, y, z, a, b, c):
    glDisable(GL_LIGHTING)
    glLineWidth(2)
    glColor3f(a, b, c)
    size = 30
    glBegin(GL_LINES)
    glVertex3f(x - size, y, z + 0.1); glVertex3f(x + size, y, z + 0.1)
    glVertex3f(x, y - size, z + 0.1); glVertex3f(x, y + size, z + 0.1)
    glEnd()
    glBegin(GL_LINE_LOOP)
    segments = 20
    r = 18
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        glVertex3f(x + r * math.cos(ang), y + r * math.sin(ang), z + 0.1)
    glEnd()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# -------------------- CONTROLS --------------------
def keyboardListener(key, x, y):
    global tank1, tank2,nuke_active, nuke_pos, nuke_radius
    if tank1 is None or tank2 is None:
        return
    if key == b'w': tank1.move_forward()
    if key == b's': tank1.move_backward()
    if key == b'a': tank1.rotate_left()
    if key == b'd': tank1.rotate_right()
    if key == b'q': tank1.straight_shoot()
    if key == b'e': tank1.mortar_shoot()

    if key == b'i': tank2.move_forward()
    if key == b'k': tank2.move_backward()
    if key == b'j': tank2.rotate_left()
    if key == b'l': tank2.rotate_right()
    if key == b'u': tank2.straight_shoot()
    if key == b'o': tank2.mortar_shoot()
    if key == b'n':  # start nuke
        nuke_active = True
        nuke_pos = [0, 0, 500]  # drop from above player
        nuke_radius = 0

def specialKeyListener(key, x, y):
    global camera_pos, cangle, radius
    if key == GLUT_KEY_LEFT:  cangle -= 1
    if key == GLUT_KEY_RIGHT: cangle += 1
    x, y, z = camera_pos
    if key == GLUT_KEY_UP:    z -= 10
    if key == GLUT_KEY_DOWN:  z += 10
    arad = math.radians(cangle)
    nx = radius * math.cos(arad)
    ny = radius * math.sin(arad)
    camera_pos = (nx, ny, z)

# -------------------- BULLETS & HIT DETECTION --------------------
def update_bullets(shooter, target):
    """Advance bullets, detect wall collisions, and detect hits against target tank."""
    new_bullets = []
    n = len(shooter.bullets) // 7
    hit_radius = TANK_RADIUS
    for i in range(n):
        bx = shooter.bullets[i*7]
        by = shooter.bullets[i*7+1]
        bz = shooter.bullets[i*7+2]
        dx = shooter.bullets[i*7+3]
        dy = shooter.bullets[i*7+4]
        dz = shooter.bullets[i*7+5]
        g = shooter.bullets[i*7+6]

        nx = bx + dx
        ny = by + dy
        nz = bz + dz

        # bullet collides with walls if its path intersects and its height <= wall height
        if bullet_hits_wall((bx, by), (nx, ny), bz):
            continue

        # new vertical velocity for next frame
        next_dz = dz + g

        # check hit against other tank's real position
        tx, ty, tz = target.pos
        if abs(nx - tx) < hit_radius and abs(ny - ty) < hit_radius and 0 <= nz <= 80:
            shooter.score += 1
            continue

        # keep bullet if inside maze/world extents and above ground
        if -GRID_LENGTH < nx < GRID_LENGTH and -GRID_LENGTH < ny < GRID_LENGTH and nz >= 0:
            new_bullets.extend([nx, ny, nz, dx, dy, next_dz, g])
    shooter.bullets = new_bullets

def animate():
    global tank1, tank2, nuke_active, nuke_pos, nuke_radius
    if tank1 is not None and tank2 is not None:
        update_bullets(tank1, tank2)
        update_bullets(tank2, tank1)
    
    if nuke_active:
        if nuke_pos[2] > 0:  # falling
            nuke_pos[2] -= nuke_speed
        else:  # explosion expanding
            nuke_radius += nuke_expand_speed
            if nuke_radius >= GRID_LENGTH:  # explosion covers the field
                sys.exit(0)  # end program immediately

    glutPostRedisplay()

def draw_bullets(bullets, color):
    glColor3f(*color)
    n = len(bullets) // 7
    for i in range(n):
        glPushMatrix()
        glTranslatef(bullets[i*7], bullets[i*7+1], bullets[i*7+2])
        glutSolidCube(5)
        glPopMatrix()


nuke_pos = [0, 0, 500]  
nuke_radius = 5          
nuke_active = False     
nuke_speed = 5           
nuke_expand_speed = 10  

def draw_nuke():
    global nuke_pos, nuke_radius, nuke_active
    if not nuke_active:
        return

    glPushMatrix()
    glColor4f(1.0, 0.5, 0.0, 0.8)  # orange semi-transparent
    if nuke_pos[2] > 0:
        # falling sphere
        glTranslatef(nuke_pos[0], nuke_pos[1], nuke_pos[2])
        glutSolidSphere(10, 20, 20)
    else:
        # expanding explosion
        glTranslatef(nuke_pos[0], nuke_pos[1], 0)
        glutSolidSphere(nuke_radius, 40, 40)
    glPopMatrix()







# -------------------- CAMERA & DISPLAY --------------------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def update_tank_scores(t1, t2):
    pass

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()

    if tank1 is not None and tank2 is not None:
        draw_text(10, 730, f"Player 1(Blue) score: {tank1.score}")
        draw_text(10, 700, f"Player 2(Green) score: {tank2.score}")


    draw_nuke()
    if not nuke_active or (nuke_radius < GRID_LENGTH*2):
        draw_maze(10, 10)
        draw_grass()
        draw_tree()



    if tank1 is not None and tank2 is not None:
        tank1.draw(); tank2.draw()
        tank1.draw_target_marker(0,0,1); tank2.draw_target_marker(1,1,0)
        draw_bullets(tank1.bullets, tank1.bullet_color)
        draw_bullets(tank2.bullets, tank2.bullet_color)

    glutSwapBuffers()

# -------------------- INIT --------------------
def init_gl_state():
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glClearDepth(1.0)
    glDisable(GL_CULL_FACE)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.52, 0.80, 0.92, 1.0)

# -------------------- SPAWN HELPERS --------------------
def find_safe_spawn(radius, row, col, max_attempts=2000):
    """Find free point inside a maze cell that doesn't collide with walls (consistent radius)."""
    if level == 0:
        maze = maze_layout_one
    elif level == 1:
        maze = maze_layout_two
    else:
        maze = maze_layout_three

    rows = len(maze)
    cols = len(maze[0])
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        c = random.randint(0, cols - 1)
        r = random.randint(0, rows - 1)
        if maze[r][c] == 0:  # free cell
            cx = (c - cols // 2) * gLen
            cy = (rows // 2 - r) * gLen
            # random offset inside the cell (leave margins)
            x = cx - random.randint(20, gLen - 20)
            y = cy - random.randint(20, gLen - 20)
            if not wall_collision(x, y, radius):
                return x, y
    # fallback: brute force inside whole world
    for _ in range(1000):
        x = random.randint(-GRID_LENGTH + 20, GRID_LENGTH - 20)
        y = random.randint(-GRID_LENGTH + 20, GRID_LENGTH - 20)
        if not wall_collision(x, y, radius):
            return x, y
    # still nothing; return center
    return 0, 0

# -------------------- MAIN --------------------
def main():
    global tank1, tank2
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D OpenGL Tanks - Maze collision fixed")
    init_gl_state()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(animate)

    # Create world lists and walls BEFORE spawning tanks
    grass_init(10, 10)
    tree_init(10, 10)

    # build walls (updates GRID_LENGTH to match maze extents)
    if level == 0:
        maze = maze_layout_one
    elif level == 1:
        maze = maze_layout_two
    else:
        maze = maze_layout_three
    build_wall_list(maze, 10, 10)

    # spawn two tanks in safe positions (consistent radius)
    sx1, sy1 = find_safe_spawn(TANK_RADIUS, 10, 10)
    sx2, sy2 = find_safe_spawn(TANK_RADIUS, 10, 10)
    attempts = 0
    while math.hypot(sx1 - sx2, sy1 - sy2) < 200 and attempts < 200:
        sx2, sy2 = find_safe_spawn(TANK_RADIUS, 10, 10)
        attempts += 1

    tank1 = Tank((0, 0, 1), (1, 0, 0), (1, 0, 0), (sx1, sy1), name="Tank1")
    tank2 = Tank((0, 1, 0), (1, 1, 0), (1, 0, 1), (sx2, sy2), name="Tank2")

    glutMainLoop()

if __name__ == "__main__":
    main()
