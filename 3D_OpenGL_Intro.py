from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# -------------------- CAMERA / WORLD --------------------
camera_pos = (500,0, 200)
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
        self.target_distance = 300  # how far ahead the mortar crosshair is
        self.score=0

    def muzzle_world_pos(self):
        """Approximate muzzle position in world space (front of turret)."""
        rad = math.radians(self.rot)
        forward_x = -math.sin(rad)
        forward_y =  math.cos(rad)
        x = self.pos[0] + forward_x * 30
        y = self.pos[1] + forward_y * 30
        z = 55
        return x, y, z

    def target_world_pos(self):
        """Crosshair directly in front of the tank at target_distance."""
        rad = math.radians(self.rot)
        forward_x = -math.sin(rad)
        forward_y =  math.cos(rad)
        tx = self.pos[0] + forward_x * self.target_distance
        ty = self.pos[1] + forward_y * self.target_distance
        return tx, ty, 0

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

    def draw_target_marker(self,h,j,k):
        tx, ty, tz = self.target_world_pos()
        draw_target_marker(tx, ty, tz,h,j,k)

    def straight_shoot(self):
        rad = math.radians(self.rot)
        speed = 8.0
        mx, my, mz = self.muzzle_world_pos()
        dx = speed * -math.sin(rad)
        dy = speed *  math.cos(rad)
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
    grassList = []
    i = 0
    while i < 1000:
        # Random position strictly inside the grid
        x = random.randint(-GRID_LENGTH + 20, GRID_LENGTH - 20)
        y = random.randint(-GRID_LENGTH + 20, GRID_LENGTH - 20)
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
    wall_height = 100
    L = -GRID_LENGTH
    R =  GRID_LENGTH
    B = -GRID_LENGTH
    T =  GRID_LENGTH

    glColor3f(0.3, 0.3, 0.35)
    glBegin(GL_QUADS)
    glVertex3f(L, B, 0); glVertex3f(L, T, 0); glVertex3f(L, T, wall_height); glVertex3f(L, B, wall_height)
    glEnd()

    glColor3f(0.35, 0.35, 0.4)
    glBegin(GL_QUADS)
    glVertex3f(R, T, 0); glVertex3f(R, B, 0); glVertex3f(R, B, wall_height); glVertex3f(R, T, wall_height)
    glEnd()

    glColor3f(0.4, 0.4, 0.45)
    glBegin(GL_QUADS)
    glVertex3f(L, T, 0); glVertex3f(R, T, 0); glVertex3f(R, T, wall_height); glVertex3f(L, T, wall_height)
    glEnd()

    glColor3f(0.45, 0.45, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(R, B, 0); glVertex3f(L, B, 0); glVertex3f(L, B, wall_height); glVertex3f(R, B, wall_height)
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
def draw_target_marker(x, y, z,a,b,c):
    glDisable(GL_LIGHTING)
    glLineWidth(2)
    glColor3f(a,b,c)
    size = 30
    glBegin(GL_LINES)
    glVertex3f(x - size, y, z + 0.1); glVertex3f(x + size, y, z + 0.1)
    glVertex3f(x, y - size, z + 0.1); glVertex3f(x, y + size, z + 0.1)
    glEnd()
# -------------------- TEXT --------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top
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
    global tank1, tank2
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
def update_bullets(shooter, target):
    """Update bullets for one tank, detect hits on the other tank."""
    new_bullets = []
    n = len(shooter.bullets) // 7
    hit_radius = 40   # approximate tank hitbox radius
    for i in range(n):
        # advance bullet
        x = shooter.bullets[i*7] + shooter.bullets[i*7+3]
        y = shooter.bullets[i*7+1] + shooter.bullets[i*7+4]
        z = shooter.bullets[i*7+2] + shooter.bullets[i*7+5]
        dx = shooter.bullets[i*7+3]
        dy = shooter.bullets[i*7+4]
        dz = shooter.bullets[i*7+5] + shooter.bullets[i*7+6]
        g  = shooter.bullets[i*7+6]
        # --- check hit against target tank’s actual position ---
        tx, ty, tz = target.pos
        if abs(x - tx) < hit_radius and abs(y - ty) < hit_radius and 0 <= z <= 80:
            shooter.score += 1
            continue  # remove bullet on hit
        # --- keep bullet only if inside grid and above ground ---
        if -GRID_LENGTH < x < GRID_LENGTH and -GRID_LENGTH < y < GRID_LENGTH and z >= 0:
            new_bullets.extend([x, y, z, dx, dy, dz, g])
    shooter.bullets = new_bullets

def animate():
    global tank1, tank2
    update_bullets(tank1,tank2)
    update_bullets(tank2,tank1)
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
    draw_text(10, 730, f"Player 1(Blue) score: {tank1.score}")
    draw_text(10, 700, f'Player 2(Green) score: {tank2.score}')
    draw_grass()
    drawgrid()
    drawwall()
    alltrees()

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
