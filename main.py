import pygame
import sys

# 初始化 Pygame
pygame.init()
pygame.key.stop_text_input()

# 設定視窗
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mechanical Odyssey")

# 顏色 - 機械風格調色盤
BLACK = (10, 10, 15)
GREEN = (0, 255, 127) # 霓虹綠
BLUE = (0, 191, 255)  # 科技藍
GRAY = (70, 70, 80)
YELLOW = (255, 215, 0)
RED = (255, 69, 58)
WHITE = (230, 230, 250)

# 物理參數
GRAVITY = 0.5
PLAYER_SPEED = 5
CLIMB_SPEED = 3
JUMP_FORCE = -10
MAX_ENERGY = 100
ENERGY_CONSUMPTION = 0.5
ENERGY_RECOVERY = 0.2

# 遊戲狀態
MENU = 0
PLAYING = 1
GAMEOVER = 2

# 本地化設定
LANG = "zh"
TEXTS = {
    "zh": {
        "title": "機械奧德賽",
        "start": "按 ENTER 開始",
        "controls": "控制: 方向鍵移動, SPACE 跳躍, L-CTRL 吸附/爬行",
        "climb": "按 L-CTRL 吸附/爬行",
        "energy": "關卡: {level} | 能量: {energy}",
        "gameover": "恭喜通關！按 ESC 退出"
    },
    "en": {
        "title": "MECHANICAL ODYSSEY",
        "start": "Press ENTER to Start",
        "controls": "Controls: Arrows to Move, SPACE to Jump, L-CTRL to Cling",
        "climb": "Hold L-CTRL to Cling/Climb",
        "energy": "Level: {level} | Energy: {energy}",
        "gameover": "You Won! Press ESC to Exit"
    }
}

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))

class DataShard(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))

class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(x, y))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(50, HEIGHT - 50))
        self.vel_x = 0
        self.vel_y = 0
        self.is_on_ground = False
        self.energy = MAX_ENERGY

    def update(self, keys, walls, shards, goal):
        # 1. Input - Using polling directly in update
        clinging_key = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        dx = 0
        if keys[pygame.K_LEFT]: dx = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT]: dx = PLAYER_SPEED
        
        # 2. Collision Detection for Cling
        cling_rect = self.rect.inflate(8, 0)
        is_touching_wall = any(cling_rect.colliderect(wall.rect) for wall in walls)
        
        # 3. Movement
        # 嚴格能量檢查：若能量為 0，強制取消吸附狀態
        if clinging_key and is_touching_wall and self.energy > 0:
            self.energy = max(0, self.energy - ENERGY_CONSUMPTION)
            self.vel_x = 0
            self.vel_y = 0
            if keys[pygame.K_UP]: self.vel_y = -CLIMB_SPEED
            elif keys[pygame.K_DOWN]: self.vel_y = CLIMB_SPEED
        else:
            self.vel_y += GRAVITY
            # 能量恢復邏輯
            if not clinging_key:
                self.energy = min(MAX_ENERGY, self.energy + ENERGY_RECOVERY)
            self.vel_x = dx
        
        # 4. Apply Collision
        self.rect.x += self.vel_x
        # X collision
        hit_wall = pygame.sprite.spritecollideany(self, walls)
        if hit_wall:
            if self.vel_x > 0: self.rect.right = hit_wall.rect.left
            elif self.vel_x < 0: self.rect.left = hit_wall.rect.right
        
        self.rect.y += self.vel_y
        
        # Y collision
        hit_platform = pygame.sprite.spritecollideany(self, walls)
        self.is_on_ground = False
        if hit_platform:
            if self.vel_y > 0:
                self.rect.bottom = hit_platform.rect.top
                self.vel_y = 0
                self.is_on_ground = True
            elif self.vel_y < 0:
                self.rect.top = hit_platform.rect.bottom
                self.vel_y = 0
        
        if self.rect.bottom > HEIGHT:
            return "DIE"
            
        # 跳躍
        if keys[pygame.K_SPACE]:
            if self.is_on_ground:
                self.vel_y = JUMP_FORCE
                self.is_on_ground = False
            elif clinging_key and is_touching_wall:
                self.vel_y = JUMP_FORCE
                self.vel_x = PLAYER_SPEED

        collected = pygame.sprite.spritecollide(self, shards, True)
        for shard in collected:
            self.energy = min(MAX_ENERGY, self.energy + 30)

        return pygame.sprite.spritecollideany(self, goal)

def draw_centered_text(text, font, color, y_offset):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    SCREEN.blit(surface, rect)

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + int(WIDTH / 2)
        # 限制攝影機不移出畫面邊界
        x = min(0, max(x, -(self.width - WIDTH)))
        self.camera = pygame.Rect(x, 0, self.width, self.height)

def main():
    state = MENU
    level_num = 1
    player = Player()
    walls, shards, goal = setup_level(level_num)
    camera = Camera(WIDTH * 2, HEIGHT)
    
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("microsoftyahei", 60)
    font_small = pygame.font.SysFont("microsoftyahei", 30)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if state == MENU and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                state = PLAYING
            if state == GAMEOVER and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        
        SCREEN.fill(BLACK)
        
        if state == MENU:
            draw_centered_text(TEXTS[LANG]["title"], font_large, GREEN, -150)
            draw_centered_text(TEXTS[LANG]["start"], font_small, YELLOW, -50)
            draw_centered_text(TEXTS[LANG]["controls"], font_small, WHITE, 50)
            draw_centered_text(TEXTS[LANG]["climb"], font_small, WHITE, 90)
        
        elif state == PLAYING:
            keys = pygame.key.get_pressed()
            result = player.update(keys, walls, shards, goal)
            camera.update(player)
            
            if result == "DIE":
                player.rect.center = (50, HEIGHT - 50)
            elif result:
                level_num += 1
                if level_num > 3: state = GAMEOVER
                else:
                    player.rect.center = (50, HEIGHT - 50)
                    walls, shards, goal = setup_level(level_num)
                    camera.update(player)
            
            # 確保攝影機偏移量應用在所有繪製物件上
            for wall in walls: SCREEN.blit(wall.image, camera.apply(wall))
            for shard in shards: SCREEN.blit(shard.image, camera.apply(shard))
            for g in goal: SCREEN.blit(g.image, camera.apply(g))
            SCREEN.blit(player.image, camera.apply(player))
            
            energy_display = TEXTS[LANG]["energy"].format(level=level_num, energy=int(player.energy))
            font = pygame.font.SysFont("microsoftyahei", 30)
            SCREEN.blit(font.render(energy_display, True, BLUE), (10, 10))
            
        elif state == GAMEOVER:
            draw_centered_text(TEXTS[LANG]["gameover"], font_large, WHITE, 0)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()

def setup_level(level_num):
    walls = pygame.sprite.Group()
    shards = pygame.sprite.Group()
    goal = pygame.sprite.Group()
    if level_num == 1:
        walls.add(Wall(0, 550, 400, 50), Wall(400, 450, 50, 150), Wall(450, 450, 600, 50), Wall(1000, 200, 50, 400))
        shards.add(DataShard(450, 400), DataShard(800, 400))
        goal.add(Goal(1100, 150))
    elif level_num == 2:
        walls.add(Wall(0, 550, 200, 50), Wall(200, 200, 50, 400), Wall(250, 200, 500, 50), Wall(700, 200, 50, 400), Wall(700, 550, 200, 50))
        shards.add(DataShard(300, 150), DataShard(500, 150))
        goal.add(Goal(800, 500))
    elif level_num == 3:
        # Level 3: Ceiling Maze - Fixed Path
        walls.add(Wall(0, 550, 200, 50), Wall(200, 500, 50, 100), Wall(250, 200, 50, 350), Wall(300, 200, 400, 50), Wall(700, 200, 50, 400))
        shards.add(DataShard(400, 300), DataShard(500, 300))
        goal.add(Goal(750, 550))
    return walls, shards, goal

if __name__ == "__main__":
    main()
