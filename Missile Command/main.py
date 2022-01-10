import pygame, os, math, time, random, csv, sys

from pygame.constants import K_KP_ENTER, K_SPACE, MOUSEBUTTONDOWN
from pygame.display import update
from pygame.version import PygameVersion

# Window setup
WIDTH = 1024
HEIGHT = 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Missile Command")
pygame.init()

# Required to Cap the FPS
FPS = 60
clock = pygame.time.Clock()

# Loading Assets
ground_img = pygame.image.load(os.path.join("Assets", "missile_command_ground.png"))
missile_img = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "missile_command_missile.png")), (15, 25))
missile_launcher_img = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "missile_command_launcher.png")), (40, 55))
missile_target_img = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "missile_command_X.png")), (20, 20))
building_image = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "missile_command_building.png")), (124, 65)) # Original Dimensions are 400, 250, 8:5 Ratio

font = pygame.font.Font(os.path.join("Assets", "AtariClassicChunky.ttf"), 24)
small_font = pygame.font.Font(os.path.join("Assets", "AtariClassicChunky.ttf"), 40)
medium_font = pygame.font.Font(os.path.join("Assets", "AtariClassicChunky.ttf"), 64)
large_font = pygame.font.Font(os.path.join("Assets", "AtariClassicChunky.ttf"), 90)

missile_offset = (missile_img.get_width() / 2, missile_img.get_height() / 2)
missile_launcher_offset = (missile_launcher_img.get_width() / 2, missile_launcher_img.get_height() / 2)
missile_target_offset = (missile_target_img.get_width() / 2, missile_target_img.get_height() / 2)
building_offset = (building_image.get_width() / 2, building_image.get_height() / 2)


# Variables, Arrays are to keep track of what is currently in the game
current_wave = 1
velocity = 3
score = 0
spawn_delay = 1
max_wave = 25

launchers = []
missiles = []
enemy_missiles = []
explosions = []
buildings = [(225, 675), (375, 675), (650, 675), (800, 675)]

building_coords = [(225, 675), (375, 675), (650, 675), (800, 675)]

class Missile_Launcher():
    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
        self.offset_x = missile_launcher_offset[0]
        self.offset_y = missile_launcher_offset[1]
        self.angle = 0

class Missile():
    def __init__(self, x, y, target_x, target_y, angle, velocity):
        self.image = missile_img
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.angle = angle
        self.velocity = velocity
        self.velocity_x = -velocity * math.sin(angle * (math.pi/180))
        self.velocity_y = -velocity * math.cos(angle * (math.pi/180))

    # Move the missile. If it comes in range of the target blow it up instead.
    def move(self):
        self.x += self.velocity_x
        self.y += self.velocity_y

        blitRotate(self.image, (self.x, self.y), (missile_offset[0], missile_offset[1]), self.angle)

class Explosion():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.expansion_rate = 0.5
        self.max_radius = 40
        self.colors = ["#FFFFFF", "#F482FF", "#B0FF82"]
        self.color_index = 0

    # Grow the explosion and change the color based off of what size the circle is currently at
    def grow(self):
        self.radius += self.expansion_rate
        if self.radius % 3 == 0:
            self.color_index = (self.color_index + 1) % 3
        pygame.draw.circle(screen, self.colors[self.color_index], (self.x, self.y), self.radius)

launchers.append(Missile_Launcher(missile_launcher_img, 92, 647))
launchers.append(Missile_Launcher(missile_launcher_img, 512, 647))
launchers.append(Missile_Launcher(missile_launcher_img, 933, 647))

# Handles all the game logic
def game():
    # Variables that need to be ran once at the start of each round
    global current_wave

    if current_wave > max_wave:
        current_wave = max_wave
        return game_over(True)

    missiles_shot = 0
    running = True
    wave_started = True
    start_time = time.time()
    enemies_to_spawn = 10 + current_wave # Simple might upgrade
    mouse_pos = (0, 0)
    enemies_defeated = 0
    pygame.display.set_caption(f"Wave: {current_wave}")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Which missile launcher to shoot from to lower the rocket's travel time only if the missile is above ground
                if mouse_pos[1] < 675 + building_offset[1]:
                    third = WIDTH / 3
                    if mouse_pos[0] < third:
                        index = 0
                    elif mouse_pos[0] < third * 2:
                        index = 1
                    else:
                        index = 2
                    
                    # Get the angle and then rotate the image (The rotate function is thanks to the guy I've left a link to above the blitrotate function)
                    angle = math.atan2(launchers[index].y - mouse_pos[1], launchers[index].x - mouse_pos[0]) * (180 / math.pi) - 90
                    launchers[index].angle = -angle
                    missiles.append(Missile(launchers[index].x, launchers[index].y, mouse_pos[0], mouse_pos[1], -angle, 6))
                    missiles_shot += 1

        # Spawn a missile at the delay specified
        if time.time() > start_time + spawn_delay and enemies_to_spawn > 0:
            spawn_enemy(mouse_pos)
            start_time = time.time()
            enemies_to_spawn -= 1

        # Handle the rendering
        screen.fill("#0C0C1E")
        enemies_defeated += render_game()
        pygame.display.update()

        # If there are no more enemy missiles then reset everything and spawn a new wave
        if enemies_to_spawn == 0 and len(enemy_missiles) < 1:
            current_wave += 1
            return between_waves(enemies_defeated, missiles_shot)

        # If there are no buildings the game is lost. Otherwise draw buildings. (Infinite Missiles. If somebody loses honestly that would be incredible.)
        if len(buildings) < 1:
            game_over(False)


        # This keeps the FPS at the value set
        clock.tick(FPS)

# This will render the main menu and have some menu options
def main_menu():

    reset_variables()

    missile_text = large_font.render("MISSILE", False, "#FFFFFF")
    missile_text_rect = missile_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 180))

    command_text = large_font.render("COMMAND", False, "#FFFFFF")
    command_text_rect = command_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 90))

    play_button = medium_font.render("PLAY", False, "#FFFFFF")
    play_button_rect = play_button.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 10))

    highscore_button = medium_font.render("HIGHSCORES", False, "#FFFFFF")
    highscore_button_rect = highscore_button.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 90))

    quit_button = medium_font.render("QUIT", False, "#FFFFFF")
    quit_button_rect = quit_button.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 170))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if play_button_rect.collidepoint(mouse_pos):
                    global score
                    score = 0
                    global current_wave
                    current_wave = 0
                    return game()
                elif highscore_button_rect.collidepoint(mouse_pos):
                    return highscores()
                elif quit_button_rect.collidepoint(mouse_pos):
                    sys.exit()

        # Render
        screen.fill("#0C0C1E")
    
        screen.blit(missile_text, missile_text_rect)
        screen.blit(command_text, command_text_rect)

        screen.blit(play_button, play_button_rect)
        pygame.draw.rect(screen, "#FFFFFF", play_button_rect, 2)

        screen.blit(highscore_button, highscore_button_rect)
        pygame.draw.rect(screen, "#FFFFFF", highscore_button_rect, 2)

        screen.blit(quit_button, quit_button_rect)
        pygame.draw.rect(screen, "#FFFFFF", quit_button_rect, 2)

        pygame.display.update()
        clock.tick(FPS)

# Handles rendering and just a lot of other logic since it was convienient for it to fit in here
def render_game():
    # This moves the missile towards the target and when the target is reached stop rendering the target and explode
    for missile in missiles:
        missile.move()
        screen.blit(missile_target_img, (missile.target_x - missile_target_offset[0], missile.target_y - missile_target_offset[1]))
        if missile.x >= missile.target_x - velocity and missile.x <= missile.target_x + velocity and missile.y >= missile.target_y - velocity and missile.y <= missile.target_y + velocity:
            explosions.append(Explosion(missile.target_x, missile.target_y))
            missiles.pop(missiles.index(missile))

    # Does the same thing but for enemy missiles they are separate and have some repeating code since these will have to detect collisions with explosions
    for missile in enemy_missiles:
        missile.move()
        if missile.x >= missile.target_x - velocity and missile.x <= missile.target_x + velocity and missile.y >= missile.target_y - velocity and missile.y <= missile.target_y + velocity:
            explosions.append(Explosion(missile.target_x, missile.target_y))
            enemy_missiles.pop(enemy_missiles.index(missile))

    # Draw missile launchers left to right
    for i in range(len(launchers)):
        blitRotate(launchers[i].image, (launchers[i].x, launchers[i].y), (launchers[i].offset_x, launchers[i].offset_y + 10), launchers[i].angle)
    
    # Draw rectangles that make it so the rocket launchers won't be visible from beneath the ground then any explosions then the ground
    pygame.draw.rect(screen, '#0C0C1E', (65, HEIGHT - 115, 50, 50))
    pygame.draw.rect(screen, '#0C0C1E', (WIDTH / 2 - 25, HEIGHT - 115, 50, 50))
    pygame.draw.rect(screen, '#0C0C1E', (WIDTH - 115, HEIGHT - 115, 50, 50))

    for building in buildings:
        screen.blit(building_image, (building[0] - building_offset[0], building[1] - building_offset[1]))

    # Handle everything to do with the explosions and their collisions with enemies and buildings then return a variable that stores how many enemies were defeated
    enemies_defeated = handle_explosions()

    screen.blit(ground_img, (0,0)) # The ground (it's called ground_img this comment is not even needed but here I am anyway)

    return enemies_defeated

# This displays your score, the amount of enemies defeated, missile shot, etc in between waves
def between_waves(enemies_defeated, missiles_shot):
    global current_wave
    global score
    deduction = (4 - len(building_coords)) * 500
    score += ((enemies_defeated * 100) * (enemies_defeated / missiles_shot)) - deduction
    score = int(round(score))

    # Max score cap since I doubt anyone will hit this high anyway and I want the score to not go too far on the transition screen
    if score > 999999999:
        score = 999999999
    
    score_text = medium_font.render(f"Score:{round(score)}", False, "#FFFFFF")
    score_text_rect = score_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 100))

    continue_text = font.render("Hit SPACE to contine to the next wave", False, "#FFFFFF")
    continue_text_rect = continue_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 100))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # If the player clicks then start the next wave
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    reset_variables()
                    return game()

        # Rendering
        screen.fill("#0C0C1E")

        screen.blit(score_text, score_text_rect)
        screen.blit(continue_text, continue_text_rect)

        pygame.display.update()
        clock.tick(FPS)

# This will display a menu for when the game is over and give the option to submit your score to the local leaderboard
def game_over(game_won):
    reset_variables()

    if game_won:
        result_text = font.render("Congratulations you've defended the Earth!", False, "#FFFFFF")
    else:
        result_text = font.render("That's a shame, you've lost.", False, "#FFFFFF")

    result_text_rect = result_text.get_rect(center=(WIDTH / 2, 150))

    score_text = font.render(f"Score: {score}", False, "#FFFFFF")
    score_text_rect = score_text.get_rect(center=(WIDTH / 2, 200))

    return_text = font.render("Hit SPACE to return to the Main Menu", False, "#FFFFFF")
    return_text_rect = return_text.get_rect(center=(WIDTH / 2, HEIGHT - 200))

    # Make sure that the score is high enough to be submitted before displaying the option to submit the score
    data = []
    submit_possible = True
    with open("highscores.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            data.append(row[1])

        if len(data) == 5:
            if score < int(data[-1]):
                submit_possible = False

    if submit_possible:
        submit_text = font.render(f"Hit ENTER to save your Score", False, "#FFFFFF")
        submit_text_rect = submit_text.get_rect(center=(WIDTH / 2, HEIGHT - 150))
    else:
        submit_text = font.render(f"Score is too low for the leaderboard", False, "#FFFFFF")
        submit_text_rect = submit_text.get_rect(center=(WIDTH / 2, HEIGHT - 150))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return main_menu()
                if event.key == pygame.K_RETURN and submit_possible:
                    return submit_score()

        # Rendering stuff
        screen.fill("#0C0C1E")

        screen.blit(result_text, result_text_rect)
        screen.blit(score_text, score_text_rect)
        screen.blit(return_text, return_text_rect)
        screen.blit(submit_text, submit_text_rect)

        pygame.display.update()
        clock.tick(FPS)

# This is where you can submit your score only if it is high enough.
def submit_score():

    scores = []
    name = []
    name_text = []

    with open("highscores.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            scores.append([row[0], round(int(row[1])), round(int(row[2]))])

    instructions = medium_font.render("Enter your Name", False, "#FFFFFF")
    instructions_rect = instructions.get_rect(center=(WIDTH / 2, 125))

    submit_text = font.render("Hit ENTER to submit", False, "#FFFFFF")
    submit_text_rect = submit_text.get_rect(center=(WIDTH / 2, HEIGHT - 100))

    return_text = font.render("Hit SPACE to go to the main menu", False, "#FFFFFF")
    return_text_rect = return_text.get_rect(center=(WIDTH / 2, HEIGHT - 150))

    running = True
    while running:
        event = pygame.event.poll()
        update_text = False

        if event.type == pygame.KEYDOWN:
            key = pygame.key.name(event.key)
            if key == "space":
                return main_menu()
            elif key == "return":
                if len(scores) == 5:
                    scores.pop()
                scores.append([''.join(name), score, current_wave])
                scores = sorted(scores, key=lambda x: x[1], reverse=True)

                with open("highscores.csv", "w", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["name", "score", "wave"])
                    for array in scores:
                        writer.writerow(array)
                return highscores()
            if key == "backspace":
                name.pop()
                update_text = True
            elif len(name) < 3 and len(key) == 1:
                name.append(key.upper())
                update_text = True
        
        if event.type == pygame.QUIT:
            running = False

        if update_text:
            x = -100
            name_text = []
            for letter in name:
                temp = large_font.render(f"{letter}", False, "#FFFFFF")
                temp_rect = temp.get_rect(center=(WIDTH / 2 + x, HEIGHT / 2))
                name_text.append([temp, temp_rect])
                x += 100

        # Render Stuff
        screen.fill("#0C0C1E")
        
        screen.blit(instructions, instructions_rect)
        for text in name_text:
            screen.blit(text[0], text[1])

        screen.blit(submit_text, submit_text_rect)
        screen.blit(return_text, return_text_rect)        

        pygame.display.update()
        clock.tick(FPS)

# Display scores
def highscores():
    running = True

    scores = []
    with open("highscores.csv", "r") as file:
        reader = csv.reader(file)
        next(reader)

        x = 270
        for row in reader:
            temp = font.render(f"{row[0]} {int(row[1])} {int(row[2])}", False, "#FFFFFF")
            temp_rect = temp.get_rect(center=(WIDTH / 2, x))
            scores.append([temp, temp_rect])
            x += 50

    category = small_font.render("Name Score and Wave", False, "#FFFFFF")
    category_rect = category.get_rect(center=(WIDTH / 2, 175))

    main_menu_text = font.render("Hit ENTER to return to the main menu", False, "#FFFFFF")
    main_menu_text_rect = main_menu_text.get_rect(center=(WIDTH / 2, HEIGHT - 200))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return main_menu()   

        # Render
        screen.fill("#0C0C1E")

        screen.blit(category, category_rect)
        for entry in scores:
            screen.blit(entry[0], entry[1])
        screen.blit(main_menu_text, main_menu_text_rect)

        pygame.display.update()
        clock.tick(FPS)

# This will spawn a randomized wave of increasing difficulty based off the current wave
def spawn_enemy(mouse_pos):
    x = random.randint(0, WIDTH)
    y = -missile_img.get_height()
    rand = random.choice(buildings)

    target = (rand[0], rand[1])

    angle = math.atan2(y - target[1], x - target[0]) * (180 / math.pi) - 90

    enemy_missiles.append(Missile(x, y, target[0], target[1], -angle, 2.5))

# Credit to this post for the following function -> https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
def blitRotate(image, pos, originPos, angle):

    # offset from pivot to center
    image_rect = image.get_rect(topleft = (pos[0] - originPos[0], pos[1] - originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    
    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # rotated image center
    rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

    # rotate and blit the image
    screen.blit(rotated_image, rotated_image_rect)

# Resets some things to default, mainly for transitions
def reset_variables():
    for launcher in launchers:
        launcher.angle = 0
    while len(explosions) > 0:
        explosions.pop()
    while len(missiles) > 0:
        missiles.pop()
    while len(enemy_missiles) > 0:
        enemy_missiles.pop()
    for coords in building_coords:
        try:
            buildings.index(coords)
        except ValueError:
            buildings.append(coords)
    
# Handles the Explosions, DUH
def handle_explosions():
    enemies_defeated = 0
    # Make the explosions get larger before they vanish when they reach their max radius also check for collisions with buildings and enemies
    for explosion in explosions:
        explosion.grow()
        if explosion.radius > explosion.max_radius:
            explosions.pop(explosions.index(explosion))
            break
        # 675 is the building Y coord. Don't bother checking if it can collide with buildings if it isn't even at a low enough Y level
        if explosion.y > 675 - building_offset[1] - explosion.max_radius:
            for building in buildings:
                # My own collision code just because I wanted to. Isn't incredible but it works and I may make it better if I have time.
                if explosion.y + explosion.radius > building[1] - building_offset[1]:
                    if explosion.x + explosion.radius > building[0] - building_offset[0] and explosion.x + explosion.radius < building[0] + building_offset[0]:
                        buildings.pop(buildings.index(building))
                    elif explosion.x - explosion.radius > building[0] - building_offset[0] and explosion.x - explosion.radius < building[0] + building_offset[0]:
                        buildings.pop(buildings.index(building))

        # Handle enemy missile collisions
        for missile in enemy_missiles:
            # Pick the point on the border of the circle that is closest to the missile
            angle = math.atan2(explosion.y - missile.y, explosion.x - missile.x)
            closest_point = ((explosion.radius * math.cos(angle + math.pi)) + explosion.x, (explosion.radius * math.sin(angle + math.pi)) + explosion.y)
            # pygame.draw.circle(screen, (255,0,0), closest_point, 3) # This line draws dots to make sure the closest_point was working
            missile_rect = missile.image.get_rect(center=(missile.x, missile.y))
            # If the point intercepts the rectange of the missile then the images have collided
            if missile_rect.collidepoint(closest_point):
                enemy_missiles.pop(enemy_missiles.index(missile))
                explosions.append(Explosion(missile.x, missile.y))
                enemies_defeated += 1
        
    return enemies_defeated

# Main
if __name__ == "__main__":
    main_menu()