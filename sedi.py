# ============================================================
#  RETRO RACER - Full 2D Arcade Racing Game (Single File)
#  Requires: pygame
#
#  Install:
#     pip install pygame
#
#  Run:
#     python retro_racer.py
#
#  FEATURES
#  - Smooth arcade driving
#  - AI traffic cars
#  - Infinite scrolling road
#  - Speed boost
#  - Score system
#  - High score
#  - Collision + explosion effect
#  - Particle effects
#  - Pause system
#  - Retro HUD
#  - Difficulty scaling
# ============================================================

import pygame
import random
import math
import sys

pygame.init()

# ============================================================
# SETTINGS
# ============================================================

WIDTH = 900
HEIGHT = 700
FPS = 60

ROAD_WIDTH = 420
ROAD_X = WIDTH // 2 - ROAD_WIDTH // 2

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
DARK_GRAY = (30, 30, 30)
GREEN = (40, 150, 40)
YELLOW = (255, 220, 0)
RED = (220, 50, 50)
BLUE = (50, 120, 255)
CYAN = (50, 220, 255)
ORANGE = (255, 140, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RETRO RACER")

clock = pygame.time.Clock()

font_big = pygame.font.SysFont("arial", 56, bold=True)
font_med = pygame.font.SysFont("arial", 30, bold=True)
font_small = pygame.font.SysFont("arial", 22)

# ============================================================
# GAME STATE
# ============================================================

high_score = 0

# ============================================================
# HELPERS
# ============================================================

def draw_text(text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

def clamp(v, mn, mx):
    return max(mn, min(mx, v))

# ============================================================
# PARTICLES
# ============================================================

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.life = random.randint(20, 40)
        self.size = random.randint(3, 7)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self):
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

# ============================================================
# PLAYER
# ============================================================

class Player:
    def __init__(self):
        self.width = 54
        self.height = 100
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 150

        self.speed = 0
        self.max_speed = 14
        self.accel = 0.28
        self.brake = 0.4
        self.turn_speed = 7

        self.boost = 100
        self.boosting = False

        self.alive = True

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys):

        # Acceleration
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += self.accel
        else:
            self.speed -= 0.12

        # Braking
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= self.brake

        # Clamp speed
        self.speed = clamp(self.speed, 0, self.max_speed)

        # Boost
        self.boosting = False
        if (keys[pygame.K_SPACE]) and self.boost > 0:
            self.boosting = True
            self.speed = self.max_speed + 7
            self.boost -= 0.7
        else:
            self.boost += 0.15

        self.boost = clamp(self.boost, 0, 100)

        # Turning
        move_amount = self.turn_speed * (self.speed / self.max_speed + 0.2)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= move_amount

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += move_amount

        # Road bounds
        left_bound = ROAD_X + 18
        right_bound = ROAD_X + ROAD_WIDTH - self.width - 18

        self.x = clamp(self.x, left_bound, right_bound)

    def draw(self):

        # Boost flame
        if self.boosting:
            pygame.draw.polygon(
                screen,
                ORANGE,
                [
                    (self.x + 12, self.y + self.height),
                    (self.x + self.width // 2, self.y + self.height + random.randint(15, 28)),
                    (self.x + self.width - 12, self.y + self.height)
                ]
            )

        # Shadow
        pygame.draw.rect(screen, (20, 20, 20),
                         (self.x + 6, self.y + 6, self.width, self.height),
                         border_radius=12)

        # Car body
        pygame.draw.rect(screen, RED,
                         (self.x, self.y, self.width, self.height),
                         border_radius=12)

        # Windshield
        pygame.draw.rect(screen, CYAN,
                         (self.x + 10, self.y + 18,
                          self.width - 20, 24),
                         border_radius=6)

        # Details
        pygame.draw.rect(screen, BLACK,
                         (self.x + 8, self.y + 60,
                          self.width - 16, 18),
                         border_radius=4)

        # Wheels
        pygame.draw.rect(screen, BLACK,
                         (self.x - 5, self.y + 12, 8, 24),
                         border_radius=4)
        pygame.draw.rect(screen, BLACK,
                         (self.x + self.width - 3, self.y + 12, 8, 24),
                         border_radius=4)

        pygame.draw.rect(screen, BLACK,
                         (self.x - 5, self.y + 64, 8, 24),
                         border_radius=4)
        pygame.draw.rect(screen, BLACK,
                         (self.x + self.width - 3, self.y + 64, 8, 24),
                         border_radius=4)

# ============================================================
# ENEMY CARS
# ============================================================

class EnemyCar:
    COLORS = [
        BLUE,
        YELLOW,
        ORANGE,
        (180, 0, 255),
        (0, 255, 140)
    ]

    def __init__(self, speed_bonus=0):
        self.width = 52
        self.height = random.randint(90, 110)

        lane_padding = 25

        self.x = random.randint(
            ROAD_X + lane_padding,
            ROAD_X + ROAD_WIDTH - self.width - lane_padding
        )

        self.y = -150

        self.speed = random.uniform(6, 12) + speed_bonus

        self.color = random.choice(self.COLORS)

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, player_speed):
        self.y += self.speed + player_speed * 0.45

    def draw(self):

        pygame.draw.rect(screen, (25, 25, 25),
                         (self.x + 5, self.y + 5,
                          self.width, self.height),
                         border_radius=10)

        pygame.draw.rect(screen, self.color,
                         (self.x, self.y,
                          self.width, self.height),
                         border_radius=10)

        pygame.draw.rect(screen, CYAN,
                         (self.x + 8, self.y + 16,
                          self.width - 16, 20),
                         border_radius=5)

        pygame.draw.rect(screen, BLACK,
                         (self.x + 6, self.y + 55,
                          self.width - 12, 15),
                         border_radius=4)

# ============================================================
# ROAD
# ============================================================

road_scroll = 0

def draw_background():
    screen.fill(GREEN)

    # Grass details
    for i in range(0, HEIGHT, 50):
        pygame.draw.circle(screen, (30, 130, 30),
                           (50, (i * 3 + road_scroll) % HEIGHT), 20)
        pygame.draw.circle(screen, (30, 130, 30),
                           (WIDTH - 50, (i * 2 + road_scroll) % HEIGHT), 20)

def draw_road(speed):
    global road_scroll

    road_scroll += speed * 1.5

    pygame.draw.rect(screen, DARK_GRAY,
                     (ROAD_X, 0, ROAD_WIDTH, HEIGHT))

    # Side borders
    pygame.draw.rect(screen, WHITE,
                     (ROAD_X, 0, 10, HEIGHT))

    pygame.draw.rect(screen, WHITE,
                     (ROAD_X + ROAD_WIDTH - 10, 0, 10, HEIGHT))

    # Lane lines
    lane_x = WIDTH // 2

    for y in range(-40, HEIGHT, 80):
        yy = y + (road_scroll % 80)

        pygame.draw.rect(screen, YELLOW,
                         (lane_x - 6, yy, 12, 45),
                         border_radius=4)

# ============================================================
# MAIN MENU
# ============================================================

def menu():
    blink = 0

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

        screen.fill((15, 15, 20))

        draw_text("RETRO RACER", font_big, RED,
                  WIDTH // 2, 180, center=True)

        draw_text("2D Arcade Racing", font_med, WHITE,
                  WIDTH // 2, 260, center=True)

        blink += 1

        if (blink // 30) % 2 == 0:
            draw_text("PRESS ENTER TO START",
                      font_med,
                      YELLOW,
                      WIDTH // 2,
                      420,
                      center=True)

        draw_text("Controls:", font_small, CYAN,
                  WIDTH // 2, 520, center=True)

        draw_text("Arrow Keys / WASD = Drive",
                  font_small, WHITE,
                  WIDTH // 2, 555, center=True)

        draw_text("SPACE = Boost",
                  font_small, WHITE,
                  WIDTH // 2, 585, center=True)

        draw_text("P = Pause",
                  font_small, WHITE,
                  WIDTH // 2, 615, center=True)

        pygame.display.flip()

# ============================================================
# GAME OVER
# ============================================================

def game_over_screen(score, best):
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

        screen.fill((10, 10, 10))

        draw_text("GAME OVER",
                  font_big,
                  RED,
                  WIDTH // 2,
                  220,
                  center=True)

        draw_text(f"SCORE: {score}",
                  font_med,
                  WHITE,
                  WIDTH // 2,
                  340,
                  center=True)

        draw_text(f"HIGH SCORE: {best}",
                  font_med,
                  YELLOW,
                  WIDTH // 2,
                  390,
                  center=True)

        draw_text("PRESS ENTER TO PLAY AGAIN",
                  font_small,
                  CYAN,
                  WIDTH // 2,
                  520,
                  center=True)

        pygame.display.flip()

# ============================================================
# GAME LOOP
# ============================================================

def game():
    global high_score

    player = Player()

    enemies = []
    particles = []

    enemy_timer = 0

    score = 0
    distance = 0

    paused = False

    running = True

    while running:
        dt = clock.tick(FPS)

        # ====================================================
        # EVENTS
        # ====================================================

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused

        keys = pygame.key.get_pressed()

        # ====================================================
        # PAUSE
        # ====================================================

        if paused:
            draw_text("PAUSED",
                      font_big,
                      WHITE,
                      WIDTH // 2,
                      HEIGHT // 2,
                      center=True)

            pygame.display.flip()
            continue

        # ====================================================
        # UPDATE
        # ====================================================

        player.update(keys)

        # Difficulty scaling
        difficulty = score / 1500

        # Spawn enemies
        enemy_timer += 1

        spawn_rate = max(18, int(42 - difficulty * 2))

        if enemy_timer >= spawn_rate:
            enemy_timer = 0
            enemies.append(EnemyCar(speed_bonus=difficulty * 0.5))

        # Update enemies
        for enemy in enemies[:]:
            enemy.update(player.speed)

            if enemy.y > HEIGHT + 120:
                enemies.remove(enemy)
                score += 100

            # Collision
            if player.rect().colliderect(enemy.rect()):

                # Explosion particles
                for _ in range(80):
                    particles.append(
                        Particle(
                            player.x + player.width // 2,
                            player.y + player.height // 2,
                            random.choice([RED, ORANGE, YELLOW])
                        )
                    )

                high_score = max(high_score, score)

                # Death animation
                for _ in range(90):

                    clock.tick(FPS)

                    draw_background()
                    draw_road(player.speed)

                    for p in particles:
                        p.update()
                        p.draw()

                    pygame.display.flip()

                return game_over_screen(score, high_score)

        # Update particles
        for p in particles[:]:
            p.update()

            if p.life <= 0:
                particles.remove(p)

        distance += player.speed
        score += int(player.speed * 0.6)

        # ====================================================
        # DRAW
        # ====================================================

        draw_background()
        draw_road(player.speed)

        # Road glow
        if player.boosting:
            glow = pygame.Surface((ROAD_WIDTH, HEIGHT), pygame.SRCALPHA)
            glow.fill((255, 120, 0, 30))
            screen.blit(glow, (ROAD_X, 0))

        # Draw enemies
        for enemy in enemies:
            enemy.draw()

        # Draw player
        player.draw()

        # Draw particles
        for p in particles:
            p.draw()

        # ====================================================
        # HUD
        # ====================================================

        pygame.draw.rect(screen, (0, 0, 0, 120),
                         (15, 15, 240, 140),
                         border_radius=10)

        draw_text(f"SCORE: {score}",
                  font_small,
                  WHITE,
                  25,
                  25)

        draw_text(f"HIGH: {high_score}",
                  font_small,
                  YELLOW,
                  25,
                  55)

        draw_text(f"SPEED: {int(player.speed * 18)}",
                  font_small,
                  CYAN,
                  25,
                  85)

        # Boost bar
        pygame.draw.rect(screen, WHITE,
                         (25, 120, 200, 18),
                         2,
                         border_radius=6)

        pygame.draw.rect(screen, ORANGE,
                         (27, 122, int(player.boost * 1.96), 14),
                         border_radius=5)

        draw_text("BOOST", font_small, WHITE, 235, 114)

        pygame.display.flip()

# ============================================================
# START
# ============================================================

while True:
    menu()
    game()