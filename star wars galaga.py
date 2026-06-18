import pygame, sys, random, math

# --- INITIALIZATION ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Star Wars Shooter Ultra: Death Star Edition")
clock = pygame.time.Clock()

# --- GLOBALS ---
screen_shake_timer = 0
shake_intensity = 0
hyperspace_timer = 0

# --- COLORS ---
WHITE, RED, CYAN = (255, 255, 255), (255, 50, 50), (0, 255, 255)
ORANGE, GREEN, BLUE = (255, 165, 0), (0, 255, 0), (50, 150, 255)
PURPLE, DARK_BLUE, YELLOW = (180, 0, 255), (5, 5, 20), (255, 255, 0)
GRAY, DARK_GRAY = (100, 100, 110), (50, 50, 60)
LIGHT_GRAY = (180,180,190)
BLACK = (0, 0, 0)

# --- FONTS ---
FONT = pygame.font.Font(None, 36)
BIG_FONT = pygame.font.Font(None, 72)

# --- GROUPS ---
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
bosses = pygame.sprite.Group()
particles = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# --- BACKGROUND ASSETS ---
stars = [[[random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 2)] for _ in range(70)] for _ in range(3)]
nebulae = [[random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(50, 120), random.randint(50, 120), (random.randint(50, 100), 0, random.randint(50, 100), 50)] for _ in range(8)]

def draw_background(surface, offset=(0,0)):
    surface.fill(DARK_BLUE)
    for i, layer in enumerate(stars):
        speed = 0.3 * (i + 1)
        for star in layer:
            pygame.draw.circle(surface, WHITE, (int(star[0] + offset[0]), int(star[1] + offset[1])), star[2])
            star[1] += speed
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)
    for neb in nebulae:
        s = pygame.Surface((neb[2], neb[3]), pygame.SRCALPHA)
        pygame.draw.ellipse(s, neb[4], (0, 0, neb[2], neb[3]))
        surface.blit(s, (neb[0] + offset[0], neb[1] + offset[1]))
        neb[1] += 0.1
        if neb[1] > SCREEN_HEIGHT:
            neb[1] = -neb[3]
            neb[0] = random.randint(0, SCREEN_WIDTH)

def draw_hyperspace(surface):
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    for _ in range(25):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.randint(20, 450)
        stretch = (40 - hyperspace_timer) * 8
        x1 = cx + math.cos(angle) * dist
        y1 = cy + math.sin(angle) * dist
        x2 = cx + math.cos(angle) * (dist + stretch)
        y2 = cy + math.sin(angle) * (dist + stretch)
        pygame.draw.line(surface, WHITE, (x1, y1), (x2, y2), 2)

# --- UTILITY CLASSES ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, dx, dy, life, size=3):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx, self.dy, self.life = dx, dy, life
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.life -= 1
        if self.life <= 0: self.kill()

class AbsorbRing(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.radius = 5
        self.max_radius = 30
        self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.image.fill((0, 0, 0, 0))
        self.radius += 3
        alpha = max(0, 255 - self.radius * 8)

        pygame.draw.circle(
            self.image,
            (50, 150, 255, alpha),
            (40, 40),
            self.radius,
            3
        )

        if self.radius >= self.max_radius:
            self.kill()


def spawn_particles(x, y, color, amount=10):
    for _ in range(amount):
        p = Particle(x, y, color, random.uniform(-2, 2), random.uniform(-2, 2), random.randint(10, 25))
        particles.add(p); all_sprites.add(p)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type_):
        super().__init__()
        self.type = type_
        self.angle = random.uniform(0, 360)
        self.spin = random.choice([-1, 1]) * random.uniform(1.5, 3)
        self.pulse = random.uniform(0, math.pi * 2)
        self.hover = random.uniform(0, math.pi * 2)

        self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.base_y = y

    def update(self):
        self.rect.y += 1.5
        self.angle += self.spin
        self.pulse += 0.12
        self.hover += 0.08

        # Subtle hover wobble
        self.rect.centerx += int(math.sin(self.hover) * 0.3)

        self.image.fill((0, 0, 0, 0))
        cx, cy = 24, 24
        glow = int((math.sin(self.pulse) + 1) * 4)

        # ======================
        # DOUBLE SHOT – KYBER CORE
        # ======================
        if self.type == "double":
            # Outer hologram ring
            pygame.draw.circle(self.image, (0, 140, 255, 90), (cx, cy), 18 + glow, 2)

            # Rotating brackets
            for a in range(0, 360, 90):
                rad = math.radians(a + self.angle)
                x1 = cx + math.cos(rad) * 14
                y1 = cy + math.sin(rad) * 14
                x2 = cx + math.cos(rad) * 20
                y2 = cy + math.sin(rad) * 20
                pygame.draw.line(self.image, CYAN, (x1, y1), (x2, y2), 3)

            # Kyber crystal core
            pygame.draw.circle(self.image, (0, 200, 255), (cx, cy), 7 + glow)
            pygame.draw.circle(self.image, WHITE, (cx, cy), 7 + glow, 2)

        # ======================
        # SPREAD SHOT – BLASTER FAN
        # ======================
        elif self.type == "spread":
            # Arc cone
            for i, angle in enumerate([-25, 0, 25]):
                rad = math.radians(angle)
                pygame.draw.line(
                    self.image,
                    ORANGE,
                    (cx, cy),
                    (cx + math.sin(rad) * 20, cy - math.cos(rad) * 20),
                    4
                )

            # Energy ring
            pygame.draw.circle(self.image, (255, 180, 80, 120), (cx, cy), 18, 2)

            # Core emitter
            pygame.draw.circle(self.image, WHITE, (cx, cy), 4)

        # ======================
        # SPEED – HYPERSPACE DRIVE
        # ======================
        elif self.type == "speed":
            # Stacked hyperspace arrows
            for i in range(4):
                off = i * 6 - 9
                pygame.draw.polygon(
                    self.image,
                    (0, 255, 120),
                    [
                        (cx - 7, cy + off),
                        (cx + 7, cy + off),
                        (cx, cy + off - 7),
                    ],
                )

            # Warp ring
            pygame.draw.circle(self.image, (0, 255, 150, 100), (cx, cy), 20, 2)

        # ======================
        # LIFE ORB – FORCE ENERGY
        # ======================
        elif self.type == "shield":
            radius = 10 + glow

            # Force field aura
            pygame.draw.circle(self.image, (50, 150, 255, 90), (cx, cy), radius + 8)
            pygame.draw.circle(self.image, BLUE, (cx, cy), radius)
            pygame.draw.circle(self.image, WHITE, (cx, cy), radius, 2)

            # Plus symbol
            pygame.draw.line(self.image, WHITE, (cx, cy - 6), (cx, cy + 6), 2)
            pygame.draw.line(self.image, WHITE, (cx - 6, cy), (cx + 6, cy), 2)

        # Cleanup
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# --- PLAYER CLASS ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pygame.Rect(SCREEN_WIDTH//2, SCREEN_HEIGHT-60, 40, 40)
        self.speed = 5
        self.double_shot = False
        self.spread_shot = False
        self.shield = False
        self.shield_timer = 0
        self.speed_timer = 0
        
        # --- NEW ANIMATION VARIABLES ---
        self.tilt = 0          # Target tilt for banking left/right
        self.current_tilt = 0  # Smoothed tilt for drawing
        self.recoil = 0        # Push back when shooting
        self.thruster_frame = 0 # For flickering engine

    def update(self):
        keys = pygame.key.get_pressed()
        curr_speed = self.speed * 1.5 if self.speed_timer > 0 else self.speed
        
        # Reset tilt target
        self.tilt = 0
        
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]): 
            self.rect.x -= curr_speed
            self.tilt = 15 # Tilt left
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]): 
            self.rect.x += curr_speed
            self.tilt = -15 # Tilt right
            
        # Smoothly interpolate tilt (Ease-in/out)
        self.current_tilt += (self.tilt - self.current_tilt) * 0.1
        
        # Smoothly recover from recoil
        if self.recoil > 0: self.recoil -= 1
        
        self.rect.x = max(0, min(SCREEN_WIDTH-40, self.rect.x))
        if self.shield:
            self.shield_timer -= 1
            if self.shield_timer <= 0: self.shield = False
            
        self.thruster_frame += 1

    def shoot(self):
        # Trigger recoil animation
        self.recoil = 5
        
        if self.double_shot:
            player_bullets.add(PlayerBullet(self.rect.left, self.rect.top), PlayerBullet(self.rect.right, self.rect.top))
        elif self.spread_shot:
            player_bullets.add(PlayerBullet(self.rect.centerx, self.rect.top, -3), PlayerBullet(self.rect.centerx, self.rect.top, 0), PlayerBullet(self.rect.centerx, self.rect.top, 3))
        else:
            player_bullets.add(PlayerBullet(self.rect.centerx, self.rect.top))
        all_sprites.add(player_bullets)

    def draw_ship(self, surface, offset=(0,0)):
        # Apply recoil and shake offset
        ox, oy = offset[0], offset[1] + self.recoil
        cx, cy = self.rect.centerx + ox, self.rect.centery + oy
        
        # Wing spread based on current_tilt
        wing_w = 20
        wing_h = 15 + (abs(self.current_tilt) * 0.2) # Wings "flex" when turning

        # 1. ENGINE FLAME (Animated)
        flicker = random.randint(0, 5) if self.thruster_frame % 2 == 0 else 0
        for side in [-1, 1]:
            pygame.draw.ellipse(surface, CYAN, (cx + (side*12) - 3, cy + 10, 6, 10 + flicker))
            pygame.draw.ellipse(surface, WHITE, (cx + (side*12) - 1, cy + 12, 2, 5 + flicker))

        # 2. X-WING WINGS (Drawing with tilt)
        t_off = self.current_tilt
        # Top Wings
        pygame.draw.line(surface, LIGHT_GRAY, (cx, cy), (cx - wing_w, cy - wing_h + t_off), 4)
        pygame.draw.line(surface, LIGHT_GRAY, (cx, cy), (cx + wing_w, cy - wing_h - t_off), 4)
        # Bottom Wings
        pygame.draw.line(surface, LIGHT_GRAY, (cx, cy), (cx - wing_w, cy + wing_h + t_off), 4)
        pygame.draw.line(surface, LIGHT_GRAY, (cx, cy), (cx + wing_w, cy + wing_h - t_off), 4)

        # 3. BODY (Fuselage)
        hull_pts = [(cx, cy-20), (cx-7, cy+10), (cx+7, cy+10)]
        pygame.draw.polygon(surface, WHITE, hull_pts)
        pygame.draw.polygon(surface, GRAY, hull_pts, 2)

        # 4. COCKPIT GLOW
        # We use 200 as a base so that adding 'glow' doesn't exceed 255
        glow = abs(int(math.sin(pygame.time.get_ticks() * 0.005) * 55)) 
        pygame.draw.circle(surface, (50, 150, 200 + glow), (cx, cy-5), 4)
        
    def reset_position(self):
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 60
        self.current_tilt = 0

class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx=0):
        super().__init__()
        self.image = pygame.Surface((6, 12))
        self.image.fill(CYAN)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx, self.dy = dx, -12
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.bottom < 0: self.kill()
        spawn_particles(self.rect.centerx, self.rect.centery, CYAN, 1)

# --- ENEMY CLASSES ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.speed = random.randint(1, 3)
        self.time_offset = random.random() * 10
    def update(self):
        self.rect.y += self.speed
        self.rect.x = self.start_x + math.sin(self.rect.y * 0.05 + self.time_offset) * 30
        if self.rect.top > SCREEN_HEIGHT: self.kill()
        if random.randint(0, 150) == 0: self.shoot()
    def draw_ship(self, surface, offset=(0,0)):
        cx, cy = self.rect.centerx + offset[0], self.rect.centery + offset[1]
        
        # Calculate a slight tilt based on the sine-wave movement
        # This makes the ship look like it's banking
        tilt = math.cos(self.rect.y * 0.05 + self.time_offset) * 10
        
        # 1. WING CONNECTORS (The horizontal bars)
        pygame.draw.line(surface, GRAY, (cx - 15, cy), (cx + 15, cy), 4)
        
        # 2. SOLAR WINGS (Hexagonal side panels)
        # We draw these as narrow vertical rectangles with a border
        for side in [-1, 1]:
            wx = cx + (side * 18)
            # Main wing panel
            wing_rect = pygame.Rect(wx - 2, cy - 15 + tilt, 5, 30)
            pygame.draw.rect(surface, (20, 20, 25), wing_rect) # Dark solar panel
            pygame.draw.rect(surface, LIGHT_GRAY, wing_rect, 1) # Metal frame
            
            # Wing structural details (Top and bottom caps)
            pygame.draw.line(surface, LIGHT_GRAY, (wx - 4, cy - 15 + tilt), (wx + 4, cy - 15 + tilt), 2)
            pygame.draw.line(surface, LIGHT_GRAY, (wx - 4, cy + 15 + tilt), (wx + 4, cy + 15 + tilt), 2)

        # 3. COCKPIT SPHERE
        pygame.draw.circle(surface, GRAY, (cx, cy), 8)
        pygame.draw.circle(surface, DARK_GRAY, (cx, cy), 8, 2) # Outline
        
        # 4. VIEWPORT (The "web" pattern on the front)
        # Central dot
        pygame.draw.circle(surface, (30, 30, 40), (cx, cy), 4)
        # Spoke lines for the window frame
        for i in range(4):
            angle = i * (math.pi / 2)
            ex = cx + math.cos(angle) * 7
            ey = cy + math.sin(angle) * 7
            pygame.draw.line(surface, DARK_GRAY, (cx, cy), (ex, ey), 1)

        # 5. ION ENGINES (Two small red dots on the back)
        pygame.draw.circle(surface, RED, (cx - 3, cy + 4), 2)
        pygame.draw.circle(surface, RED, (cx + 3, cy + 4), 2)
    def shoot(self):
        b = EnemyBullet(self.rect.centerx, self.rect.bottom)
        enemy_bullets.add(b); all_sprites.add(b)

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx=0, dy=6):
        super().__init__()
        self.image = pygame.Surface((6, 12))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx, self.dy = dx, dy
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0: self.kill()

class ExplosionEffect(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frame = 0
        self.max_frames = 25 
        # Large surface to accommodate the expanding fireball
        self.image = pygame.Surface((120, 120), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.image.fill((0, 0, 0, 0)) # Clear frame
        self.frame += 1
        
        # Calculate size and transparency based on frame
        # Growth starts fast, then slows
        radius = self.frame * 2.5 
        alpha = max(0, 255 - (self.frame * 10)) 
        
        # Color shifting: White -> Yellow -> Orange -> Red
        if self.frame < 6:
            color = (255, 255, 255) # Flash
        elif self.frame < 12:
            color = (255, 255, 100) # Bright Yellow
        elif self.frame < 18:
            color = (255, 150, 50)  # Orange
        else:
            color = (150, 20, 0)    # Deep Red/Smoke

        # Draw the main animated sphere
        pygame.draw.circle(self.image, (*color, alpha), (60, 60), radius)
        
        # Add a secondary "inner glow" layer for depth
        if alpha > 100:
            pygame.draw.circle(self.image, (255, 255, 255, alpha//2), (60, 60), radius * 0.6)

        if self.frame >= self.max_frames:
            self.kill()

class TIEBomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Small, dangerous-looking cylindrical bomb
        self.image = pygame.Surface((8, 12), pygame.SRCALPHA)
        pygame.draw.rect(self.image, DARK_GRAY, (0, 0, 8, 12), border_radius=2)
        pygame.draw.rect(self.image, RED, (2, 2, 4, 2)) # Small glowing "armed" light
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3.5
        self.timer = 0

    def update(self):
        self.rect.y += self.speed
        self.timer += 1
        # Explodes after a short distance or if shot
        if self.timer >= 60 or self.rect.y > SCREEN_HEIGHT - 100:
            self.explode()

    def explode(self):
            # 1. THE CENTRAL FLASH (White-hot core)
            # We spawn a few large, fast-fading white particles for the initial "pop"
            for _ in range(5):
                flash = Particle(self.rect.centerx, self.rect.centery, WHITE, 
                                 random.uniform(-2, 2), random.uniform(-2, 2), 15)
                particles.add(flash); all_sprites.add(flash)

            # 2. PLASMA SHOCKWAVE (Expanding Ring)
            # We create a ring that starts bright cyan/white and fades to deep blue
            shockwave = AbsorbRing(self.rect.centerx, self.rect.centery)
            shockwave.color = (0, 255, 255) # Ion Blue
            shockwave.max_radius = 50       # How far the shockwave travels
            particles.add(shockwave); all_sprites.add(shockwave)

            # 3. TACTICAL SHARDS (The dangerous part)
            # These are the "yellow shards" you wanted, glowing and lethal
            for angle in range(30, 360, 60): # 6 directional shards
                rad = math.radians(angle)
                shard = EnemyBullet(self.rect.centerx, self.rect.centery, math.cos(rad)*5, math.sin(rad)*5)
                
                # Make the shard look like a glowing energy fragment
                shard.image = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(shard.image, YELLOW, (3, 3), 3)
                pygame.draw.circle(shard.image, WHITE, (3, 3), 1) # Hot center
                
                enemy_bullets.add(shard); all_sprites.add(shard)
                
            # 4. LINGERING EMBERS (Visual flair)
            # Small orange/yellow sparks that drift away slowly
            for _ in range(12):
                p_color = random.choice([YELLOW, ORANGE, (255, 50, 0)])
                p = Particle(self.rect.centerx, self.rect.centery, p_color, 
                             random.uniform(-4, 4), random.uniform(-4, 4), 30)
                particles.add(p); all_sprites.add(p)

            # 5. HIT DETECTION (Fair 40px radius)
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            if dist < 40:
                global player_lives
                player_lives -= 1
                player.reset_position()
                
            self.kill()

class TIEBomber(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 1.1
        self.bomb_timer = 0
        
    def draw_ship(self, surface, offset=(0,0)):
            cx, cy = self.rect.centerx + offset[0], self.rect.centery + offset[1]
            
            # 1. THE DUAL HULL (Max Detail)
            # Pilot Pod (Left)
            pygame.draw.circle(surface, GRAY, (cx - 8, cy), 8)
            pygame.draw.circle(surface, DARK_GRAY, (cx - 8, cy), 8, 1) 
            pygame.draw.circle(surface, RED, (cx - 8, cy - 2), 4) # Red Window
            # Add "Targeting Eye" sensor above window
            pygame.draw.rect(surface, (50, 50, 60), (cx - 11, cy - 7, 3, 2))
            # Internal window struts
            pygame.draw.line(surface, BLACK, (cx - 10, cy - 4), (cx - 6, cy), 1)
            pygame.draw.line(surface, BLACK, (cx - 6, cy - 4), (cx - 10, cy), 1)
            
            # Ordnance Pod (Right)
            pygame.draw.circle(surface, GRAY, (cx + 8, cy), 8)
            pygame.draw.rect(surface, DARK_GRAY, (cx + 5, cy - 3, 6, 6), border_radius=1) # Hatch
            pygame.draw.circle(surface, BLACK, (cx + 8, cy + 2), 3) # Bomb Chute
            # Technical "Ribbing" (Slats) on the side of the pod
            for i in range(-3, 4, 2):
                pygame.draw.line(surface, (50, 50, 55), (cx + 12, cy + i), (cx + 15, cy + i), 1)
                
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.circle(surface, YELLOW, (cx + 5, cy - 4), 1) # Blink

            # Neck with "Power Cables"
            pygame.draw.rect(surface, DARK_GRAY, (cx - 3, cy - 1, 6, 3))
            pygame.draw.line(surface, BLACK, (cx - 3, cy), (cx + 3, cy), 1)

            # 2. THE WINGS (Angled Hexagonal "C" Bend)
            for side in [-1, 1]:
                x_outer = cx + (side * 30)      # Spine of the wing
                x_mid = cx + (side * 28)        # Notched corner
                x_inner_tip = cx + (side * 16)  # Tip pointing inward
                
                # Struts with mechanical "joints"
                pygame.draw.line(surface, GRAY, (cx + (side * 10), cy), (x_outer, cy), 3)
                pygame.draw.circle(surface, DARK_GRAY, (x_outer, cy), 3)
                
                # The Wing Panels: Using 5 points per panel to get the hexagonal "notched" look
                # This breaks up the "long vertical lines" you didn't like.
                top_panel = [
                    (x_outer, cy),              # Center spine
                    (x_outer, cy - 12),         # Vertical spine part
                    (x_mid, cy - 22),           # Angled corner (The notch)
                    (x_inner_tip, cy - 22),     # Top tip (pointing in)
                    (x_inner_tip + (side*4), cy - 8) # Return angle
                ]
                
                bot_panel = [
                    (x_outer, cy),              # Center spine
                    (x_outer, cy + 12),         # Vertical spine part
                    (x_mid, cy + 22),           # Angled corner
                    (x_inner_tip, cy + 22),     # Bottom tip (pointing in)
                    (x_inner_tip + (side*4), cy + 8) # Return angle
                ]
                
                for panel in [top_panel, bot_panel]:
                    pygame.draw.polygon(surface, BLACK, panel)   # Solar Panel
                    pygame.draw.polygon(surface, GRAY, panel, 2)  # Outer Frame
                    
                    # Internal "Solar Grid" Lines (Adds depth, removes flatness)
                    # Drawing a line from the spine to the tip
                    pygame.draw.line(surface, (40, 40, 45), panel[1], panel[3], 1)
                
                # Vertical Ridge (Thicker to look like a structural beam)
                pygame.draw.line(surface, GRAY, (x_outer, cy - 12), (x_outer, cy + 12), 4)

    def shoot_bomb(self):
        b = TIEBomb(self.rect.centerx + 8, self.rect.bottom)
        enemy_bullets.add(b); all_sprites.add(b)

    def update(self):
        self.rect.y += self.speed
        self.rect.x = self.start_x + math.sin(self.rect.y * 0.01) * 15
        self.bomb_timer += 1
        if self.bomb_timer >= 160:
            self.shoot_bomb()
            self.bomb_timer = 0
        if self.rect.top > SCREEN_HEIGHT: self.kill()

# --- BOSS CLASSES ---
class Boss(pygame.sprite.Sprite):
    """ High-Detail Imperial Star Destroyer """
    def __init__(self, level):
        super().__init__()
        # Increased size for more detail
        self.width, self.height = 240, 320
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//2, -300))
        self.max_health = 40 + level * 10
        self.health = self.max_health
        self.entering = True
        self.move_dir = 1
        
        # Pre-generate random 'Technical Greebles' for the hull surface
        self.hull_greebles = []
        for _ in range(20):
            gx = random.randint(-70, 70)
            gy = random.randint(100, 220)
            self.hull_greebles.append((gx, gy, random.randint(3, 8), random.randint(2, 4)))

    def update(self):
        if self.entering:
            self.rect.y += 1
            if self.rect.top >= 20: self.entering = False
        else:
            self.rect.x += self.move_dir * 2
            if self.rect.right > SCREEN_WIDTH - 20 or self.rect.left < 20:
                self.move_dir *= -1
            if random.randint(0, 30) == 0: self.shoot()
        spawn_particles(self.rect.centerx, self.rect.top, RED, 1)

    def draw_ship(self, surface, offset=(0,0)):
        r = self.rect.move(offset)
        cx, top = r.centerx, r.top

        # 1. UNDER-HULL (The 'Side Trench' layer)
        # Gives the ship a 3D thickness
        trench_color = (30, 30, 35)
        trench_pts = [(cx, r.bottom + 8), (r.left - 12, top + 95), (r.right + 12, top + 95)]
        pygame.draw.polygon(surface, trench_color, trench_pts)

        # 2. MAIN WEDGE HULL
        wedge_pts = [(cx, r.bottom), (r.left, top + 90), (r.right, top + 90)]
        pygame.draw.polygon(surface, GRAY, wedge_pts)
        
        # 3. HULL DETAILING
        # Central spine
        pygame.draw.line(surface, LIGHT_GRAY, (cx, r.bottom), (cx, top + 90), 2)
        
        # Panel lines (Horizontal ribs)
        for i in range(1, 7):
            ratio = i / 7
            y_pos = (top + 90) + (r.height - 130) * ratio
            w = (r.width // 2) * (1 - ratio)
            pygame.draw.line(surface, DARK_GRAY, (cx - w, y_pos), (cx + w, y_pos), 1)

        # Surface Greebles (Technical bumps)
        for gx, gy, gw, gh in self.hull_greebles:
            # Masking greebles to stay inside the triangle
            ratio = (gy - 90) / (r.height - 90)
            max_w = (r.width // 2) * (1 - ratio)
            if abs(gx) < max_w:
                pygame.draw.rect(surface, (70, 70, 80), (cx + gx, top + gy, gw, gh))

        # 4. REAR ENGINES (Blue Ion Glow)
        for ex in [-55, -25, 0, 25, 55]:
            # Pulsing logic for engines
            glow = random.randint(4, 8)
            pygame.draw.circle(surface, BLUE, (cx + ex, top + 90), glow)
            pygame.draw.circle(surface, WHITE, (cx + ex, top + 90), 3)

        # 5. SUPERSTRUCTURE (The Tiered City)
        for i in range(5):
            w, h = 65 - (i*12), 10
            y_level = top + 35 + (i*9)
            tier_rect = pygame.Rect(cx - w, y_level, w*2, h)
            # Main tier block
            pygame.draw.rect(surface, GRAY, tier_rect)
            pygame.draw.rect(surface, WHITE, tier_rect, 1)
            # Windows (Yellow flickering lights)
            for wx in range(-w + 6, w - 6, 12):
                if random.random() > 0.4:
                    pygame.draw.rect(surface, YELLOW, (cx + wx, y_level + 3, 2, 2))

        # 6. COMMAND BRIDGE TOWER
        # Neck
        pygame.draw.rect(surface, DARK_GRAY, (cx - 12, top + 20, 24, 15))
        # Bridge Face (T-shape)
        bridge_rect = pygame.Rect(cx - 35, top + 8, 70, 12)
        pygame.draw.rect(surface, GRAY, bridge_rect)
        pygame.draw.rect(surface, WHITE, bridge_rect, 1)
        # Deflector Shield Domes
        pygame.draw.circle(surface, LIGHT_GRAY, (cx - 22, top + 8), 6)
        pygame.draw.circle(surface, WHITE, (cx - 22, top + 8), 6, 1)
        pygame.draw.circle(surface, LIGHT_GRAY, (cx + 22, top + 8), 6)
        pygame.draw.circle(surface, WHITE, (cx + 22, top + 8), 6, 1)

        # 7. MAIN OUTLINE (Crisp white edge)
        pygame.draw.polygon(surface, WHITE, wedge_pts, 2)

        # 8. HEALTH BAR
        bar_w = 200
        pygame.draw.rect(surface, RED, (cx - bar_w//2, top - 25, bar_w, 8))
        pygame.draw.rect(surface, GREEN, (cx - bar_w//2, top - 25, int(bar_w * (max(0, self.health)/self.max_health)), 8))

    def shoot(self):
        # Fire from the side battery "notches"
        for side in [-1, 1]:
            # Three bolts from each side for a 'broadside' feel
            for i in range(3):
                bx = self.rect.centerx + (side * (40 + i*15))
                by = self.rect.top + 100
                b = EnemyBullet(bx, by, 0, 8)
                enemy_bullets.add(b); all_sprites.add(b)

class ExecutorBoss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        # Optimized size: Thin and long for that "Dreadnought" feel
        self.width, self.height = 280, 400 
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, -200))

        self.max_health = 150 + level * 20
        self.health = self.max_health
        self.entering = True
        self.move_dir = 1
        self.engine_pulse = 0
        self.fire_timer = 0
        
        # Pre-generate random "City Lights" and "Greebles" (Mechanical bumps)
        self.greebles = []
        for _ in range(35):
            self.greebles.append({
                'x': random.randint(-40, 40),
                'y': random.randint(60, 200),
                'w': random.randint(2, 5),
                'h': random.randint(2, 4),
                'color': random.choice([(70,70,80), (40,40,50)])
            })

    def update(self):
        if self.entering:
            self.rect.y += 1
            if self.rect.top >= 20: self.entering = False
        else:
            self.rect.x += self.move_dir * 1.2
            if self.rect.left < 40 or self.rect.right > SCREEN_WIDTH - 40:
                self.move_dir *= -1
            
            self.fire_timer += 1
            if self.fire_timer % 40 == 0: self.shoot()

        self.engine_pulse += 0.2

    def draw_ship(self, surface, offset=(0,0)):
        r = self.rect.move(offset)
        cx, cy = r.centerx, r.top

        # 1. THE SIDE TRENCH (The 'thickness' of the ship)
        # This creates the 3D look by drawing a darker shape behind the main hull
        trench_pts = [(cx, cy + 380), (cx - 130, cy + 40), (cx + 130, cy + 40)]
        pygame.draw.polygon(surface, (20, 20, 25), trench_pts)

        # 2. THE LOWER HULL (Main Wings)
        # Split into two shades for a central "spine" ridge
        hull_left = [(cx, cy + 370), (cx - 120, cy + 45), (cx, cy + 45)]
        hull_right = [(cx, cy + 370), (cx + 120, cy + 45), (cx, cy + 45)]
        pygame.draw.polygon(surface, (60, 60, 70), hull_left)
        pygame.draw.polygon(surface, (80, 80, 90), hull_right)
        pygame.draw.polygon(surface, WHITE, hull_left + hull_right, 1) # Thin crisp outline

        # 3. THE RAISED SUPERSTRUCTURE (The "City" spine)
        # This tapers toward the front
        spine_pts = [(cx, cy + 280), (cx - 45, cy + 60), (cx + 45, cy + 60)]
        pygame.draw.polygon(surface, (45, 45, 55), spine_pts)
        pygame.draw.polygon(surface, GRAY, spine_pts, 1)

        # 4. GREEBLES & WINDOWS (Technical detail)
        for g in self.greebles:
            pygame.draw.rect(surface, g['color'], (cx + g['x'], cy + g['y'], g['w'], g['h']))
            if random.random() > 0.98: # Tiny flickering window lights
                pygame.draw.rect(surface, YELLOW, (cx + g['x'], cy + g['y'], 1, 1))

        # 5. COMMAND BRIDGE TOWER (The T-shape)
        bridge_y = cy + 50
        # Neck
        pygame.draw.rect(surface, (30, 30, 40), (cx - 10, bridge_y, 20, 15))
        # Bridge Face
        pygame.draw.rect(surface, (100, 100, 110), (cx - 45, bridge_y - 10, 90, 12))
        pygame.draw.rect(surface, WHITE, (cx - 45, bridge_y - 10, 90, 12), 1)
        # Deflector Domes (The two balls on top)
        pygame.draw.circle(surface, LIGHT_GRAY, (cx - 25, bridge_y - 12), 5)
        pygame.draw.circle(surface, LIGHT_GRAY, (cx + 25, bridge_y - 12), 5)

        # 6. REAR ENGINES (Blue Ion Glow)
        # Positioned along the back edge (cy + 40)
        engine_y = cy + 35
        for i, ex in enumerate([-85, -50, -20, 20, 50, 85]):
            p = int(math.sin(self.engine_pulse + i) * 3)
            # Outer glow
            pygame.draw.circle(surface, (0, 180, 255), (cx + ex, engine_y), 7 + p)
            # Core
            pygame.draw.circle(surface, WHITE, (cx + ex, engine_y), 3)

        # 7. HEALTH BAR
        bar_w = 240
        pygame.draw.rect(surface, RED, (cx - bar_w//2, r.bottom + 10, bar_w, 8))
        pygame.draw.rect(surface, GREEN, (cx - bar_w//2, r.bottom + 10, int(bar_w * (max(0, self.health)/self.max_health)), 8))

    def shoot(self):
        # Fire a broadside of 4 bolts from the side batteries
        for side in [-1, 1]:
            for i in range(2):
                bx = self.rect.centerx + (side * (50 + i * 20))
                by = self.rect.top + 100
                b = EnemyBullet(bx, by, 0, 8)
                enemy_bullets.add(b); all_sprites.add(b)

class DeathStarBoss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.radius = 120
        self.image = pygame.Surface((self.radius*2 + 10, self.radius*2 + 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//2, -200))
        self.max_health = 100 + (level * 5)
        self.health = self.max_health
        self.entering = True
        self.move_dir = 1
        self.attack_timer = 0
        self.superlaser_charging = False
        self.charge_count = 0
        # Pre-generate random "city lights" for surface detail
        self.light_points = []
        for _ in range(40):
            # Random points within the circle
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(10, self.radius - 5)
            self.light_points.append((math.cos(angle) * dist, math.sin(angle) * dist))

    def update(self):
        if self.entering:
            self.rect.y += 2
            if self.rect.top >= 50: self.entering = False
        else:
            self.rect.x += self.move_dir * 1.5
            if self.rect.right > SCREEN_WIDTH - 50: self.rect.right = SCREEN_WIDTH - 50; self.move_dir = -1
            elif self.rect.left < 50: self.rect.left = 50; self.move_dir = 1
            self.attack_timer += 1
            if self.superlaser_charging:
                self.charge_count += 1
                dish_pos = (self.rect.centerx - 45, self.rect.centery - 45)
                spawn_particles(dish_pos[0], dish_pos[1], GREEN, 2)
                if self.charge_count > 60:
                    self.fire_superlaser()
                    self.superlaser_charging = False
                    self.charge_count = 0
            elif self.attack_timer % 200 == 0: self.superlaser_charging = True
            elif self.attack_timer % 70 == 0: self.burst_attack()

    def draw_ship(self, surface, offset=(0,0)):
        r = self.rect.move(offset)
        
        # 1. Base Sphere Shadow/Body
        pygame.draw.circle(surface, (40, 40, 45), r.center, self.radius) # Darker base
        pygame.draw.circle(surface, GRAY, r.center, self.radius, 0)
        
        # 2. Equatorial Trench (Defined)
        pygame.draw.rect(surface, (20, 20, 25), (r.left, r.centery - 5, self.radius*2, 10))
        pygame.draw.line(surface, DARK_GRAY, (r.left, r.centery), (r.right, r.centery), 1)

        # 3. Vertical Structural Ribs (Creates 3D curve effect)
        for i in range(-3, 4):
            width = int(math.cos(i * 0.4) * self.radius)
            rect_x = r.centerx - width
            # Draw curved arcs (ellipses) to simulate sphere longitude
            pygame.draw.ellipse(surface, DARK_GRAY, (r.centerx - width, r.top, width * 2, self.radius * 2), 1)

        # 4. Surface "City Lights"
        for lp in self.light_points:
            color = random.choice([CYAN, WHITE, YELLOW]) if random.random() > 0.9 else (150, 150, 150)
            pygame.draw.circle(surface, color, (int(r.centerx + lp[0]), int(r.centery + lp[1])), 1)

        # 5. Detailed Superlaser Dish
        dish_pos = (r.centerx - 45, r.centery - 45)
        # Outer rim
        pygame.draw.circle(surface, DARK_GRAY, dish_pos, 32)
        # Inner bowl with gradient-like circles
        pygame.draw.circle(surface, (60, 60, 65), dish_pos, 28)
        pygame.draw.circle(surface, (80, 80, 85), dish_pos, 20)
        # Technical lines inside dish
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            pygame.draw.line(surface, DARK_GRAY, dish_pos, (dish_pos[0] + math.cos(rad)*28, dish_pos[1] + math.sin(rad)*28), 1)
        
        # Charging effect
        if self.superlaser_charging:
            for i in range(8):
                angle = i * (math.pi / 4) + (pygame.time.get_ticks() * 0.01)
                rx, ry = dish_pos[0] + math.cos(angle) * 25, dish_pos[1] + math.sin(angle) * 25
                pygame.draw.line(surface, GREEN, (rx, ry), dish_pos, 2)
            pygame.draw.circle(surface, WHITE, dish_pos, 4 + (self.charge_count // 10))

        # 6. Final Outer Glow/Edge
        pygame.draw.circle(surface, WHITE, r.center, self.radius, 2)

        # Health Bar
        bar_width = 250
        pygame.draw.rect(surface, RED, (r.centerx - bar_width//2, r.top - 20, bar_width, 10))
        pygame.draw.rect(surface, GREEN, (r.centerx - bar_width//2, r.top - 20, int(bar_width * (max(0, self.health)/self.max_health)), 10))

    def burst_attack(self):
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            b = EnemyBullet(self.rect.centerx, self.rect.centery, math.cos(rad)*4, math.sin(rad)*4)
            enemy_bullets.add(b); all_sprites.add(b)

    def fire_superlaser(self):
        dish_pos = (self.rect.centerx - 45, self.rect.centery - 45)
        for _ in range(50):
            p = Particle(dish_pos[0], dish_pos[1], GREEN, random.uniform(-4, 4), 12, 40, 8)
            particles.add(p); all_sprites.add(p)
        for x_off in range(-15, 16, 10):
            b = EnemyBullet(dish_pos[0] + x_off, dish_pos[1], 0, 15)
            enemy_bullets.add(b); all_sprites.add(b)


# --- GAME LOGIC FUNCTIONS ---
def spawn_enemies(lvl):
    # Spawn normal enemies and bombers
    for _ in range(lvl * 3):
        x_pos = random.randint(50, SCREEN_WIDTH - 50)
        y_pos = random.randint(-500, -50)
        
        # 1% chance to be a Bomber
        if random.random() < 0.01:
            e = TIEBomber(x_pos, y_pos)
        else:
            e = Enemy(x_pos, y_pos)
            
        enemies.add(e)
        all_sprites.add(e)

    # Boss spawning logic remains the same...

    # Spawn boss every 3 levels
    if lvl % 3 == 0:
        boss_num = lvl // 3

        if boss_num % 4 == 0:
            b = DeathStarBoss(lvl)
        elif boss_num % 2 == 0:
            b = ExecutorBoss(lvl)
        else:
            b = Boss(lvl)

        bosses.add(b)
        all_sprites.add(b)



def reset_game():
    global score, level, player_lives, game_active, screen_shake_timer, hyperspace_timer
    score, level, player_lives, game_active, screen_shake_timer, hyperspace_timer = 0, 1, 3, True, 0, 0
    all_sprites.empty(); enemies.empty(); enemy_bullets.empty(); bosses.empty(); powerups.empty(); player_bullets.empty(); particles.empty()
    p = Player(); all_sprites.add(p); spawn_enemies(level)
    return p

# --- INITIAL SETUP ---
score, level, player_lives, game_active = 0, 1, 3, True
player = Player(); all_sprites.add(player); spawn_enemies(level)

# --- MAIN LOOP ---
while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if game_active and event.key == pygame.K_SPACE and hyperspace_timer <= 0: player.shoot()
            if not game_active and event.key == pygame.K_SPACE: player = reset_game()

    if game_active:
        if hyperspace_timer > 0:
            SCREEN.fill(DARK_BLUE)
            draw_hyperspace(SCREEN)
            hyperspace_timer -= 1
            if hyperspace_timer == 1:
                level += 1
                # --- NEW CODE TO GET RID OF BULLETS IN HYPERSPACE ---
                # Clear all bullets so the new level starts fresh
                enemy_bullets.empty()
                player_bullets.empty()
                # Also remove them from the master group to prevent drawing errors
                for sprite in all_sprites:
                    if isinstance(sprite, (PlayerBullet, EnemyBullet)):
                        sprite.kill()
                # ----------------------
                spawn_enemies(level)
                player.reset_position()
        else:
            all_sprites.update()
            if not player.shield:
                if pygame.sprite.spritecollide(player, enemy_bullets, True) or pygame.sprite.spritecollide(player, enemies, True):
                    player_lives -= 1; player.reset_position()
                    if player_lives <= 0: game_active = False

            hits = pygame.sprite.groupcollide(enemies, player_bullets, True, True)
            for h in hits: 
                score += 10; spawn_particles(h.rect.centerx, h.rect.centery, RED)
                if random.random() < 0.2:
                    pu = PowerUp(h.rect.centerx, h.rect.centery, random.choice(["double", "spread", "speed", "shield"]))
                    powerups.add(pu); all_sprites.add(pu)

            # --- REPLACEMENT FOR BOMB LOGIC IN MAIN LOOP ---
            bomb_hits = pygame.sprite.groupcollide(enemy_bullets, player_bullets, False, False) # Both False so they don't auto-die
            for b in bomb_hits:
                if isinstance(b, TIEBomb):
                    for bullet in bomb_hits[b]:
                        bullet.kill() # Your bullet dies
                    b.explode()     # Bomb explodes
                # Regular lasers are ignored, so your bullets fly right through them!

            for b in bosses:
                hit_list = pygame.sprite.spritecollide(b, player_bullets, True)
                for h in hit_list:
                    b.health -= 1; spawn_particles(h.rect.centerx, h.rect.centery, ORANGE, 5)
                    if b.health <= 0: 
                        screen_shake_timer = 30
                        shake_intensity = 15 if isinstance(b, DeathStarBoss) else 5
                        spawn_particles(b.rect.centerx, b.rect.centery, YELLOW, 50); b.kill(); score += 500

            collected = pygame.sprite.spritecollide(player, powerups, True)
            for pu in collected:
                if pu.type == "double": player.double_shot, player.spread_shot = True, False
                elif pu.type == "spread": player.spread_shot, player.double_shot = True, False
                elif pu.type == "speed": player.speed_timer = 400
                elif pu.type == "shield":
                    player_lives += 1

                    # Absorb animation
                    ring = AbsorbRing(player.rect.centerx, player.rect.centery)
                    particles.add(ring)
                    all_sprites.add(ring)

                    spawn_particles(player.rect.centerx, player.rect.centery, BLUE, 20)


            if not enemies and not bosses: 
                hyperspace_timer = 40

            offset = (random.randint(-shake_intensity, shake_intensity), random.randint(-shake_intensity, shake_intensity)) if screen_shake_timer > 0 else (0,0)
            if screen_shake_timer > 0: screen_shake_timer -= 1

            draw_background(SCREEN, offset)
            if any(b.entering for b in bosses):
                if (pygame.time.get_ticks() // 250) % 2 == 0:
                    warn = FONT.render("!!! BOSS APPROACHING !!!", True, RED)
                    SCREEN.blit(warn, warn.get_rect(center=(SCREEN_WIDTH//2 + offset[0], 150 + offset[1])))

            for sprite in all_sprites:
                if hasattr(sprite, 'draw_ship'): sprite.draw_ship(SCREEN, offset)
                else: SCREEN.blit(sprite.image, (sprite.rect.x + offset[0], sprite.rect.y + offset[1]))

    # UI
    SCREEN.blit(FONT.render(f"Score: {score}", True, WHITE), (10, 10))
    SCREEN.blit(FONT.render(f"Lives: {player_lives}", True, WHITE), (10, 40))
    SCREEN.blit(FONT.render(f"Level: {level}", True, WHITE), (SCREEN_WIDTH-120, 10))

    if not game_active:
        txt = BIG_FONT.render("GAME OVER", True, RED)
        SCREEN.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
        txt2 = FONT.render("Press SPACE to Restart", True, WHITE)
        SCREEN.blit(txt2, txt2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60)))

    pygame.display.flip()
