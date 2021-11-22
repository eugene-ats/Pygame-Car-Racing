import pygame
import time
import math
pygame.init()

# Load medias
def scale_img(img, factor):
    newDimension = round(img.get_width()*factor), round(img.get_height()*factor)
    return pygame.transform.scale(img, newDimension)

GRASS = scale_img(pygame.image.load('media/grass-resized.jpg'), 0.8)
TRACK = scale_img(pygame.image.load('media/track.png'), 0.9)
TRACK_BORDER = scale_img(pygame.image.load('media/track-border.png'), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
FINISH_LINE = pygame.image.load('media/finish.png')
FINISH_MASK = pygame.mask.from_surface(FINISH_LINE)
FINISH_POSITION = (134, 258)

CAR_WHITE = pygame.image.load('media/car-white-resized.png')
CAR_YELLOW = pygame.image.load('media/car-yellow-resized.png')
ICON = pygame.image.load('media/car-yellow-icon-32px.png')

cheer_sound = pygame.mixer.Sound("media/crowd_cheer.wav")

# Create window
width, height = TRACK.get_width(), TRACK.get_height()
win = pygame.display.set_mode((width, height))
pygame.display.set_caption('Car Racing 8')
pygame.display.set_icon(ICON)

class GameInfo:
    LEVELS = 8
    def __init__(self, level=1):
        self.level = level
        self.started = False
        self.level_start_time = 0
        self.intro = True
        self.isPause = False
        self.mode = None

    def start_level(self):
        self.started = True
        self.level_start_time = time.time()

    def next_level(self):
        self.level += 1
        self.reset()

    def reset(self):
        self.started = False
        self.level_start_time = 0
        computer_car.current_point = 0
        player_1.resetPos()
        player_2.resetPos()
        computer_car.next_level(game.level - 1)

    def game_finished(self):
        return self.level > self.LEVELS

    def get_level_time(self):
        if not self.started:
            return 0
        return round(time.time() - self.level_start_time)

    def resetAll(self):
        self.reset()
        self.level = 1
        computer_car.vel = computer_car.max_vel
        computer_car.rotation_vel = 3
    
    def handlePause(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.intro = True
            self.isPause = True

class CarBasic:
    def __init__(self, max_vel, rotation_vel, start_pos):
        self.img = self.IMG
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.start_pos = start_pos
        self.x, self.y = self.start_pos
        self.acceleration = 0.08
        self.point = 0

    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_vel
        elif right: 
            self.angle -= self.rotation_vel

    def draw_car(self, win):
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def move(self):
        radians = math.radians(self.angle)
        vertical = math.cos(radians) * self.vel
        horizontal = math.sin(radians) * self.vel
        self.y -= vertical
        self.x -= horizontal

    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel/2)
        self.move()

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.img)
        offset = (int(self.x - x), int(self.y - y))
        pointOfIntersection = mask.overlap(car_mask, offset)
        return pointOfIntersection

    def resetPos(self):
        self.x, self.y = self.start_pos
        self.angle, self.vel = 0, 0

class PlayerCar(CarBasic):
    IMG = CAR_WHITE
    
    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()

    def bounceOff(self):
        self.vel = -self.vel/1.6
        self.move()
    
    def win_point(self):
        self.point += 1

class ComputerCar(CarBasic):
    IMG = CAR_YELLOW
    def __init__(self, max_vel, rotation_vel, start_pos, path=[]):
        super().__init__(max_vel, rotation_vel, start_pos)
        self.path = path
        self.current_point = 0
        self.vel = max_vel

    def draw_points(self, win):
        for point in self.path:
            pygame.draw.circle(win, (255, 0, 0), point, 5)

    def draw_car(self, win):
        super().draw_car(win)
        # self.draw_points(win)

    def calculate_angle(self):
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y
        if y_diff == 0:
            desired_radian_angle = math.pi / 2
        else:
            desired_radian_angle = math.atan(x_diff / y_diff)
        # if the target's position is below computer's car
        if target_y > self.y:
            desired_radian_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radian_angle)
        if difference_in_angle >= 180:
            difference_in_angle -= 360
        # rotate to the right by the difference in angle between the car and the target point,
        # or by the rotation velocity if rotation vel is smaller than the difference in angle
        if  difference_in_angle > 0:
            self.angle -= min(self.rotation_vel, abs(difference_in_angle))
        else: 
            self.angle += min(self.rotation_vel, abs(difference_in_angle))

    def update_path_point(self):
        target = self.path[self.current_point]
        rect = pygame.Rect(self.x, self.y, self.img.get_width(), self.img.get_height())
        # if collide, update to the next target point index in the path array
        if rect.collidepoint(*target):
            self.current_point += 1

    def move(self):
        if self.current_point >= len(self.path):
            return
        self.calculate_angle()
        self.update_path_point()
        super().move()

    def next_level(self, level):
        self.resetPos()
        self.vel = self.max_vel + (level - 1) * 0.4
        self.rotation_vel = self.vel
        self.current_point = 0

class button:
    def __init__(self, msg, x, y, width, height, inactiveColor, activeColor, inactiveWordcolor="white", activeWordcolor="white"):
        self.pressed = False

        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if x+width > mouse[0] > x and y+height > mouse[1] > y:
            pygame.draw.rect(win, activeColor, (x, y, width, height), border_radius=22)
            buttonTxt = BTTN_FONT.render(msg, True, activeWordcolor)
            if click[0] == 1:
                game.intro = False
                self.pressed = True
        else:
            pygame.draw.rect(win, inactiveColor, (x, y, width, height), border_radius=22)
            buttonTxt = BTTN_FONT.render(msg, True, inactiveWordcolor)
            
        win.blit(buttonTxt, (x + width/2 - buttonTxt.get_width()/2, y + height/2 - buttonTxt.get_height()/2))
    
def draw(win, images, player1, game, player2=False, computer_car=False):
    for img, pos in images:
        win.blit(img, pos)
    def draw_level():
        level_text = RECORD_FONT.render(f"LEVEL {game.level}/8", 1, "white")
        win.blit(level_text, (16, height - level_text.get_height() - 100))
    def draw_vel():
        vel_text = RECORD_FONT.render(f"Velocity: {round(player1.vel, 1)}px/s", 1, "white")
        win.blit(vel_text, (16, height - vel_text.get_height() - 50))
    def draw_time():
        time_text = RECORD_FONT.render(f"Time: {game.get_level_time()}s", 1, "white")
        win.blit(time_text, (16, height - time_text.get_height() - 20))
    def draw_points():
        player_points = P_FONT.render(f"{player1.point} vs {player2.point}", 1, "white")
        win.blit(player_points, (16, height - player_points.get_height() - 100))

    player1.draw_car(win)
    if player2:
        player2.draw_car(win)
        draw_points()
        draw_time()
    elif computer_car:
        computer_car.draw_car(win)
        draw_level()
        draw_vel()
        draw_time()

    pygame.display.update()

def move_player(player1, player2=False):
    keys = pygame.key.get_pressed()
    moved = False
    if keys[pygame.K_LEFT]:
        player1.rotate(left=True)
    if keys[pygame.K_RIGHT]:
        player1.rotate(right=True)
    if keys[pygame.K_UP]:
        moved = True
        player1.move_forward()
    if keys[pygame.K_DOWN]:
        moved = True
        player1.move_backward()
    if not moved:
        player1.reduce_speed()
    
    if player2:
        moved2 = False
        if keys[pygame.K_a]:
            player2.rotate(left=True)
        if keys[pygame.K_d]:
            player2.rotate(right=True)
        if keys[pygame.K_w]:
            moved2 = True
            player2.move_forward()
        if keys[pygame.K_s]:
            moved2 = True
            player2.move_backward()
        if not moved2:
            player2.reduce_speed()

def handle_collision(player1, game, player2=False, computer_car=False):
    if player1.collide(TRACK_BORDER_MASK) != None:
        player1.bounceOff()

    if computer_car:
        player_finish_poi_collide = player1.collide(FINISH_MASK, *FINISH_POSITION)
        if player_finish_poi_collide != None:
            if player_finish_poi_collide[1] == 0:
                player1.bounceOff()
            else:
                blit_text_center(win, MAIN_FONT, f" You pass level {game.level}! ", background="black")   
                game.next_level()
                computer_car.next_level(game.level) 
                pygame.mixer.Sound.play(cheer_sound)
                pygame.display.update()
                pygame.time.wait(3000)

        computer_finish_poi_collide = computer_car.collide(FINISH_MASK, *FINISH_POSITION)
        if computer_finish_poi_collide != None:
            blit_text_center(win, MAIN_FONT, " You lost! ", background=(20, 20, 20))
            game.reset()
            pygame.display.update()
            pygame.time.wait(3000)

    elif player2:
        if player2.collide(TRACK_BORDER_MASK) != None:
            player2.bounceOff()

        player1_finish_poi_collide = player1.collide(FINISH_MASK, *FINISH_POSITION)
        if player1_finish_poi_collide != None:
            if player1_finish_poi_collide[1] == 0:
                player1.bounceOff()
            else:
                blit_text_center(win, MAIN_FONT, "Player 1 won!", background="black")    
                pygame.mixer.Sound.play(cheer_sound)     
                game.reset()
                player1.win_point()
                pygame.display.update()
                pygame.time.wait(3000)

        player2_finish_poi_collide = player2.collide(FINISH_MASK, *FINISH_POSITION)
        if player2_finish_poi_collide != None:
            if player2_finish_poi_collide[1] == 0:
                player2.bounceOff()
            else:
                blit_text_center(win, MAIN_FONT, "Player 2 won!", background="black")    
                pygame.mixer.Sound.play(cheer_sound)                    
                game.reset()
                player2.win_point()
                pygame.display.update()
                pygame.time.wait(3000)

def blit_rotate_center(surface, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    # Properly rotate the image on its center
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft = top_left).center)
    surface.blit(rotated_image, new_rect.topleft)

def blit_text_center(win, font, text, color=(244,244,244), background=None, offsetTop=0):
    render = font.render(text, 1, color, background)
    win.blit(render, (win.get_width()/2 - render.get_width()/2, win.get_height()/2 - render.get_height()/2 - offsetTop))

def handle_quit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()


FPS = 60
clock = pygame.time.Clock()
PATH = [(167, 114), (121, 67), (76, 112), (55, 446), (80, 497), (339, 744), (417, 688), (418, 549), (478, 481), (571, 472), (638, 552), (621, 702), (703, 747), (776, 669), (766, 415), (713, 349), (454, 348), (406, 306), (448, 247), (717, 215), (737, 77), (337, 56), (281, 107), (279, 373), (199, 370), (163, 267)]

MAIN_FONT = pygame.font.SysFont("consolas", 42)
TITLE_FONT = pygame.font.SysFont("consolas", 100, bold=True)
RECORD_FONT = pygame.font.SysFont("consolas", 26, italic=True)
BTTN_FONT = pygame.font.SysFont('consolas', 30, bold=True)
P_FONT = pygame.font.SysFont('consolas', 36)

imageList = [(GRASS, (0,0)), (TRACK, (0,0)), (FINISH_LINE, FINISH_POSITION), (TRACK_BORDER, (0, 0))]
button_width = 300
button_height = 60
button_x = win.get_width()/2 - button_width/2
button_y = 420

player_1 = PlayerCar(6, 5, (185, 200))
player_2 = PlayerCar(6, 5, (155, 200))
player_2.img = CAR_YELLOW
computer_car = ComputerCar(3, 3, (155, 200), PATH)
game = GameInfo()

# Main loop
run = True
while run:
    clock.tick(60)

    while game.intro:
        handle_quit()

        win.fill("white")
        blit_text_center(win, TITLE_FONT, "Car Racing 8", "black", offsetTop=120)

        singleBttn = button("Single-Player", button_x, button_y, button_width, button_height, (27, 168, 36), (26, 201, 38))
        dualBttn = button("Dual-Player", button_x, button_y+70, button_width, button_height, (217, 63, 11), (255, 67, 5))
        
        if game.isPause:
            resumeBttn = button('Resume', button_x, button_y+200, button_width, button_height, "white", "white", (90, 90, 90), "black")
            if resumeBttn.pressed:
                if game.mode == 'single':
                    singleBttn.pressed = True
                elif game.mode == 'dual':
                    dualBttn.pressed = True
            if game.mode == 'single':
                if dualBttn.pressed:
                    game.reset()
            elif game.mode == 'dual':
                if singleBttn.pressed: 
                    game.reset()

        pygame.display.update()
 

    if singleBttn.pressed:
        game.mode = 'single'
        draw(win, imageList, player_1, game, computer_car=computer_car)

        handle_quit()
        game.handlePause()
            
        # While player is not ready
        while not game.started:
            blit_text_center(win, MAIN_FONT, f" Press space key to start level {game.level}! ", background="black", offsetTop=40)
            blit_text_center(win, P_FONT, f" ESC key to pause ", background="black", offsetTop=-30)
            pygame.display.update()
            handle_quit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game.start_level()
        
        move_player(player_1)
        computer_car.move()
        handle_collision(player_1, game, computer_car=computer_car)

        if game.game_finished():
            blit_text_center(win, MAIN_FONT, " Congratulations, ", offsetTop=50)
            blit_text_center(win, MAIN_FONT, " You won the game! ", offsetTop=-50)
            pygame.display.update()
            pygame.time.wait(3000)
            game.resetAll()
    elif dualBttn.pressed:
        game.mode = 'dual'
        draw(win, imageList, player_1, game, player2=player_2)

        handle_quit()
        game.handlePause()

        while not game.started:
            blit_text_center(win, MAIN_FONT, f" Ready & press space key to start ", background="black", offsetTop=40)
            blit_text_center(win, P_FONT, f" ESC key to pause ", background="black", offsetTop=-30)
            playerNum2 = RECORD_FONT.render("2", True, (240,240,240))
            playerNum1 = RECORD_FONT.render("1", True, (240,240,240))
            win.blit(playerNum2, (160, 160))
            win.blit(playerNum1, (192, 160))
            pygame.display.update()
            handle_quit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game.start_level()

        move_player(player_1, player_2)
        handle_collision(player_1, game, player2=player_2)


pygame.quit()