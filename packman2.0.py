import arcade
import random
import math
import time

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 750
MOVEMENT_SPEED = 140
BOOSTED_SPEED = 300
PLAYER_RADIUS = 25
COIN_RADIUS_BASE = 10
ENEMY_SIZE = 15
SHOOTER_SIZE = 20
BIG_ENEMY_SIZE = 28
YELLOW_SIZE = 18
BULLET_SIZE = 4
MAX_LEVEL = 10
MIN_ENEMY_DIST = 80
PLAYER_MAX_HP = 5
UPGRADE_DURATION = 5.0
ENEMY_ATTACK_COOLDOWN = 3.0

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Игра ✅ НОВЫЕ ВРАГИ!")
        arcade.set_background_color((0, 100, 0))
        self.reset_game()

    def reset_game(self):
        self.player_x = 100
        self.player_y = SCREEN_HEIGHT//2
        self.player_vx = 0
        self.player_vy = 0
        self.player_hp = PLAYER_MAX_HP
        self.player_shield = 0
        self.speed_boost_end = 0
        self.magnet_boost_end = 0
        self.god_mode = False
        self.notifications = []
        self.coins = []
        self.enemies = []
        self.big_enemies = []
        self.yellow_enemies = []
        self.enemies_attack_time = {}
        self.shooters = []
        self.bullets = []
        self.upgrades = []
        self.score = 0
        self.level = 1
        self.game_over = False
        self.victory = False
        self.collected_for_upgrade = 0
        self.level_start_score = 0
        self.last_bullet_time = {}
        self.setup()

    def setup(self):
        self.generate_level()
        self.level_start_score = self.score

    def safe_spawn_enemy(self, attempts=200, avoid_coins=True):
        for _ in range(attempts):
            if random.random() < 0.5:
                spawn_zone = random.choice(['top', 'bottom'])
                if spawn_zone == 'top':
                    x = SCREEN_WIDTH * random.uniform(0.2, 0.8)
                    y = random.uniform(50, SCREEN_HEIGHT * 0.3)
                else:
                    x = SCREEN_WIDTH * random.uniform(0.2, 0.8)
                    y = random.uniform(SCREEN_HEIGHT * 0.7, SCREEN_HEIGHT - 50)
            else:
                spawn_zone = random.choice(['left', 'right'])
                if spawn_zone == 'left':
                    x = random.uniform(50, SCREEN_WIDTH * 0.3)
                    y = SCREEN_HEIGHT * random.uniform(0.2, 0.8)
                else:
                    x = random.uniform(SCREEN_WIDTH * 0.7, SCREEN_WIDTH - 50)
                    y = SCREEN_HEIGHT * random.uniform(0.2, 0.8)
            
            if math.hypot(self.player_x - x, self.player_y - y) < 150:
                continue
                
            too_close_enemy = any(math.hypot(x - e['x'], y - e['y']) < MIN_ENEMY_DIST 
                                 for e in self.enemies + self.big_enemies + self.yellow_enemies + self.shooters)
            if too_close_enemy:
                continue
            if avoid_coins:
                on_coin = any(math.hypot(x - c['x'], y - c['y']) < COIN_RADIUS_BASE + 30 
                             for c in self.coins)
                if on_coin:
                    continue
            
            return x, y
        
        return SCREEN_WIDTH//2 + random.randint(-100, 100), SCREEN_HEIGHT//2 + random.randint(-100, 100)

    def generate_level(self):
        self.total_coins = 50 + self.level * 10
        
        self.coins = []
        coin_r = max(3, COIN_RADIUS_BASE - self.level // 3)
        for _ in range(self.total_coins):
            attempts = 0
            while attempts < 50:
                if random.random() < 0.7:
                    x = SCREEN_WIDTH * 0.5 + random.uniform(-350, 350)
                    y = SCREEN_HEIGHT * 0.5 + random.uniform(-250, 250)
                else:
                    x = random.randint(30, SCREEN_WIDTH-30)
                    y = random.randint(30, SCREEN_HEIGHT-30)
                
                x = max(30, min(SCREEN_WIDTH-30, x))
                y = max(30, min(SCREEN_HEIGHT-30, y))
                
                if math.hypot(self.player_x - x, self.player_y - y) > 80:
                    too_close_coin = any(math.hypot(x - c['x'], y - c['y']) < 40 for c in self.coins)
                    if not too_close_coin:
                        self.coins.append({'x': x, 'y': y, 'r': coin_r})
                        break
                attempts += 1
        
        self.enemies = []
        self.enemies_attack_time.clear()
        enemy_count = min(5, self.level + (self.level // 2))
        for _ in range(enemy_count):
            x, y = self.safe_spawn_enemy(avoid_coins=False)
            enemy_id = id({})
            self.enemies.append({
                'x': x, 'y': y, 
                'speed': 75 + self.level * 1.8,
                'id': enemy_id,
                'intelligence': 0.85 + self.level * 0.02,
                'damage': 2
            })
            self.enemies_attack_time[enemy_id] = 0
        
        self.big_enemies = []
        if self.level >= 6:
            big_count = min(2, (self.level - 5))
            for _ in range(big_count):
                x, y = self.safe_spawn_enemy(avoid_coins=False)
                enemy_id = id({})
                self.big_enemies.append({
                    'x': x, 'y': y, 
                    'speed': 75 + self.level * 1.5,
                    'id': enemy_id,
                    'damage': 2
                })
                self.enemies_attack_time[enemy_id] = 0
        
        self.yellow_enemies = []
        if self.level >= 4:
            yellow_count = min(3, self.level - 3)
            for _ in range(yellow_count):
                x, y = self.safe_spawn_enemy(avoid_coins=True)
                self.yellow_enemies.append({
                    'x': x, 'y': y,
                    'speed': MOVEMENT_SPEED - 10,
                    'attack_time': 0,
                    'damage': 1,
                    'ghost': True  # ✅ Желтые - призраки!
                })

        self.shooters = []
        self.last_bullet_time.clear()
        if self.level >= 2:
            shooter_count = 2
            for i in range(shooter_count):
                x, y = self.safe_spawn_enemy(avoid_coins=True)
                self.shooters.append({
                    'x': x, 'y': y, 
                    'speed': 70,
                    'accuracy': 0.95,
                    'shot_offset': -15 if i == 0 else 15
                })

        self.add_notification(f"🎮 УР.{self.level} | Монет: {self.total_coins}")

    def spawn_upgrade(self, x=None, y=None):
        if x is None:
            x = random.randint(100, SCREEN_WIDTH-100)
            y = random.randint(100, SCREEN_HEIGHT-100)
        
        rand = random.randint(1, 3)
        if rand == 1:
            upgrade_type = 'speed'
            symbol = '⚡'
            color = (255, 255, 0)
        elif rand == 2:
            upgrade_type = 'magnet'
            symbol = '🧲'
            color = (0, 255, 255)
        else:
            upgrade_type = 'shield'
            symbol = '🛡️'
            color = (0, 255, 0)
        
        self.upgrades.append({
            'x': x, 'y': y, 'r': 14, 
            'type': upgrade_type,
            'symbol': symbol,
            'color': color
        })
        
        type_names = {'speed': 'СКОРОСТЬ 300', 'magnet': 'МАГНИТ +75px', 'shield': 'ЩИТ'}
        self.add_notification(f"✨ {type_names[upgrade_type]}!")

    def add_notification(self, message):
        current_time = time.time()
        self.notifications.insert(0, {'text': message, 'time': current_time})

    def get_current_speed(self):
        if time.time() < self.speed_boost_end:
            return BOOSTED_SPEED
        return MOVEMENT_SPEED

    def get_coin_collect_radius(self):
        base_radius = PLAYER_RADIUS + COIN_RADIUS_BASE
        if time.time() < self.magnet_boost_end:
            return base_radius + 75
        return base_radius

    def is_speed_active(self):
        return time.time() < self.speed_boost_end

    def is_magnet_active(self):
        return time.time() < self.magnet_boost_end

    def can_enemy_attack(self, enemy_id):
        current_time = time.time()
        return enemy_id not in self.enemies_attack_time or current_time - self.enemies_attack_time[enemy_id] >= ENEMY_ATTACK_COOLDOWN

    def resolve_enemy_collisions(self, delta_time):
        # ✅ Исключаем желтых врагов из коллизий
        collidable_enemies = self.enemies + self.big_enemies + self.shooters
        
        for i, e1 in enumerate(collidable_enemies):
            for j, e2 in enumerate(collidable_enemies[i+1:], i+1):
                dx = e1['x'] - e2['x']
                dy = e1['y'] - e2['y']
                dist = math.hypot(dx, dy)
                
                if dist < MIN_ENEMY_DIST and dist > 0:
                    force = (MIN_ENEMY_DIST - dist) * 100 * delta_time
                    e1['x'] += (dx / dist) * force
                    e1['y'] += (dy / dist) * force
                    e2['x'] -= (dx / dist) * force
                    e2['y'] -= (dy / dist) * force

    def on_draw(self):
        self.clear()
        
        bg_color = (0, 100 + self.level * 8, 0)
        arcade.set_background_color(bg_color)
        
        player_color = (0, 255, 255)
        if self.is_speed_active():
            player_color = (255, 255, 150)
        elif self.god_mode:
            player_color = (255, 255, 0)
        
        arcade.draw_circle_filled(self.player_x, self.player_y, PLAYER_RADIUS, player_color)
        arcade.draw_circle_filled(self.player_x - 8, self.player_y + 5, 4, (0, 0, 0))
        arcade.draw_circle_filled(self.player_x + 8, self.player_y + 5, 4, (0, 0, 0))
        
        # HUD
        speed = self.get_current_speed()
        speed_color = (255, 255, 0) if self.is_speed_active() else (255, 255, 255)
        arcade.draw_text(f"Скорость: {speed}", 10, SCREEN_HEIGHT - 25, speed_color, 20)
        
        if self.is_magnet_active():
            arcade.draw_text("🧲 МАГНИТ +75px", 220, SCREEN_HEIGHT - 25, (0, 255, 255), 18)
        
        hp_total = self.player_hp + self.player_shield
        god_text = " 🛡️" if self.god_mode else ""
        arcade.draw_text(f"HP: {hp_total}/7{god_text}  Щит: {self.player_shield}", 10, SCREEN_HEIGHT - 50, (255, 255, 255), 16)
        
        level_progress = self.score - self.level_start_score
        arcade.draw_text(f"Ур.{self.level}: {level_progress}/{self.total_coins}", 10, SCREEN_HEIGHT - 105, (0, 255, 0), 16)
        arcade.draw_text(f"Общий: {self.score}", 10, SCREEN_HEIGHT - 125, (255, 255, 255), 14)
        arcade.draw_text(f"До баффа: {20 - (self.collected_for_upgrade % 20)}", 10, SCREEN_HEIGHT - 145, (255, 200, 0), 14)
        
        collect_radius = self.get_coin_collect_radius()
        for coin in self.coins:
            dist = math.hypot(self.player_x - coin['x'], self.player_y - coin['y'])
            if dist <= collect_radius:
                arcade.draw_circle_filled(coin['x'], coin['y'], coin['r'] + 2, (255, 200, 0))
            else:
                arcade.draw_circle_filled(coin['x'], coin['y'], coin['r'], (255, 255, 0))
        
        if self.is_magnet_active():
            arcade.draw_circle_outline(self.player_x, self.player_y, collect_radius, (0, 255, 255), 2)
        
        for upgrade in self.upgrades:
            arcade.draw_circle_filled(upgrade['x'], upgrade['y'], upgrade['r'], upgrade['color'])
            arcade.draw_text(upgrade['symbol'], upgrade['x'], upgrade['y'], (0, 0, 0), 16, anchor_x="center", anchor_y="center")
        
        for yellow in self.yellow_enemies:
            arcade.draw_circle_filled(yellow['x'], yellow['y'], YELLOW_SIZE, (255, 200, 0))
        
        for enemy in self.enemies:
            c = (255 - self.level * 12, 20, 20)
            arcade.draw_circle_filled(enemy['x'], enemy['y'], ENEMY_SIZE, c)
        
        for big_enemy in self.big_enemies:
            c = (200, 10, 10)
            arcade.draw_circle_filled(big_enemy['x'], big_enemy['y'], BIG_ENEMY_SIZE, c)
            for angle in range(0, 360, 45):
                rx = big_enemy['x'] + math.cos(math.radians(angle)) * BIG_ENEMY_SIZE
                ry = big_enemy['y'] + math.sin(math.radians(angle)) * BIG_ENEMY_SIZE
                arcade.draw_circle_filled(rx, ry, 4, (255, 255, 255))
        
        for shooter in self.shooters:
            arcade.draw_circle_filled(shooter['x'], shooter['y'], SHOOTER_SIZE, (180, 0, 180))
            arcade.draw_circle_outline(shooter['x'], shooter['y'], SHOOTER_SIZE, (255, 0, 255), 2)
        
        for bullet in self.bullets:
            arcade.draw_circle_filled(bullet['x'], bullet['y'], BULLET_SIZE, (255, 100, 100))
        
        current_time = time.time()
        for i, notif in enumerate(self.notifications[:]):
            age = current_time - notif['time']
            if age < 3.5:
                y_pos = SCREEN_HEIGHT - 170 - i * 25
                arcade.draw_text(notif['text'], SCREEN_WIDTH//2, y_pos, (255, 255, 0), 18, anchor_x="center")
            else:
                self.notifications.remove(notif)
        
        if self.game_over:
            color = (255, 255, 0) if self.victory else (255, 0, 0)
            text = "🎉 ПОБЕДА!" if self.victory else "💀 GAME OVER"
            arcade.draw_text(text, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, color, 40, anchor_x="center")
            arcade.draw_text(f"Счёт: {self.score}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60, (255, 255, 255), 28, anchor_x="center")
            arcade.draw_text("T - рестарт", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 110, (255, 255, 255), 20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.T:
                self.reset_game()
            return
        
        if key == arcade.key.F1:
            if self.level < MAX_LEVEL:
                self.level += 1
                self.add_notification(f"🚀 УРОВЕНЬ {self.level}!")
                self.setup()
            return
        
        if key == arcade.key.F9:
            self.god_mode = not self.god_mode
            status = "ВКЛ" if self.god_mode else "ВЫКЛ"
            self.add_notification(f"🛡️ Бессмертие {status}!")
            return
        
        speed = self.get_current_speed()
        if key == arcade.key.W: self.player_vy = speed
        elif key == arcade.key.S: self.player_vy = -speed
        elif key == arcade.key.A: self.player_vx = -speed
        elif key == arcade.key.D: self.player_vx = speed

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.W, arcade.key.S): self.player_vy = 0
        if key in (arcade.key.A, arcade.key.D): self.player_vx = 0

    def on_update(self, delta_time):
        if self.game_over: return
        
        self.player_x += self.player_vx * delta_time
        self.player_y += self.player_vy * delta_time
        self.player_x = max(PLAYER_RADIUS, min(SCREEN_WIDTH - PLAYER_RADIUS, self.player_x))
        self.player_y = max(PLAYER_RADIUS, min(SCREEN_HEIGHT - PLAYER_RADIUS, self.player_y))
        
        self.magnet_pull(delta_time)
        self.collect_items()
        self.spawn_upgrades_if_needed()
        
        self.move_enemies(delta_time)
        self.resolve_enemy_collisions(delta_time)
        self.update_bullets(delta_time)
        self.check_collisions()
        
        for obj_list in [self.enemies, self.big_enemies, self.yellow_enemies, self.shooters]:
            for obj in obj_list:
                obj['x'] = max(25, min(SCREEN_WIDTH - 25, obj['x']))
                obj['y'] = max(25, min(SCREEN_HEIGHT - 25, obj['y']))
        
        level_progress = self.score - self.level_start_score
        if level_progress >= self.total_coins:
            if self.level < MAX_LEVEL:
                self.level += 1
                self.add_notification(f"🚀 УРОВЕНЬ {self.level}!")
                self.setup()
            else:
                self.game_over = True
                self.victory = True

    def magnet_pull(self, delta_time):
        if not self.is_magnet_active(): return
        pull_radius = 200
        pull_force = 250 * delta_time
        for coin in self.coins:
            dx = self.player_x - coin['x']
            dy = self.player_y - coin['y']
            dist = math.hypot(dx, dy)
            if dist < pull_radius and dist > self.get_coin_collect_radius():
                coin['x'] += (dx / dist) * pull_force
                coin['y'] += (dy / dist) * pull_force

    def collect_items(self):
        collect_radius = self.get_coin_collect_radius()
        for coin in self.coins[:]:
            dist = math.hypot(self.player_x - coin['x'], self.player_y - coin['y'])
            if dist <= collect_radius:
                self.coins.remove(coin)
                self.score += 1
                self.collected_for_upgrade += 1
        for upgrade in self.upgrades[:]:
            dist = math.hypot(self.player_x - upgrade['x'], self.player_y - upgrade['y'])
            if dist <= PLAYER_RADIUS + upgrade['r']:
                self.apply_upgrade(upgrade['type'])
                self.upgrades.remove(upgrade)

    def spawn_upgrades_if_needed(self):
        if len(self.upgrades) == 0 and self.collected_for_upgrade % 20 == 0 and self.collected_for_upgrade > 0:
            self.spawn_upgrade()

    def apply_upgrade(self, upgrade_type):
        current_time = time.time()
        if upgrade_type == 'speed':
            self.speed_boost_end = current_time + UPGRADE_DURATION
            self.add_notification("⚡ 300мс на 5с!")
        elif upgrade_type == 'magnet':
            self.magnet_boost_end = current_time + UPGRADE_DURATION
            self.add_notification("🧲 Магнит +75px!")
        elif upgrade_type == 'shield':
            if self.player_shield < 2:
                self.player_shield += 1
                self.add_notification(f"🛡️ Щит {self.player_shield}!")

    def move_enemies(self, delta_time):
        for enemy in self.enemies:
            dx = self.player_x - enemy['x']
            dy = self.player_y - enemy['y']
            dist = math.hypot(dx, dy)
            if dist > PLAYER_RADIUS + ENEMY_SIZE + 10:
                deviation = random.uniform(-0.1, 0.1) * (1 - enemy['intelligence'])
                move_x = (dx / dist) * enemy['speed'] * delta_time * enemy['intelligence']
                move_y = (dy / dist) * enemy['speed'] * delta_time * enemy['intelligence']
                enemy['x'] += move_x + deviation
                enemy['y'] += move_y - deviation
        for big_enemy in self.big_enemies:
            dx = self.player_x - big_enemy['x']
            dy = self.player_y - big_enemy['y']
            dist = math.hypot(dx, dy)
            if dist > PLAYER_RADIUS + BIG_ENEMY_SIZE + 10:
                big_enemy['x'] += (dx / dist) * big_enemy['speed'] * delta_time
                big_enemy['y'] += (dy / dist) * big_enemy['speed'] * delta_time
        for yellow in self.yellow_enemies:
            dx = self.player_x - yellow['x']
            dy = self.player_y - yellow['y']
            dist = math.hypot(dx, dy)
            if dist > PLAYER_RADIUS + YELLOW_SIZE + 10:
                yellow['x'] += (dx / dist) * yellow['speed'] * delta_time
                yellow['y'] += (dy / dist) * yellow['speed'] * delta_time
        for shooter in self.shooters:
            dx = self.player_x - shooter['x']
            dy = self.player_y - shooter['y']
            dist = math.hypot(dx, dy)
            if dist > 60:
                shooter['x'] += (dx / dist) * shooter['speed'] * delta_time
                shooter['y'] += (dy / dist) * shooter['speed'] * delta_time

    def update_bullets(self, delta_time):
        current_time = time.time()
        for shooter in self.shooters:
            sid = id(shooter)
            if sid not in self.last_bullet_time or current_time - self.last_bullet_time[sid] > 1.8:
                dx = self.player_x - shooter['x']
                dy = self.player_y - shooter['y']
                dist = math.hypot(dx, dy)
                if dist > 0:
                    accuracy_factor = shooter.get('accuracy', 0.95)
                    bullet_speed = 280 * accuracy_factor
                    self.bullets.append({
                        'x': shooter['x'], 
                        'y': shooter['y'],
                        'vx': (dx / dist) * bullet_speed, 
                        'vy': (dy / dist) * bullet_speed
                    })
                    self.last_bullet_time[sid] = current_time
        
        for bullet in self.bullets[:]:
            bullet['x'] += bullet['vx'] * delta_time
            bullet['y'] += bullet['vy'] * delta_time
            if not (0 < bullet['x'] < SCREEN_WIDTH and 0 < bullet['y'] < SCREEN_HEIGHT):
                self.bullets.remove(bullet)

    def check_collisions(self):
        if self.god_mode:
            return
            
        current_time = time.time()
        for enemy in self.enemies:
            if math.hypot(self.player_x - enemy['x'], self.player_y - enemy['y']) < PLAYER_RADIUS + ENEMY_SIZE:
                if self.can_enemy_attack(enemy['id']):
                    self.take_damage(enemy['damage'])
                    self.enemies_attack_time[enemy['id']] = current_time
                    return
        for big_enemy in self.big_enemies:
            if math.hypot(self.player_x - big_enemy['x'], self.player_y - big_enemy['y']) < PLAYER_RADIUS + BIG_ENEMY_SIZE:
                if self.can_enemy_attack(big_enemy['id']):
                    self.take_damage(big_enemy['damage'])
                    self.enemies_attack_time[big_enemy['id']] = current_time
                    return
        for yellow in self.yellow_enemies:
            if math.hypot(self.player_x - yellow['x'], self.player_y - yellow['y']) < PLAYER_RADIUS + YELLOW_SIZE:
                if 'last_attack' not in yellow or current_time - yellow['last_attack'] >= 3.0:
                    self.take_damage(yellow['damage'])
                    yellow['last_attack'] = current_time
                    return
        for bullet in self.bullets[:]:
            if math.hypot(self.player_x - bullet['x'], self.player_y - bullet['y']) < PLAYER_RADIUS + BULLET_SIZE:
                self.bullets.remove(bullet)
                self.take_damage(2)
                return

    def take_damage(self, damage):
        self.add_notification(f"Урон {damage}")
        if self.player_shield > 0:
            self.player_shield -= damage
            if self.player_shield < 0:
                self.player_hp += self.player_shield
                self.player_shield = 0
        else:
            self.player_hp -= damage
        
        if self.player_hp <= 0:
            self.game_over = True

if __name__ == "__main__":
    game = MyGame()
    arcade.run()
