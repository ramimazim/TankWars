from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# -------------------- CAMERA / WORLD --------------------
camera_pos = (0, -500, 200)
fovY = 120
GRID_LENGTH = 600
gLen = 600
level = 0
grassList = []
treelist = []
cangle = 0
radius = 500

# -------------------- TANK CLASS --------------------
class Tank:
    def __init__(self, color_base, color_turret, bullet_color, spawn):
        self.pos = [spawn[0], spawn[1], 0]
        self.rot = 0
        self.color_base = color_base
        self.color_turret = color_turret
        self.bullet_color = bullet_color
        self.bullets = []  # flat array of [x,y,z, dx,dy,dz, g_per_frame]
        # Target marker for mortar (where the shell is calculated to land)
        self.mortar_offset = (200, 200)  # (dx, dy) from current tank pos

    def muzzle_world_pos(self):
        """Approximate muzzle position in world space (front of turret)."""
        # Tank base at z=0; turret top ~50, muzzle ~55 in model
        # Muzzle offset is along facing direction (local +X before we rotate)
        rad = math.radians(self.rot)
        forward_x = -math.sin(rad)
        forward_y =  math.cos(rad)
        # 20 is the local +X used in draw(); push a tad farther so it clears the turret
        x = self.pos[0] + forward_x * 30
        y = self.pos[1] + forward_y * 30
        z = 55  # gun height
        return x, y, z

    def draw(self):
        x, y, z = self.pos
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(self.rot + 90, 0, 0, 1)

        # Base (frustum)
        glPushMatrix()
        glColor3f(*self.color_base)
        gluCylinder(gluNewQuadric(), 70, 20, 60, 30, 30)
        glPopMatrix()

        # Turret (cube)
        glPushMatrix()
        glColor3f(*self.color_turret)
        glTranslatef(0, 0, 50)
        glScalef(2.5, 2.0, 1.2)
        glutSolidCube(20)
        glPopMatrix()

        # Gun (barrel)
        glPushMatrix()
        glColor3f(0, 0, 0)
        glTranslatef(20, 0, 55)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 3, 3, 40, 10, 10)
        glPopMatrix()

        glPopMatrix()

    def draw_target_marker(self):
        """Draw a ground crosshair + ring where the mortar will land."""
        tx = self.pos[0] + self.mortar_offset[0]
        ty = self.pos[1] + self.mortar_offset[1]
        tz = 0
        draw_target_marker(tx, ty, tz)

    def straight_shoot(self):
        """Fire a straight (no gravity) round from the muzzle, parallel to ground."""
        rad = math.radians(self.rot)
        speed = 8.0
        mx, my, mz = self.muzzle_world_pos()
        dx = speed * -math.sin(rad)
        dy = speed *  math.cos(rad)
        dz = 0.0                     # straight — no vertical component
        g_per_frame = 0.0            # no gravity for straight rounds
        self.bullets.extend([mx, my, mz, dx, dy, dz, g_per_frame])

    def mortar_shoot(self):
        """Fire an arcing round that lands at the target marker."""
        px, py, pz = self.pos
        tx = px + self.mortar_offset[0]
        ty = py + self.mortar_offset[1]
        # Fire from muzzle so it clears the turret
        mx, my, mz = self.muzzle_world_pos()

        # Kinematics: choose T and g to solve for dz so z(T)=0
        g = -0.15
        T = 120.0
        dx = (tx - mx) / T
        dy = (ty - my) / T
        # Solve for dz so that mz + dz*T + 0.5*g*T^2 = 0
        dz = (0 - mz - 0.5 * g * (T**2)) / T
        self.bullets.extend([mx, my, mz, dx, dy, dz, g])

    def move_forward(self):
        rad = math.radians(self.rot)
        speed = 10.0
        nx = self.pos[0] + speed * -math.sin(rad)
        ny = self.pos[1] + speed *  math.cos(rad)
        if -GRID_LENGTH + 20 < nx < GRID_LENGTH - 20 and -GRID_LENGTH + 20 < ny < GRID_LENGTH - 20:
            self.pos[0], self.pos[1] = nx, ny

    def move_backward(self):
        rad = math.radians(self.rot)
        speed = 10.0
        nx = self.pos[0] - speed * -math.sin(rad)
        ny = self.pos[1] - speed *  math.cos(rad)
        if -GRID_LENGTH + 20 < nx < GRID_LENGTH - 20 and -GRID_LENGTH + 20 < ny < GRID_LENGTH - 20:
            self.pos[0], self.pos[1] = nx, ny

    def rotate_left(self):
        self.rot = (self.rot + 5) % 360

    def rotate_right(self):
        self.rot = (self.rot - 5) % 360


# -------------------- TANKS --------------------
tank1 = Tank(color_base=(0, 0, 1), color_turret=(1, 0, 0), bullet_color=(1, 0, 0),
             spawn=(random.randint(-300, 300), random.randint(-300, 300)))
tank2 = Tank(color_base=(0, 1, 0), color_turret=(1, 1, 0), bullet_color=(1, 0, 1),
             spawn=(random.randint(-300, 300), random.randint(-300, 300)))

# -------------------- ENVIRONMENT --------------------
def grass_init(row, col):
    global grassList
    i = 0
    while i < 1000:
        x = random.randint(-600, 400)
        y = random.randint(-500, 500)
        g = random.uniform(0.7, 0.9)
        col_index = int((x + (col // 2) * gLen) // gLen)
        row_index = int(((row // 2) * gLen - y) // gLen)
        if 0 <= row_index < row and 0 <= col_index < col:
            grassList.append((x - gLen, y, g))
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

def drawgrid():
    tsize = 45
    for i in range(-GRID_LENGTH, GRID_LENGTH, tsize):
        for j in range(-GRID_LENGTH, GRID_LENGTH, tsize):
            if ((i + j) // tsize) % 2 == 0:
                glColor3f(0.82, 0.71, 0.55)
            else:
                glColor3f(0.72, 0.75, 0.32)
            glBegin(GL_QUADS)
            glVertex3f(i, j, 0)
            glVertex3f(i + tsize, j, 0)
            glVertex3f(i + tsize, j + tsize, 0)
            glVertex3f(i, j + tsize, 0)
            glEnd()

def drawwall():
    """Four vertical boundary walls with consistent CCW winding."""
    wall_height = 100
    L = -GRID_LENGTH
    R =  GRID_LENGTH
    B = -GRID_LENGTH
    T =  GRID_LENGTH

    # Left wall (x=L)
    glColor3f(0.3, 0.3, 0.35)
    glBegin(GL_QUADS)
    glVertex3f(L, B, 0)
    glVertex3f(L, T, 0)
    glVertex3f(L, T, wall_height)
    glVertex3f(L, B, wall_height)
    glEnd()

    # Right wall (x=R)
    glColor3f(0.35, 0.35, 0.4)
    glBegin(GL_QUADS)
    glVertex3f(R, T, 0)
    glVertex3f(R, B, 0)
    glVertex3f(R, B, wall_height)
    glVertex3f(R, T, wall_height)
    glEnd()

    # Top wall (y=T)
    glColor3f(0.4, 0.4, 0.45)
    glBegin(GL_QUADS)
    glVertex3f(L, T, 0)
    glVertex3f(R, T, 0)
    glVertex3f(R, T, wall_height)
    glVertex3f(L, T, wall_height)
    glEnd()

    # Bottom wall (y=B)
    glColor3f(0.45, 0.45, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(R, B, 0)
    glVertex3f(L, B, 0)
    glVertex3f(L, B, wall_height)
    glVertex3f(R, B, wall_height)
    glEnd()

def draw_tree(x=0, y=0, z=0, scale=2):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(scale, scale, scale)
    glPushMatrix()
    glColor3f(0.55, 0.27, 0.07)
    glTranslatef(0, 0, 15)
    glScalef(8, 8, 30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.0, 0.6, 0.0)
    glTranslatef(0, 0, 30)
    glutSolidSphere(17, 6, 10)
    glPopMatrix()
    glPopMatrix()

def treespawn():
    global treelist
    treelist = []
    for i in range(10):
        x = random.randint(-GRID_LENGTH + 20, GRID_LENGTH - 20)
        y = random.randint(-GRID_LENGTH + 20, GRID_LENGTH - 20)
        scale = random.randint(1, 3)
        treelist.append((x, y, 0, scale))

def alltrees():
    for i in treelist:
        x, y, z, scale = i
        draw_tree(x, y, z, scale)

# -------------------- HELPERS --------------------
def draw_target_marker(x, y, z=0):
    """Draw a thin crosshair and ring on the ground."""
    glDisable(GL_LIGHTING)
    glLineWidth(2)
    glColor3f(0, 0, 0)
    size = 25
    # Cross
    glBegin(GL_LINES)
    glVertex3f(x - size, y, z + 0.1)
    glVertex3f(x + size, y, z + 0.1)
    glVertex3f(x, y - size, z + 0.1)
    glVertex3f(x, y + size, z + 0.1)
    glEnd()
    # Ring
    glBegin(GL_LINE_LOOP)
    segments = 24
    r = 18
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        glVertex3f(x + r * math.cos(ang), y + r * math.sin(ang), z + 0.1)
    glEnd()

# -------------------- CONTROLS --------------------
def keyboardListener(key, x, y):
    global tank1, tank2
    # Tank 1 (WASD + F/G)
    if key == b'w': tank1.move_forward()
    if key == b's': tank1.move_backward()
    if key == b'a': tank1.rotate_left()
    if key == b'd': tank1.rotate_right()
    if key == b'q': tank1.straight_shoot()
    if key == b'e': tank1.mortar_shoot()

    # Tank 2 (IJKL + N/M)
    if key == b'i': tank2.move_forward()
    if key == b'k': tank2.move_backward()
    if key == b'j': tank2.rotate_left()
    if key == b'l': tank2.rotate_right()
    if key == b'u': tank2.straight_shoot()
    if key == b'o': tank2.mortar_shoot()

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

# -------------------- BULLETS & ANIMATION --------------------
def update_bullets(bullets):
    """Update bullets; each bullet has its own gravity factor g per frame."""
    new_bullets = []
    n = len(bullets) // 7
    for i in range(n):
        x  = bullets[i*7]     + bullets[i*7+3]
        y  = bullets[i*7+1]   + bullets[i*7+4]
        z  = bullets[i*7+2]   + bullets[i*7+5]
        dx = bullets[i*7+3]
        dy = bullets[i*7+4]
        dz = bullets[i*7+5]   + bullets[i*7+6]  # add per-bullet gravity
        g  = bullets[i*7+6]
        # Keep while above ground
        if z >= 0:
            new_bullets.extend([x, y, z, dx, dy, dz, g])
    return new_bullets

def animate():
    global tank1, tank2
    tank1.bullets = update_bullets(tank1.bullets)
    tank2.bullets = update_bullets(tank2.bullets)
    glutPostRedisplay()

def draw_bullets(bullets, color):
    glColor3f(*color)
    n = len(bullets) // 7
    for i in range(n):
        glPushMatrix()
        glTranslatef(bullets[i*7], bullets[i*7+1], bullets[i*7+2])
        glutSolidCube(5)
        glPopMatrix()

# -------------------- CAMERA & DISPLAY --------------------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()

    draw_grass()
    drawgrid()
    drawwall()
    alltrees()

    # Tanks
    tank1.draw()
    tank2.draw()

    # Target markers (mortar landing points)
    tank1.draw_target_marker()
    tank2.draw_target_marker()

    # Bullets
    draw_bullets(tank1.bullets, tank1.bullet_color)
    draw_bullets(tank2.bullets, tank2.bullet_color)

    glutSwapBuffers()

# -------------------- INIT (Depth, Culling, Clear) --------------------
def init_gl_state():
    glEnable(GL_DEPTH_TEST)        # fix walls flicker/disappear
    glDepthFunc(GL_LEQUAL)
    glClearDepth(1.0)
    glDisable(GL_CULL_FACE)        # render both sides; safer with custom quads
    glShadeModel(GL_SMOOTH)
    glClearColor(0.52, 0.80, 0.92, 1.0)  # sky-ish background

# -------------------- MAIN --------------------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D OpenGL Tanks - Two Player")
    init_gl_state()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(animate)
    grass_init(10, 10)
    treespawn()
    glutMainLoop()

if __name__ == "__main__":
    main()
