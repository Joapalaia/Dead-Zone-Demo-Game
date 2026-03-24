import pygame
import sys
import math
import random
import os


import os
os.environ['SDL_RENDER_SCALE_QUALITY'] = '0'
pygame.init()
pygame.mixer.init()
 
SCREEN_W, SCREEN_H = 800, 600
ZOOM    = 3.5
WORLD_W = int(SCREEN_W / ZOOM)
WORLD_H = int(SCREEN_H / ZOOM)
world_surface = pygame.Surface((WORLD_W, WORLD_H))
MAP_W, MAP_H = 2400, 2400
FPS = 60

WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
RED     = (220,  30,  30)
DARK_RED= (140,   0,   0)
GREEN   = ( 50, 180,  50)
DARK_GREEN=(30, 100,  30)
GRAY    = (120, 120, 120)
DARK_GRAY=(60,  60,  60)
YELLOW  = (255, 220,   0)
ORANGE  = (255, 140,   0)
BROWN   = (100,  60,  20)
LIGHT_BROWN=(160,100, 50)
BG_COLOR= ( 34,  85,  34)

screen        = pygame.display.set_mode((SCREEN_W, SCREEN_H))
world_surface = pygame.Surface((WORLD_W, WORLD_H))
pygame.display.set_caption("ZUMBIS MALDITOS")
clock         = pygame.time.Clock()


BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
SOUNDS_DIR  = os.path.join(ASSETS_DIR, "sounds")

def load_sound(name):
    path = os.path.join(SOUNDS_DIR, name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

snd_shoot = load_sound("shoot.mp3")
print("shoot carregado:", snd_shoot)
snd_zombie_walk = load_sound("zombie.mp3")
shoot_channel   = pygame.mixer.Channel(1)

def asset(*parts):
    return os.path.join(ASSETS_DIR, *parts)

def sprite(*parts):
    return os.path.join(SPRITES_DIR, *parts)


def make_placeholder(w, h, color, label=""):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill(color)
    if label:
        fnt = pygame.font.SysFont("Arial", max(8, h//3))
        txt = fnt.render(label, True, WHITE)
        surf.blit(txt, (2, h//2 - txt.get_height()//2))
    return surf


def load_sheet(path, frame_w, frame_h, count, fallback_color=(100,100,200)):
    frames = []
    if os.path.exists(path):
        sheet = pygame.image.load(path).convert_alpha()
        for i in range(count):
            frame = sheet.subsurface((i * frame_w, 0, frame_w, frame_h))
            frames.append(frame)
    else:
        for i in range(count):
            frames.append(make_placeholder(frame_w, frame_h, fallback_color))
    return frames

def load_image(path, fallback_color=(100,100,200), size=None):
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    w, h = size if size else (32, 32)
    return make_placeholder(w, h, fallback_color)



player_walk_frames = load_sheet(sprite("player.png"), 32, 32, 4, (50, 120, 200))


zombie_colors = [(0,140,0), (80,0,80), (180,80,0)]
zombie_walk_frames  = []
zombie_death_frames = []
for i, color in enumerate(zombie_colors):
    path = sprite(f"zombie{i+1}.png")
    frames = load_sheet(path, 32, 32, 4, color)
    zombie_walk_frames.append(frames)
    zombie_death_frames.append([])


weapon_img = load_image(sprite("weapon.png"), (180, 80, 0), (32, 16))


bullet_img = load_image(sprite("bullet.png"), YELLOW, (8, 8))


tree_img = load_image(sprite("tree.png"),  DARK_GREEN, (48, 48))
rock_img = load_image(sprite("rock.png"),  DARK_GRAY,  (40, 40))


map_img = load_image(sprite("map.png"), BG_COLOR, (MAP_W, MAP_H))


try:
    font_big   = pygame.font.SysFont("Impact", 72)
    font_med   = pygame.font.SysFont("Impact", 36)
    font_small = pygame.font.SysFont("Consolas", 22)
    font_tiny  = pygame.font.SysFont("Consolas", 16)
except:
    font_big   = pygame.font.SysFont(None, 72)
    font_med   = pygame.font.SysFont(None, 36)
    font_small = pygame.font.SysFont(None, 22)
    font_tiny  = pygame.font.SysFont(None, 16)


SCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

def load_high_score():
    try:
        with open(SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_high_score(score):
    try:
        with open(SCORE_FILE, "w") as f:
            f.write(str(score))
    except:
        pass





class Particle:
    def __init__(self, x, y, color):
        self.x  = x
        self.y  = y
        angle   = random.uniform(0, math.tau)
        speed   = random.uniform(1, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life    = random.randint(15, 35)
        self.max_life = self.life
        self.color   = color
        self.size    = random.randint(2, 5)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.life -= 1

    def draw(self, surface, cam_x, cam_y):
        alpha = int(255 * self.life / self.max_life)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if 0 <= sx <= SCREEN_W and 0 <= sy <= SCREEN_H:
            tmp = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*self.color, alpha), (self.size, self.size), self.size)
            surface.blit(tmp, (sx - self.size, sy - self.size))


class Bullet:
    SPEED = 12
    def __init__(self, x, y, angle):
        self.x     = x
        self.y     = y
        self.vx    = math.cos(angle) * self.SPEED
        self.vy    = math.sin(angle) * self.SPEED
        self.alive = True
        self.rect  = pygame.Rect(x-4, y-4, 8, 8)

    def update(self, obstacles):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (int(self.x), int(self.y))
        if not (0 <= self.x <= MAP_W and 0 <= self.y <= MAP_H):
            self.alive = False
        for obs in obstacles:
            if obs.rect.colliderect(self.rect):
                self.alive = False
                break

    def draw(self, surface, cam_x, cam_y):
        angle_deg = math.degrees(math.atan2(self.vy, self.vx))
        rotated   = pygame.transform.rotate(bullet_img, -angle_deg)
        sx = int(self.x - cam_x) - rotated.get_width()  // 2
        sy = int(self.y - cam_y) - rotated.get_height() // 2
        surface.blit(rotated, (sx, sy))


class Player:
    SPEED      = 3.5
    MAX_HP     = 10
    SHOOT_CD   = 15
    HIT_FLASH  = 30

    def __init__(self, x, y):
        self.x    = float(x)
        self.y    = float(y)
        self.hp   = self.MAX_HP
        self.rect = pygame.Rect(x-14, y-14, 28, 28)

        self.frame      = 0
        self.anim_timer = 0
        self.facing_left= False

        self.shoot_timer = 0
        self.hit_timer   = 0
        self.angle       = 0.0

    def handle_input(self, keys):
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1

        moving = dx != 0 or dy != 0
        if moving:
            length = math.hypot(dx, dy)
            dx /= length; dy /= length
            self.x = max(16, min(MAP_W-16, self.x + dx * self.SPEED))
            self.y = max(16, min(MAP_H-16, self.y + dy * self.SPEED))

            if dx < 0: self.facing_left = True
            if dx > 0: self.facing_left = False

            self.anim_timer += 1
            if self.anim_timer >= 8:
                self.anim_timer = 0
                self.frame = (self.frame + 1) % 4
        else:
            self.frame = 0

        self.rect.center = (int(self.x), int(self.y))
        if self.shoot_timer > 0: self.shoot_timer -= 1
        if self.hit_timer   > 0: self.hit_timer   -= 1

    def update_aim(self, cam_x, cam_y):
        mx, my = pygame.mouse.get_pos()

        world_mx = mx / ZOOM + cam_x
        world_my = my / ZOOM + cam_y
        self.angle = math.atan2(world_my - self.y, world_mx - self.x)
        if world_mx < self.x:
            self.facing_left = True
        else:
            self.facing_left = False

    def try_shoot(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.SHOOT_CD
            bx = self.x + math.cos(self.angle) * 20
            by = self.y + math.sin(self.angle) * 20
            if snd_shoot: shoot_channel.play(snd_shoot)
            return Bullet(bx, by, self.angle)
        return None

    def take_damage(self):
        if self.hit_timer == 0:
            self.hp -= 1
            self.hit_timer = self.HIT_FLASH

    def resolve_obstacle_collision(self, obstacles):
        for obs in obstacles:
            if obs.solid and self.rect.colliderect(obs.rect):

                dx = self.x - obs.rect.centerx
                dy = self.y - obs.rect.centery
                dist = math.hypot(dx, dy) or 1
                overlap = 20 + obs.push_radius - dist
                if overlap > 0:
                    self.x += (dx/dist) * overlap
                    self.y += (dy/dist) * overlap
                    self.rect.center = (int(self.x), int(self.y))

    def draw(self, surface, cam_x, cam_y):
        frame_surf = player_walk_frames[self.frame]
        if self.facing_left:
            frame_surf = pygame.transform.flip(frame_surf, True, False)
        sx = int(self.x - cam_x) - 16
        sy = int(self.y - cam_y) - 16


        if self.hit_timer > 0 and (self.hit_timer // 4) % 2 == 0:
            tinted = frame_surf.copy()
            tinted.fill((255, 80, 80, 0), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(tinted, (sx, sy))
        else:
            surface.blit(frame_surf, (sx, sy))


        if self.facing_left:
            w_img = pygame.transform.flip(weapon_img, True, False)
            draw_angle = 180 - math.degrees(self.angle)
        else:
            w_img = weapon_img
            draw_angle = -math.degrees(self.angle)

        weapon_rotated = pygame.transform.rotate(w_img, draw_angle)
        wx = int(self.x - cam_x) - weapon_rotated.get_width()  // 2
        wy = int(self.y - cam_y) - weapon_rotated.get_height() // 2
        surface.blit(weapon_rotated, (wx, wy))

    def draw_hud(self, surface, score, wave):

        bar_x, bar_y, bar_w, bar_h = 20, 20, 200, 22
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill = int(bar_w * self.hp / self.MAX_HP)
        pygame.draw.rect(surface, RED, (bar_x, bar_y, fill, bar_h), border_radius=4)
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)
        hp_txt = font_small.render(f"HP: {self.hp}/{self.MAX_HP}", True, WHITE)
        surface.blit(hp_txt, (bar_x + 6, bar_y + 2))


        sc_txt = font_med.render(f"{score:06d}", True, YELLOW)
        surface.blit(sc_txt, (SCREEN_W//2 - sc_txt.get_width()//2, 12))


        wv_txt = font_small.render(f"WAVE {wave}", True, ORANGE)
        surface.blit(wv_txt, (SCREEN_W - wv_txt.get_width() - 20, 20))


class Zombie:
    BASE_SPEED  = 1.2
    DEATH_FRAMES_COUNT = 4
    HIT_FLASH = 6

    def __init__(self, x, y, ztype=0, wave=1):
        self.x      = float(x)
        self.y      = float(y)
        self.ztype  = ztype % 3
        self.speed  = self.BASE_SPEED + wave * 0.08 + random.uniform(-0.1, 0.2)
        self.hp     = 1 + ztype + (wave // 3)
        self.max_hp = self.hp
        self.alive  = True
        self.dying  = False
        self.rect   = pygame.Rect(x-14, y-14, 28, 28)

        self.frame      = 0
        self.anim_timer = 0
        self.facing_left= False

        self.death_frame  = 0
        self.death_timer  = 0
        self.done         = False

    def update(self, player, obstacles):
        if self.dying:
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.done = True
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy) or 1
        nx, ny = dx/dist, dy/dist

        self.x += nx * self.speed
        self.y += ny * self.speed

        if nx < 0: self.facing_left = True
        if nx > 0: self.facing_left = False

        self.rect.center = (int(self.x), int(self.y))


        for obs in obstacles:
            if obs.solid and self.rect.colliderect(obs.rect):
                ox = self.x - obs.rect.centerx
                oy = self.y - obs.rect.centery
                od = math.hypot(ox, oy) or 1
                overlap = 20 + obs.push_radius - od
                if overlap > 0:
                    self.x += (ox/od) * overlap
                    self.y += (oy/od) * overlap
                    self.rect.center = (int(self.x), int(self.y))

        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % 4

    def hit(self, particles):
        self.hp -= 1
        for _ in range(8):
            particles.append(Particle(self.x, self.y, (180, 0, 0)))
        if self.hp <= 0:
            self.dying = True
            self.alive = False
            self.death_timer = self.HIT_FLASH
            return True
        return False

    def draw(self, surface, cam_x, cam_y):
        frames = zombie_walk_frames[self.ztype]
        frame_surf = frames[self.frame]

        if self.facing_left:
            frame_surf = pygame.transform.flip(frame_surf, True, False)

        sx = int(self.x - cam_x) - 16
        sy = int(self.y - cam_y) - 16

        if self.dying:

            if (self.death_timer // 2) % 2 == 0:
                tinted = frame_surf.copy()
                tinted.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)
                surface.blit(tinted, (sx, sy))
            else:
                surface.blit(frame_surf, (sx, sy))
            return

        surface.blit(frame_surf, (sx, sy))


        if self.max_hp > 1:
            bw = 28
            bh = 4
            fill = int(bw * self.hp / self.max_hp)
            pygame.draw.rect(surface, DARK_RED, (sx+2, sy-8, bw, bh))
            pygame.draw.rect(surface, RED,      (sx+2, sy-8, fill, bh))


class Obstacle:
    def __init__(self, x, y, otype="tree"):
        self.x     = x
        self.y     = y
        self.otype = otype
        self.solid = True
        if otype == "tree":
            self.img         = tree_img
            self.push_radius = 20
            self.rect        = pygame.Rect(x-16, y-16, 32, 32)
        else:
            self.img         = rock_img
            self.push_radius = 18
            self.rect        = pygame.Rect(x-16, y-16, 32, 32)

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x) - self.img.get_width()  // 2
        sy = int(self.y - cam_y) - self.img.get_height() // 2
        if -64 <= sx <= SCREEN_W+64 and -64 <= sy <= SCREEN_H+64:
            surface.blit(self.img, (sx, sy))






class WaveManager:
    SPAWN_MARGIN = 80

    def __init__(self):
        self.wave          = 1
        self.zombies_left  = 0
        self.spawn_queue   = []
        self.spawn_timer   = 0
        self.spawn_delay   = 40
        self.between_timer = 0
        self.between_delay = FPS * 3
        self.wave_started  = False
        self._prepare_wave()

    def _prepare_wave(self):
        count = 5 + self.wave * 3
        self.spawn_queue  = []
        for _ in range(count):
            ztype = random.choices([0,1,2], weights=[5,3,2])[0]
            self.spawn_queue.append(ztype)
        self.zombies_left = count
        self.wave_started = True

    def _random_spawn_pos(self, cam_x, cam_y):
        side = random.randint(0, 3)
        if side == 0:
            x = random.randint(0, MAP_W)
            y = cam_y - self.SPAWN_MARGIN
        elif side == 1:
            x = random.randint(0, MAP_W)
            y = cam_y + SCREEN_H + self.SPAWN_MARGIN
        elif side == 2:
            x = cam_x - self.SPAWN_MARGIN
            y = random.randint(0, MAP_H)
        else:
            x = cam_x + WORLD_W + self.SPAWN_MARGIN
            y = random.randint(0, MAP_H)
        x = max(0, min(MAP_W, x))
        y = max(0, min(MAP_H, y))
        return x, y

    def update(self, zombies, cam_x, cam_y):
        """Returns True if a new wave banner should be shown."""
        show_banner = False

        if self.spawn_queue:
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_delay:
                self.spawn_timer = 0
                ztype = self.spawn_queue.pop(0)
                sx, sy = self._random_spawn_pos(cam_x, cam_y)
                zombies.append(Zombie(sx, sy, ztype, self.wave))

        alive_count = sum(1 for z in zombies if not z.done)

        if not self.spawn_queue and alive_count == 0:
            if self.between_timer == 0:
                self.between_timer = self.between_delay
            self.between_timer -= 1
            if self.between_timer <= 0:
                self.between_timer = 0
                self.wave += 1
                self._prepare_wave()
                show_banner = True

        return show_banner

    @property
    def is_between_waves(self):
        return self.between_timer > 0

    @property
    def between_pct(self):
        return self.between_timer / self.between_delay






def generate_obstacles():
    obstacles = []
    margin    = 80
    center_clear = 200

    def is_clear(x, y):
        cx, cy = MAP_W//2, MAP_H//2
        if math.hypot(x-cx, y-cy) < center_clear:
            return False
        for o in obstacles:
            if math.hypot(x-o.x, y-o.y) < 60:
                return False
        return True

    for _ in range(120):
        for attempt in range(20):
            x = random.randint(margin, MAP_W-margin)
            y = random.randint(margin, MAP_H-margin)
            if is_clear(x, y):
                otype = random.choice(["tree"]*3 + ["rock"])
                obstacles.append(Obstacle(x, y, otype))
                break

    return obstacles






def draw_menu(surface, high_score, selected):

    surface.fill((10, 10, 20))


    for y in range(0, SCREEN_H, 4):
        pygame.draw.line(surface, (0,0,0,30), (0,y), (SCREEN_W,y))


    title = font_big.render("ZUMBIS MALDITOS", True, RED)
    shadow= font_big.render("ZUMBIS MALDITOS", True, DARK_RED)
    tx = SCREEN_W//2 - title.get_width()//2
    surface.blit(shadow, (tx+4, 84))
    surface.blit(title,  (tx,   80))

    subtitle = font_small.render("demo gamer para o trab da uninter", True, GRAY)
    surface.blit(subtitle, (SCREEN_W//2 - subtitle.get_width()//2, 158))


    items = ["PLAY", "QUIT"]
    for i, item in enumerate(items):
        color = YELLOW if i == selected else WHITE
        txt   = font_med.render(item, True, color)
        x     = SCREEN_W//2 - txt.get_width()//2
        y     = 230 + i * 60
        if i == selected:
            pygame.draw.rect(surface, DARK_RED, (x-16, y-6, txt.get_width()+32, txt.get_height()+10), border_radius=4)
        surface.blit(txt, (x, y))


    hs_txt = font_small.render(f"RECORD: {high_score:06d}", True, ORANGE)
    surface.blit(hs_txt, (SCREEN_W//2 - hs_txt.get_width()//2, 370))


    ctrl_rect = pygame.Rect(SCREEN_W//2 - 180, 430, 360, 130)
    pygame.draw.rect(surface, (20,20,30), ctrl_rect, border_radius=8)
    pygame.draw.rect(surface, DARK_GRAY,  ctrl_rect, 2, border_radius=8)

    ctrl_title = font_tiny.render("── CONTROLES ──", True, GRAY)
    surface.blit(ctrl_title, (SCREEN_W//2 - ctrl_title.get_width()//2, 442))

    controls = [
        ("W A S D", "Mover personagem"),
        ("MOUSE",   "Mirar"),
        ("CLICK",   "Atirar"),
        ("ESC",     "Voltar ao menu"),
    ]
    for j, (key, action) in enumerate(controls):
        k_txt = font_tiny.render(key,    True, YELLOW)
        a_txt = font_tiny.render(action, True, WHITE)
        row_y = 466 + j * 22
        surface.blit(k_txt, (ctrl_rect.x + 20,  row_y))
        surface.blit(a_txt, (ctrl_rect.x + 130, row_y))


def draw_game_over(surface, score, high_score, new_record):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0,0,0,180))
    surface.blit(overlay, (0,0))

    go_txt = font_big.render("VOCÊ MORREU", True, RED)
    surface.blit(go_txt, (SCREEN_W//2 - go_txt.get_width()//2, 160))

    sc_txt = font_med.render(f"PONTUAÇÃO: {score:06d}", True, WHITE)
    surface.blit(sc_txt, (SCREEN_W//2 - sc_txt.get_width()//2, 270))

    if new_record:
        nr_txt = font_med.render("NOVO RECORDE!", True, YELLOW)
        surface.blit(nr_txt, (SCREEN_W//2 - nr_txt.get_width()//2, 320))

    hs_txt = font_small.render(f"RECORDE: {high_score:06d}", True, ORANGE)
    surface.blit(hs_txt, (SCREEN_W//2 - hs_txt.get_width()//2, 370))

    cont = font_small.render("Pressione ENTER para continuar", True, GRAY)
    surface.blit(cont, (SCREEN_W//2 - cont.get_width()//2, 430))


def draw_wave_banner(surface, wave, alpha):
    txt = font_big.render(f"WAVE {wave}", True, ORANGE)
    tmp = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
    tmp.blit(txt, (0,0))
    tmp.set_alpha(int(alpha * 255))
    surface.blit(tmp, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - txt.get_height()//2))






STATE_MENU      = "menu"
STATE_PLAYING   = "playing"
STATE_GAME_OVER = "gameover"

def new_game():
    player    = Player(MAP_W//2, MAP_H//2)
    obstacles = generate_obstacles()
    zombies   = []
    bullets   = []
    particles = []
    wave_mgr  = WaveManager()
    score     = 0
    return player, obstacles, zombies, bullets, particles, wave_mgr, score






def main():
    high_score = load_high_score()
    state      = STATE_MENU
    menu_sel   = 0

    player = obstacles = zombies = bullets = particles = wave_mgr = score = None


    banner_timer = 0
    BANNER_DURATION = FPS * 2
    new_record = False

    while True:
        dt = clock.tick(FPS)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if state == STATE_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        menu_sel = (menu_sel - 1) % 2
                    if event.key in (pygame.K_s, pygame.K_DOWN):
                        menu_sel = (menu_sel + 1) % 2
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if menu_sel == 0:
                            state = STATE_PLAYING
                            player, obstacles, zombies, bullets, particles, wave_mgr, score = new_game()
                            banner_timer = BANNER_DURATION
                        else:
                            pygame.quit(); sys.exit()

            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if snd_zombie_walk: snd_zombie_walk.stop()
                        state = STATE_MENU
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    bullet = player.try_shoot()
                    if bullet:
                        bullets.append(bullet)

            elif state == STATE_GAME_OVER:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    state = STATE_MENU


        if state == STATE_PLAYING:
            keys = pygame.key.get_pressed()


            if pygame.mouse.get_pressed()[0]:
                bullet = player.try_shoot()
                if bullet:
                    bullets.append(bullet)

            cam_x = int(player.x - WORLD_W//2)
            cam_y = int(player.y - WORLD_H//2)

            player.handle_input(keys)
            player.update_aim(cam_x, cam_y)
            player.resolve_obstacle_collision(obstacles)


            for b in bullets:
                b.update(obstacles)
            bullets = [b for b in bullets if b.alive]


            for z in zombies:
                z.update(player, obstacles)


            for b in bullets[:]:
                for z in zombies:
                    if z.alive and b.alive and b.rect.colliderect(z.rect):
                        b.alive = False
                        killed = z.hit(particles)
                        if killed:
                            score += 10 * (z.ztype + 1)
                        break


            alive_zombies = any(z.alive for z in zombies)
            if alive_zombies:
                if snd_zombie_walk and not pygame.mixer.get_busy():
                    snd_zombie_walk.play(-1)
            else:
                if snd_zombie_walk:
                    snd_zombie_walk.stop()

            for z in zombies:
                if z.alive and player.rect.colliderect(z.rect):
                    player.take_damage()

            for p in particles:
                p.update()
            particles = [p for p in particles if p.life > 0]


            zombies = [z for z in zombies if not z.done]


            show_banner = wave_mgr.update(zombies, cam_x, cam_y)
            if show_banner:
                banner_timer = BANNER_DURATION

            if banner_timer > 0:
                banner_timer -= 1


            if player.hp <= 0:
                new_record = score > high_score
                if new_record:
                    high_score = score
                    save_high_score(high_score)
                if snd_zombie_walk: snd_zombie_walk.stop()
                state = STATE_GAME_OVER


        if state == STATE_MENU:
            draw_menu(screen, high_score, menu_sel)

        elif state == STATE_PLAYING:
            cam_x = int(player.x - WORLD_W//2)
            cam_y = int(player.y - WORLD_H//2)


            world_surface.blit(map_img, (-cam_x, -cam_y))


            for obs in obstacles:
                obs.draw(world_surface, cam_x, cam_y)


            for p in particles:
                p.draw(world_surface, cam_x, cam_y)


            for z in zombies:
                z.draw(world_surface, cam_x, cam_y)


            for b in bullets:
                b.draw(world_surface, cam_x, cam_y)


            player.draw(world_surface, cam_x, cam_y)


            pygame.transform.scale(world_surface, (SCREEN_W, SCREEN_H), screen)


            player.draw_hud(screen, score, wave_mgr.wave)


            if banner_timer > 0:
                alpha = min(1.0, banner_timer / (FPS * 0.5))
                if banner_timer < FPS * 0.5:
                    alpha = banner_timer / (FPS * 0.5)
                draw_wave_banner(screen, wave_mgr.wave, alpha)


            if wave_mgr.is_between_waves:
                msg = font_small.render(
                    f"Próxima wave em {int(wave_mgr.between_timer / FPS) + 1}s...",
                    True, WHITE
                )
                pygame.transform.scale(world_surface, (SCREEN_W, SCREEN_H), screen)

        elif state == STATE_GAME_OVER:

            draw_game_over(screen, score, high_score, new_record)

        pygame.display.flip()


if __name__ == "__main__":
    main()
