from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Camera-related variables
camera_pos = (0,500,500)

fovY = 120  # Field of view
GRID_LENGTH = 600  # Length of grid lines
rand_var = 423
p_pos=(0,0,0) 
p_rot=0

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
    
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)



def drawwall():
    wall_height = 100 
    #WALL1
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH,  GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH,  GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, wall_height)
    glColor3f(0,0,1)
    glEnd()

    #WALL2
    glBegin(GL_QUADS)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH,  GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH,  GRID_LENGTH, wall_height)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, wall_height)
    glColor3f(0,1,0)
    glEnd()

    #WALL3
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH,  GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH,  GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, wall_height)
    glColor3f(1,0,0)
    glEnd()

    #WALL4
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH,  -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH,  -GRID_LENGTH, wall_height)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, wall_height)
    glColor3f(1,1,1)
    glEnd()

def drawgrid():
    tsize = 60  
    num_tiles = GRID_LENGTH*2//tsize

    for i in range(-GRID_LENGTH, GRID_LENGTH, tsize):
        for j in range(-GRID_LENGTH, GRID_LENGTH, tsize):
            if ((i + j) // tsize)%2==0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.7, 0.4, 0.6)

            glBegin(GL_QUADS)
            glVertex3f(i,j,0)
            glVertex3f(i+tsize,j,0)
            glVertex3f(i+tsize,j+tsize,0)
            glVertex3f(i,j+tsize,0)
            glEnd()

def draw_tank():
    global p_pos, p_rot
    x, y, z = p_pos
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(p_rot, 0, 0, 1)

    # Base (blue, taller)
    glPushMatrix()
    glColor3f(0, 0, 1)  # blue
    glScalef(4, 2, 2)  # longer, wider, taller
    glutSolidCube(30)
    glPopMatrix()

    # Turret (red, smaller, sits on top of base)
    glPushMatrix()
    glColor3f(1, 0, 0)  # red
    glTranslatef(0, 0, 40)  # raised to sit above base
    glScalef(2, 1.5, 1)  # smaller than base
    glutSolidCube(20)
    glPopMatrix()

    # Gun (black, on the shorter face of the turret)
    glPushMatrix()
    glColor3f(0, 0, 0)  # black
    glTranslatef(20, 0, 40)  # attach to side of turret (X-axis face)
    glRotatef(90, 0, 1, 0)  # rotate to point forward along X
    gluCylinder(gluNewQuadric(), 3, 3, 40, 10, 10)
    glPopMatrix()

    glPopMatrix()


def keyboardListener(key, x, y):
    global player_pos, player_angle,fovY,camera_pos,target
    step = 10  # how much the target moves each press
    if key == b'j':  # move up
        target[1] += step
    elif key == b'u':  # move down
        target[1] -= step
    elif key == b'k':  # move left
        target[0] -= step
    elif key == b'h':  # move right
        target[0] += step


def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera angle and height.
    """
    global camera_pos
    x, y, z = camera_pos
    # Move camera up (UP arrow key)
    # if key == GLUT_KEY_UP:

    # # Move camera down (DOWN arrow key)
    # if key == GLUT_KEY_DOWN:

    # moving camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        x -= 1  # Small angle decrement for smooth movement

    # moving camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        x += 1  # Small angle increment for smooth movement

    camera_pos = (x, y, z)


def mouseListener(button, state, x, y):
    global bullets, player_pos, player_angle,camera_pos
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and death==False:
        mortar_shoot(target)


def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    # Set up a perspective projection (field of view, aspect ratio, near clip, far clip)
    gluPerspective(fovY, 1.25, 0.1, 1500) # Think why aspect ration is 1.25?
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix

    # Extract camera position and look-at target
    x, y, z = camera_pos
    # Position the camera and set its orientation
    gluLookAt(x, y, z,  # Camera position
              0, 0, 0,  # Look-at target
              0, 0, 1)  # Up vector (z-axis)


def animate():
    global bullets, miss,player_pos,player_angle
    glutPostRedisplay()
    x,y,z=player_pos
    # if cheat==True:
    #     player_angle+=1
    #     if player_angle>=360:
    #         player_angle-=360
    # if life==0 or miss==10:
    #     death=True
    # if grow==True:
    #     bodyradius += scaleval
    #     headradius += scaleval * 0.5
    #     if bodyradius > 30:
    #         grow = False
    # else:
    #     bodyradius -= scaleval
    #     headradius -= scaleval * 0.5
    #     if bodyradius < 15:
    #         grow = True
    # for i in range(5):
    #     # Move enemy towards player
    #     ex = enemy[i*2]ddd
    #     ey = enemy[i*2+1]
    #     px, py, pz = player_pos
    #     speed=0.05
    #     # Compute angle from enemy to player
    #     angle = math.atan2(py - ey, px - ex)
    #     # Move enemy towards player using trig
    #     ex += speed * math.cos(angle)
    #     ey += speed * math.sin(angle)
    #     enemy[i*2] = ex
    #     enemy[i*2+1] = ey
    #     if abs(ex - px) < 10 and abs(ey - py) < 10:
    #         life -= 1
    #         enemy[i*2] = random.randint(-GRID_LENGTH+10, GRID_LENGTH-10)
    #         enemy[i*2+1] = random.randint(-GRID_LENGTH+10, GRID_LENGTH-10) 
    #         enemyflag[i]=False
    #     if cheat==True:
    #         rad = math.radians(player_angle)
    #         xinc=-math.sin(rad)
    #         yinc=math.cos(rad)
    #         a,b,c=player_pos
    #         while -GRID_LENGTH<a+xinc<GRID_LENGTH and -GRID_LENGTH<b+yinc<GRID_LENGTH:
    #             if abs(ex - a) < 10 and abs(ey - b) < 10 and enemyflag[i]==False:
    #                 enemyflag[i]=True
    #                 shoot()
    #                 break
    #             a+=xinc
    #             b+=yinc
    g = -0.1  # gravity (must match mortar_shoot)
    new_bullets = []
    for i in range(len(bullets) // 6):
        x  = bullets[i*6]   + bullets[i*6+3]
        y  = bullets[i*6+1] + bullets[i*6+4]
        z  = bullets[i*6+2] + bullets[i*6+5]
        dx = bullets[i*6+3]
        dy = bullets[i*6+4]
        dz = bullets[i*6+5] + g   # gravity applied
        if z >= 0:  # still above ground
            new_bullets.extend([x, y, z, dx, dy, dz])
        else:
            miss += 1  # bullet hit the ground
    bullets = new_bullets


def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws everything of the screen
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size

    setupCamera()  # Configure camera perspective





    # Display game info text at a fixed screen position
    draw_text(10, 770, f"A Random Fixed Position Text")
    draw_text(10, 740, f"See how the position and variable change?: {rand_var}")


    drawgrid()
    drawwall()
    draw_tank()

    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()


# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"3D OpenGL Intro")  # Create the window

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(animate)  # Register the idle function to move the bullet automatically

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
