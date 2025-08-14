import pygame
import random
import math
import json
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize pygame
pygame.init()

# Game Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 640
FPS = 60
WORLD_WIDTH = 3000
WORLD_HEIGHT = 3000

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (100, 150, 255)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
PURPLE = (128, 0, 128)
GOLD = (255, 215, 0)

class Player:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.hp = 100
        self.max_hp = 100
        self.attack = 10
        self.position = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.speed = 200
        self.size = 20
        self.active_quests = {}
        self.inventory = {"Gold": 0, "Silver": 0, "Bronze": 0}
        self.wolves_killed = 0
        self.bears_killed = 0
        self.snakes_killed = 0
        self.boars_killed = 0
        self.bandits_killed = 0
        self.unlocked_skills = []
        self.skills = [
            {"name": "Skill 1", "cooldown": 3.0, "last_used": 0.0},
            {"name": "Skill 2", "cooldown": 5.0, "last_used": 0.0},
            {"name": "Skill 3", "cooldown": 8.0, "last_used": 0.0},
            {"name": "Skill 4", "cooldown": 12.0, "last_used": 0.0}
        ]
        self.last_shot_time = 0.0
        self.shoot_cooldown = 0.3
        # Add quest items tracking
        self.quest_items = {
            "Bandit Head": 0,
            "Wolf Fang": 0,
            "Snake Venom": 0,
            "Boar Tusk": 0,
            "Dragon Scale": 0,
            "Demon Essence": 0,
            "Ancient Relic": 0
        }
        # Add domain and community system
        self.current_domain = 1
        self.community_center = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.graveyard_position = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2 + 200)  # South of village
        self.hearthstone_cooldown = 0.0
        self.hearthstone_duration = 60.0  # 1 minute cooldown
        self.is_dead = False
        self.death_timer = 0.0
        self.respawn_time = 5.0  # 5 seconds to respawn
        
    def level_up(self):
        self.level += 1
        self.max_hp += 20
        self.hp = self.max_hp
        self.attack += 5
        print(f"LEVEL UP! You are now level {self.level}!")
        
        # Unlock new skill every 5 levels
        if self.level % 5 == 0:
            skill_num = len(self.unlocked_skills) + 1
            if skill_num <= 4:
                self.unlocked_skills.append(skill_num)
                print(f"New skill unlocked: Skill {skill_num}!")
        
    def gain_exp(self, amount):
        self.exp += amount
        # Loop to handle carry-over EXP for multiple level-ups
        exp_needed = self.get_exp_needed()
        while self.exp >= exp_needed:
            self.exp -= exp_needed
            self.level_up()
            exp_needed = self.get_exp_needed()
            
    def get_exp_needed(self):
        return 100 + (self.level - 1) * 50
        
    def lose_exp_penalty(self):
        penalty = int(self.exp * 0.1)
        self.exp -= penalty
        print(f"You lost {penalty} experience points due to death!")
        
    def respawn(self):
        self.hp = self.max_hp
        self.position = self.graveyard_position.copy()
        self.is_dead = False
        self.death_timer = 0.0
        print("You have respawned at the graveyard!")
        
    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.death_timer = self.respawn_time
            self.lose_exp_penalty()
            print("You have died! Respawning in 5 seconds...")
            
    def use_hearthstone(self, current_time):
        if self.hearthstone_cooldown > 0:
            print(f"Hearthstone is on cooldown! {self.hearthstone_cooldown:.1f}s remaining")
            return False
            
        self.position = self.community_center.copy()
        self.hearthstone_cooldown = self.hearthstone_duration
        print("Hearthstone activated! Teleported to community center.")
        return True
        
    def use_skill(self, skill_num, current_time):
        if skill_num not in self.unlocked_skills:
            return False
            
        if skill_num > len(self.skills):
            return False
            
        skill = self.skills[skill_num - 1]
        if current_time - skill["last_used"] < skill["cooldown"]:
            return False
            
        skill["last_used"] = current_time
        return True

class Mob:
    def __init__(self, name, level, hp, attack, exp_reward, position):
        self.name = name
        self.level = level
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.exp_reward = exp_reward
        self.position = position
        self.size = 15
        self.speed = random.uniform(40, 70)
        self.aggro = False
        self.aggro_timer = 0.0
        self.last_hit_time = 0.0
        
        # Add AI movement properties
        self.spawn_position = position.copy()  # Original spawn point
        self.wander_radius = random.randint(80, 150)  # How far they wander from spawn
        self.wander_target = self.get_random_wander_target()
        self.wander_timer = 0.0
        self.wander_duration = random.uniform(2.0, 5.0)  # How long to move to target
        self.idle_timer = 0.0
        self.idle_duration = random.uniform(1.0, 3.0)  # How long to stay idle
        
    def get_random_wander_target(self):
        """Get a random position within wander radius"""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(20, self.wander_radius)
        offset = pygame.Vector2(
            math.cos(angle) * distance,
            math.sin(angle) * distance
        )
        return self.spawn_position + offset
        
    def update_ai(self, dt, player_position, player_level):
        """Update enemy AI behavior"""
        to_player = player_position - self.position
        dist_to_player = to_player.length()
        
        # Check if player is in detection range (use player level for difficulty color)
        detection_radius = 100 if self.get_difficulty_color(player_level) == RED else 60
        
        if dist_to_player < detection_radius or self.aggro:
            # Chase player
            if dist_to_player > 0:
                to_player.normalize_ip()
                self.position += to_player * self.speed * dt
            self.aggro = True
            self.aggro_timer = 3.0  # Reset aggro timer
        else:
            # Wander around spawn point
            if self.aggro:
                self.aggro_timer -= dt
                if self.aggro_timer <= 0:
                    self.aggro = False
                    self.wander_target = self.get_random_wander_target()
                    self.wander_timer = 0.0
                    self.idle_timer = 0.0
            
            if not self.aggro:
                # Check if we should be idle or moving
                if self.idle_timer > 0:
                    self.idle_timer -= dt
                elif self.wander_timer < self.wander_duration:
                    # Move towards wander target
                    to_target = self.wander_target - self.position
                    if to_target.length() > 5:  # If not close enough to target
                        to_target.normalize_ip()
                        self.position += to_target * (self.speed * 0.5) * dt  # Slower when wandering
                    self.wander_timer += dt
                else:
                    # Get new wander target and start idle
                    self.wander_target = self.get_random_wander_target()
                    self.wander_timer = 0.0
                    self.idle_timer = self.idle_duration
        
    def get_difficulty_color(self, player_level):
        level_diff = self.level - player_level
        if level_diff <= -5:
            return GRAY
        elif level_diff <= -2:
            return GREEN
        elif abs(level_diff) <= 2:
            return YELLOW
        elif level_diff <= 4:
            return ORANGE
        else:
            return RED
            
    def exp_chance(self, player_level):
        level_diff = self.level - player_level
        if level_diff <= -5:
            return 0.0
        elif level_diff <= -2:
            return 0.15
        elif abs(level_diff) <= 2:
            return 0.30
        elif level_diff <= 4:
            return 1.0
        else:
            return 1.0
        
    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self.aggro = True
        self.aggro_timer = 3.0
        self.last_hit_time = pygame.time.get_ticks() / 1000.0
        
    def is_dead(self):
        return self.hp <= 0

class Bullet:
    def __init__(self, position, velocity, radius, lifetime):
        self.position = position
        self.velocity = velocity
        self.radius = radius
        self.lifetime = lifetime
        
    def update(self, dt):
        self.position += self.velocity * dt
        self.lifetime -= dt
        
    def is_dead(self):
        if self.lifetime <= 0:
            return True
        if (self.position.x < 0 or self.position.y < 0 or 
            self.position.x > WORLD_WIDTH or self.position.y > WORLD_HEIGHT):
            return True
        return False

class Quest:
    def __init__(self, id, name, description, target_mob, required_kills, exp_reward, min_level=1, quest_type="kill", quest_item=None, required_items=0):
        self.id = id
        self.name = name
        self.description = description
        self.target_mob = target_mob
        self.required_kills = required_kills
        self.current_kills = 0
        self.exp_reward = exp_reward
        self.min_level = min_level
        self.completed = False
        self.quest_type = quest_type  # "kill" or "collect"
        self.quest_item = quest_item  # Item to collect (e.g., "Bandit Head")
        self.required_items = required_items
        self.current_items = 0
        
    def is_complete(self):
        if self.quest_type == "kill":
            return self.current_kills >= self.required_kills and not self.completed
        elif self.quest_type == "collect":
            return self.current_items >= self.required_items and not self.completed
        return False
        
    def get_progress_text(self):
        if self.quest_type == "kill":
            return f"{self.current_kills}/{self.required_kills}"
        elif self.quest_type == "collect":
            return f"{self.current_items}/{self.required_items}"
        return "0/0"
        
    def get_short_description(self):
        if self.quest_type == "kill":
            return f"Slay {self.target_mob} {self.get_progress_text()}"
        elif self.quest_type == "collect":
            return f"Collect {self.quest_item} {self.get_progress_text()}"
        return self.description

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chronicle of Azeria - Multi-Domain Adventure")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 16)
        self.big_font = pygame.font.SysFont("arial", 24, bold=True)
        
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.obstacles = []
        self.portals = []
        self.item_drops = []
        self.community_walls = []
        self.domain_indicators = []
        self.npc_position = pygame.Vector2(WORLD_WIDTH // 2 + 150, WORLD_HEIGHT // 2)
        self.current_level = 1
        self.current_domain = 1
        self.game_time = 0.0
        self.camera = pygame.Vector2(0, 0)
        
        self.quest_id_counter = 1
        self.show_quest_dialog = False
        self.show_quest_log = False
        self.show_inventory = False
        self.show_quest_panel = True  # Track quest panel visibility
        self.selected_quest_index = 0
        self.available_quests = []
        self.completed_quests = []  # Track turn-ins for UI/log
        
        # Add respawn system
        self.enemy_respawn_timers = {}  # Track respawn timers for each enemy type
        self.max_enemies_per_type = 15  # Maximum enemies of each type
        self.enemy_spawn_points = []  # Store spawn points for respawning
        
        # Domain-specific quest chains
        self.domain_quests = {
            1: ["Wolf Hunter", "Snake Slayer", "Bandit Headhunter", "Boar Exterminator"],
            2: ["Wolf Pack Master", "Serpent Hunter", "Bandit Justice", "Boar Champion"],
            3: ["Dragon Slayer", "Demon Hunter", "Ancient Guardian", "Void Walker"],
            4: ["Legendary Beast", "Shadow Assassin", "Crystal Collector", "Time Traveler"],
            5: ["God Slayer", "Reality Bender", "Cosmic Explorer", "Eternal Champion"]
        }
        
        self.generate_world()
        
    def generate_world(self):
        self.enemies.clear()
        self.obstacles.clear()
        self.portals.clear()
        self.community_walls.clear()
        self.domain_indicators.clear()
        self.enemy_spawn_points.clear()
        
        random.seed(42 + self.current_domain)
        
        # Generate community walls around the center
        self.generate_community_walls()
        
        # Generate domain indicator
        self.generate_domain_indicator()
        
        # Generate enemies with spawn points (domain-specific)
        min_level = (self.current_domain - 1) * 5 + 1
        max_level = self.current_domain * 5
        
        # Domain-specific enemy types
        domain_enemies = {
            1: ["Wolf", "Snake", "Boar", "Bandit"],
            2: ["Dire Wolf", "Viper", "Razorback", "Marauder"],
            3: ["Dragon", "Demon", "Ancient", "Voidling"],
            4: ["Legendary Beast", "Shadow", "Crystal", "Time Walker"],
            5: ["God", "Reality Bender", "Cosmic", "Eternal"]
        }
        
        names = domain_enemies.get(self.current_domain, domain_enemies[1])
        
        # Get village center coordinates
        center_x = self.player.community_center.x
        center_y = self.player.community_center.y
        
        # Spawn enemies in forest areas (outside village)
        forest_areas = [
            # Top forest (north of village)
            {"x_range": (center_x - 400, center_x + 400), "y_range": (50, center_y - 200)},
            # Left forest (west of village)
            {"x_range": (50, center_x - 200), "y_range": (center_y - 300, center_y + 300)},
            # Right forest (east of village)
            {"x_range": (center_x + 200, WORLD_WIDTH - 50), "y_range": (center_y - 300, center_y + 300)},
            # Bottom forest (south of village)
            {"x_range": (center_x - 400, center_x + 400), "y_range": (center_y + 200, WORLD_HEIGHT - 50)}
        ]
        
        for _ in range(50):
            name = random.choice(names)
            level = random.randint(min_level, max_level)
            max_hp = random.randint(50 + (self.current_domain - 1) * 30, 140 + (self.current_domain - 1) * 50)
            hp = max_hp
            
            # Choose random forest area
            forest = random.choice(forest_areas)
            px = random.uniform(forest["x_range"][0], forest["x_range"][1])
            py = random.uniform(forest["y_range"][0], forest["y_range"][1])
            
            speed = random.uniform(40, 70)
            exp_reward = 10 + max(0, level - self.player.level) * 2  # Reduced mob EXP
            
            enemy = Mob(name, level, hp, 8 + level * 2, exp_reward, pygame.Vector2(px, py))
            self.enemies.append(enemy)
            
            # Store spawn point for respawning
            self.enemy_spawn_points.append({
                "name": name,
                "position": pygame.Vector2(px, py),
                "level": level,
                "max_hp": max_hp,
                "speed": speed,
                "exp_reward": exp_reward
            })
        
        # Generate obstacles in forest areas (avoid village)
        for _ in range(30):
            obs_type = random.choice(["stone", "tree", "wall"])
            
            # Choose random forest area (same as enemy spawning)
            forest = random.choice(forest_areas)
            px = random.uniform(forest["x_range"][0], forest["x_range"][1])
            py = random.uniform(forest["y_range"][0], forest["y_range"][1])
            
            if obs_type == "stone":
                size = random.randint(20, 40)
            elif obs_type == "tree":
                size = random.randint(30, 50)
            else:  # wall
                size = random.randint(60, 120)
                
            self.obstacles.append({
                "position": pygame.Vector2(px, py),
                "size": size,
                "type": obs_type
            })
        
        # Generate portal to next domain
        if self.current_domain < 5:
            portal_x = random.uniform(WORLD_WIDTH * 0.8, WORLD_WIDTH * 0.9)
            portal_y = random.uniform(WORLD_HEIGHT * 0.8, WORLD_HEIGHT * 0.9)
            self.portals.append({
                "position": pygame.Vector2(portal_x, portal_y),
                "target_domain": self.current_domain + 1,
                "required_level": self.current_domain * 5
            })
            
    def generate_community_walls(self):
        """Generate safe zone village with walls, gates, and NPCs"""
        center_x = self.player.community_center.x
        center_y = self.player.community_center.y
        
        # Village dimensions
        village_width = 400
        village_height = 300
        
        # Generate rectangular walls with gates
        self.generate_safe_zone_walls(center_x, center_y, village_width, village_height)
        
        # Generate village buildings and NPCs
        self.generate_village_buildings_and_npcs(center_x, center_y, village_width, village_height)
        
        # Generate central portal
        self.generate_central_portal(center_x, center_y)
        
        # Generate respawn point
        self.generate_respawn_point(center_x, center_y)
            
    def generate_domain_indicator(self):
        """Generate domain indicator at the top of the world"""
        domain_names = {
            1: "Village Domain",
            2: "Forest Domain", 
            3: "Mountain Domain",
            4: "Shadow Domain",
            5: "Cosmic Domain"
        }
        
        self.domain_indicators.append({
            "position": pygame.Vector2(WORLD_WIDTH // 2, 50),
            "name": domain_names.get(self.current_domain, "Unknown Domain"),
            "level": self.current_domain
        })
        
    def generate_new_village_layout(self, center_x, center_y, village_width, village_height):
        """Generate new village layout matching the image"""
        # Guild House at top center (rectangular)
        guild_x = center_x
        guild_y = center_y - village_height // 3
        self.community_walls.append({
            "position": pygame.Vector2(guild_x, guild_y),
            "size": 35,
            "type": "guild_house"
        })
        
        # Guild Quest area below guild house on main path
        quest_x = center_x
        quest_y = center_y - village_height // 6
        self.community_walls.append({
            "position": pygame.Vector2(quest_x, quest_y),
            "size": 25,
            "type": "guild_quest"
        })
        
        # NPC Quest on the left curved wall (halfway down)
        npc_x = center_x - village_width // 3
        npc_y = center_y
        self.community_walls.append({
            "position": pygame.Vector2(npc_x, npc_y),
            "size": 20,
            "type": "npc_quest"
        })
        
        # Fountain in the very center
        fountain_x = center_x
        fountain_y = center_y
        self.community_walls.append({
            "position": pygame.Vector2(fountain_x, fountain_y),
            "size": 30,
            "type": "fountain"
        })
        
        # Four portals on the right curved wall in diagonal arrangement
        portal_start_x = center_x + village_width // 3
        portal_start_y = center_y - village_height // 4
        portal_spacing_x = 20
        portal_spacing_y = 15
        
        for i in range(4):
            portal_x = portal_start_x + (i * portal_spacing_x)
            portal_y = portal_start_y + (i * portal_spacing_y)
            self.community_walls.append({
                "position": pygame.Vector2(portal_x, portal_y),
                "size": 20,
                "type": "portal",
                "portal_id": i + 1
            })
        
        # Update NPC position to be in guild house
        self.npc_position = pygame.Vector2(guild_x, guild_y)
        
    def generate_npc_quest_only(self, center_x, center_y):
        """Generate only the NPC quest - no walls or other structures"""
        # NPC Quest at the center
        npc_x = center_x
        npc_y = center_y
        self.community_walls.append({
            "position": pygame.Vector2(npc_x, npc_y),
            "size": 25,
            "type": "npc_quest"
        })
        
        # Update NPC position to be at the quest location
        self.npc_position = pygame.Vector2(npc_x, npc_y)
        
    def generate_safe_zone_walls(self, center_x, center_y, village_width, village_height):
        """Generate U-shaped walls with two gates at bottom"""
        wall_thickness = 20
        
        # Top wall (single rectangle)
        self.community_walls.append({
            "position": pygame.Vector2(center_x, center_y - village_height // 2),
            "width": village_width,
            "height": wall_thickness,
            "type": "wall_rect"
        })
        
        # Left wall (single rectangle)
        self.community_walls.append({
            "position": pygame.Vector2(center_x - village_width // 2, center_y),
            "width": wall_thickness,
            "height": village_height,
            "type": "wall_rect"
        })
        
        # Right wall (single rectangle)
        self.community_walls.append({
            "position": pygame.Vector2(center_x + village_width // 2, center_y),
            "width": wall_thickness,
            "height": village_height,
            "type": "wall_rect"
        })
        
        # U-shaped bottom structure
        u_height = village_height // 2
        u_width = village_width // 2
        
        # Left U wall (vertical)
        self.community_walls.append({
            "position": pygame.Vector2(center_x - u_width // 2, center_y + u_height // 2),
            "width": wall_thickness,
            "height": u_height,
            "type": "wall_rect"
        })
        
        # Right U wall (vertical)
        self.community_walls.append({
            "position": pygame.Vector2(center_x + u_width // 2, center_y + u_height // 2),
            "width": wall_thickness,
            "height": u_height,
            "type": "wall_rect"
        })
        
        # Bottom U wall (horizontal)
        self.community_walls.append({
            "position": pygame.Vector2(center_x, center_y + u_height),
            "width": u_width,
            "height": wall_thickness,
            "type": "wall_rect"
        })
        
        # Gate labels
        gate_width = 60
        left_gate_x = center_x - u_width // 2 - gate_width // 2
        right_gate_x = center_x + u_width // 2 + gate_width // 2
        
        # Left gate
        self.community_walls.append({
            "position": pygame.Vector2(left_gate_x, center_y + u_height),
            "width": gate_width,
            "height": 10,
            "type": "gate_label"
        })
        
        # Right gate
        self.community_walls.append({
            "position": pygame.Vector2(right_gate_x, center_y + u_height),
            "width": gate_width,
            "height": 10,
            "type": "gate_label"
        })
        
    def generate_gate_guards(self, left_gate_x, right_gate_x, gate_y):
        """Generate gate guards at the gate pillars"""
        # Left gate guard
        self.community_walls.append({
            "position": pygame.Vector2(left_gate_x - 30, gate_y),
            "size": 15,
            "type": "guard"
        })
        
        # Right gate guard
        self.community_walls.append({
            "position": pygame.Vector2(right_gate_x + 30, gate_y),
            "size": 15,
            "type": "guard"
        })
        
    def generate_village_buildings_and_npcs(self, center_x, center_y, village_width, village_height):
        """Generate village buildings and NPCs based on new layout"""
        # Respawn Area (top left quadrant)
        respawn_x = center_x - village_width // 3
        respawn_y = center_y - village_height // 3
        self.community_walls.append({
            "position": pygame.Vector2(respawn_x, respawn_y),
            "width": 80,
            "height": 60,
            "type": "respawn_area"
        })
        
        # Guild House (top right quadrant)
        guild_x = center_x + village_width // 3
        guild_y = center_y - village_height // 3
        self.community_walls.append({
            "position": pygame.Vector2(guild_x, guild_y),
            "width": 100,
            "height": 80,
            "type": "guild_house"
        })
        
        # Guild Quest (inside guild house)
        guild_quest_x = guild_x
        guild_quest_y = guild_y + 20
        self.community_walls.append({
            "position": pygame.Vector2(guild_quest_x, guild_quest_y),
            "width": 60,
            "height": 30,
            "type": "guild_quest"
        })
        
        # NPC Trainer (outside left gate)
        u_width = village_width // 2
        npc_trainer_x = center_x - u_width // 2 - 40
        npc_trainer_y = center_y + village_height // 4
        self.community_walls.append({
            "position": pygame.Vector2(npc_trainer_x, npc_trainer_y),
            "width": 40,
            "height": 20,
            "type": "npc_trainer"
        })
        
        # NPC Quest (outside right gate)
        npc_quest_x = center_x + u_width // 2 + 40
        npc_quest_y = center_y + village_height // 4
        self.community_walls.append({
            "position": pygame.Vector2(npc_quest_x, npc_quest_y),
            "width": 40,
            "height": 20,
            "type": "npc_quest"
        })
        
        # Update main NPC position to guild house
        self.npc_position = pygame.Vector2(guild_x, guild_y)
        
        # Update respawn position to respawn area
        self.player.graveyard_position = pygame.Vector2(respawn_x, respawn_y)
        
    def generate_central_portal(self, center_x, center_y):
        """Generate central portal in U-shaped area"""
        # Portal in center of U-shaped area
        portal_x = center_x
        portal_y = center_y + 50  # Below center, in U-shaped area
        self.community_walls.append({
            "position": pygame.Vector2(portal_x, portal_y),
            "size": 30,
            "type": "central_portal"
        })
        
    def generate_respawn_point(self, center_x, center_y):
        """Generate respawn point on the left side"""
        respawn_x = center_x - 80
        respawn_y = center_y
        self.community_walls.append({
            "position": pygame.Vector2(respawn_x, respawn_y),
            "size": 25,
            "type": "respawn_point"
        })
        
        # Update graveyard position to respawn point
        self.player.graveyard_position = pygame.Vector2(respawn_x, respawn_y)
        
    def generate_main_path(self, center_x, center_y, village_height):
        """Generate main path running vertically through the center"""
        path_width = 40
        path_length = village_height
        
        # Main path from top to bottom, going over the fountain
        for y in range(int(center_y - path_length // 2), int(center_y + path_length // 2), 15):
            self.community_walls.append({
                "position": pygame.Vector2(center_x, y),
                "size": path_width // 2,
                "type": "main_path"
            })
        
    def generate_village_houses(self, center_x, center_y, village_width, village_height):
        """Generate houses in the village"""
        # House positions (avoiding center area for guild house)
        house_positions = [
            (center_x - 80, center_y - 60),   # Top left
            (center_x + 80, center_y - 60),   # Top right
            (center_x - 80, center_y + 60),   # Bottom left
            (center_x + 80, center_y + 60),   # Bottom right
            (center_x - 120, center_y),       # Left
            (center_x + 120, center_y),       # Right
        ]
        
        for i, (x, y) in enumerate(house_positions):
            self.community_walls.append({
                "position": pygame.Vector2(x, y),
                "size": 25,
                "type": "house",
                "house_id": i + 1
            })
            
    def generate_guild_house(self, center_x, center_y):
        """Generate guild house in the center of village"""
        self.community_walls.append({
            "position": pygame.Vector2(center_x, center_y),
            "size": 35,
            "type": "guild_house"
        })
        
        # Update NPC position to be in guild house
        self.npc_position = pygame.Vector2(center_x, center_y)
        
    def generate_main_gate(self, center_x, gate_y):
        """Generate main gate at the bottom of village"""
        gate_width = 60
        gate_height = 30
        
        # Gate pillars
        self.community_walls.append({
            "position": pygame.Vector2(center_x - gate_width // 2, gate_y),
            "size": 15,
            "type": "gate_pillar"
        })
        
        self.community_walls.append({
            "position": pygame.Vector2(center_x + gate_width // 2, gate_y),
            "size": 15,
            "type": "gate_pillar"
        })
        
        # Gate arch
        self.community_walls.append({
            "position": pygame.Vector2(center_x, gate_y - 10),
            "size": 20,
            "type": "gate_arch"
        })
        
    def generate_village_roads(self, center_x, center_y, village_width, village_height):
        """Generate roads in and around the village"""
        # Main road from gate to center
        road_length = village_height // 2
        for y in range(int(center_y - road_length), int(center_y + road_length), 15):
            self.community_walls.append({
                "position": pygame.Vector2(center_x, y),
                "size": 8,
                "type": "road"
            })
        
        # Horizontal road through center
        road_width = village_width // 2
        for x in range(int(center_x - road_width), int(center_x + road_width), 15):
            self.community_walls.append({
                "position": pygame.Vector2(x, center_y),
                "size": 8,
                "type": "road"
            })
        
        # Road outside village leading to forestssssss
        outside_road_length = 200
        for y in range(int(center_y - village_height // 2 - 50), int(center_y - village_height // 2 - 50 - outside_road_length), -15):
            self.community_walls.append({
                "position": pygame.Vector2(center_x, y),
                "size": 8,
                "type": "road"
            })
            
    def generate_quests_for_level(self, domain):
        quests = []
        min_level = (domain - 1) * 5 + 1
        max_level = domain * 5
        
        quest_templates = {
            1: [
                {"name": "Wolf Hunter", "desc": "Slay {count} Wolves in the forest", "target": "Wolf", "count": 5, "exp": 200, "type": "kill"},
                {"name": "Snake Slayer", "desc": "Defeat {count} Snakes", "target": "Snake", "count": 3, "exp": 150, "type": "kill"},
                {"name": "Bandit Headhunter", "desc": "Slay {count} Bandits and collect their heads", "target": "Bandit", "count": 6, "exp": 250, "type": "collect", "item": "Bandit Head", "items": 6},
                {"name": "Boar Exterminator", "desc": "Eliminate {count} Boars", "target": "Boar", "count": 4, "exp": 180, "type": "kill"},
            ],
            2: [
                {"name": "Wolf Pack Master", "desc": "Slay {count} Dire Wolves", "target": "Dire Wolf", "count": 8, "exp": 400, "type": "kill"},
                {"name": "Serpent Hunter", "desc": "Defeat {count} Vipers", "target": "Viper", "count": 6, "exp": 300, "type": "kill"},
                {"name": "Bandit Justice", "desc": "Defeat {count} Marauders and collect their heads", "target": "Marauder", "count": 10, "exp": 500, "type": "collect", "item": "Bandit Head", "items": 10},
                {"name": "Boar Champion", "desc": "Eliminate {count} Razorbacks", "target": "Razorback", "count": 7, "exp": 350, "type": "kill"},
            ],
            3: [
                {"name": "Dragon Slayer", "desc": "Slay {count} Dragons", "target": "Dragon", "count": 3, "exp": 800, "type": "kill"},
                {"name": "Demon Hunter", "desc": "Defeat {count} Demons", "target": "Demon", "count": 5, "exp": 600, "type": "kill"},
                {"name": "Ancient Guardian", "desc": "Defeat {count} Ancients and collect relics", "target": "Ancient", "count": 4, "exp": 700, "type": "collect", "item": "Ancient Relic", "items": 4},
                {"name": "Void Walker", "desc": "Eliminate {count} Voidlings", "target": "Voidling", "count": 6, "exp": 500, "type": "kill"},
            ],
            4: [
                {"name": "Legendary Beast", "desc": "Slay {count} Legendary Beasts", "target": "Legendary Beast", "count": 2, "exp": 1200, "type": "kill"},
                {"name": "Shadow Assassin", "desc": "Defeat {count} Shadows", "target": "Shadow", "count": 4, "exp": 1000, "type": "kill"},
                {"name": "Crystal Collector", "desc": "Collect {count} Crystals", "target": "Crystal", "count": 5, "exp": 900, "type": "collect", "item": "Crystal", "items": 5},
                {"name": "Time Traveler", "desc": "Defeat {count} Time Walkers", "target": "Time Walker", "count": 3, "exp": 1100, "type": "kill"},
            ],
            5: [
                {"name": "God Slayer", "desc": "Slay {count} Gods", "target": "God", "count": 1, "exp": 2000, "type": "kill"},
                {"name": "Reality Bender", "desc": "Defeat {count} Reality Benders", "target": "Reality Bender", "count": 2, "exp": 1800, "type": "kill"},
                {"name": "Cosmic Explorer", "desc": "Defeat {count} Cosmic beings", "target": "Cosmic", "count": 3, "exp": 1600, "type": "kill"},
                {"name": "Eternal Champion", "desc": "Defeat {count} Eternal beings", "target": "Eternal", "count": 2, "exp": 1900, "type": "kill"},
            ]
        }
        
        templates = quest_templates.get(domain, quest_templates[1])
        
        for template in templates:
            if template["type"] == "kill":
                quest = Quest(
                    id=self.quest_id_counter,
                    name=template["name"],
                    description=template["desc"].format(count=template["count"]),
                    target_mob=template["target"],
                    required_kills=template["count"],
                    exp_reward=template["exp"],
                    min_level=min_level,
                    quest_type="kill"
                )
            else:  # collect
                quest = Quest(
                    id=self.quest_id_counter,
                    name=template["name"],
                    description=template["desc"].format(count=template["count"]),
                    target_mob=template["target"],
                    required_kills=template["count"],
                    exp_reward=template["exp"],
                    min_level=min_level,
                    quest_type="collect",
                    quest_item=template["item"],
                    required_items=template["items"]
                )
            
            quests.append(quest)
            self.quest_id_counter += 1
        
        return quests
        
    def update(self, dt):
        """Update game state"""
        self.game_time += dt
        
        # Update hearthstone cooldown
        if self.player.hearthstone_cooldown > 0:
            self.player.hearthstone_cooldown -= dt
            if self.player.hearthstone_cooldown < 0:
                self.player.hearthstone_cooldown = 0.0
            
        # Handle death and respawning
        if self.player.is_dead:
            self.player.death_timer -= dt
            if self.player.death_timer <= 0:
                self.player.respawn()
            return  # Don't process other updates while dead
        
        # Update item drops
        for drop in list(self.item_drops):
            drop.update(dt)
            if drop.is_expired():
                self.item_drops.remove(drop)
        
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Player movement (only if not dead)
        if not self.player.is_dead:
            movement = pygame.Vector2(0, 0)
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                movement.y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                movement.y += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                movement.x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                movement.x += 1
                
            if movement.length() > 0:
                movement.normalize_ip()
                self.player.position += movement * self.player.speed * dt
                
            # Clamp player to world bounds
            self.player.position.x = max(self.player.size, min(self.player.position.x, WORLD_WIDTH - self.player.size))
            self.player.position.y = max(self.player.size, min(self.player.position.y, WORLD_HEIGHT - self.player.size))
            
            # Check collision with village structures (walls, houses, guild house, gate)
            for wall in self.community_walls:
                if wall["type"] in ["wall", "wall_rect", "house", "guild_house", "gate_pillar", "gate_arch"]:
                    wall_pos = wall["position"]
                    player_pos = self.player.position
                    
                    # Skip collision check for gates, main path, and NPCs (allow passage)
                    if wall["type"] in ["gate_arch", "main_path", "guard", "blacksmith", "traveler", "villager", "npc_trainer", "gate_label"]:
                        continue
                    
                    # Handle rectangular walls
                    if wall["type"] == "wall_rect":
                        width = wall.get("width", 20)
                        height = wall.get("height", 20)
                        wall_rect = pygame.Rect(wall_pos.x - width // 2, wall_pos.y - height // 2, width, height)
                        player_rect = pygame.Rect(player_pos.x - self.player.size, player_pos.y - self.player.size, 
                                                self.player.size * 2, self.player.size * 2)
                        
                        if wall_rect.colliderect(player_rect):
                            # Push player away from rectangular wall
                            if player_pos.x < wall_rect.left:
                                self.player.position.x = wall_rect.left - self.player.size
                            elif player_pos.x > wall_rect.right:
                                self.player.position.x = wall_rect.right + self.player.size
                            elif player_pos.y < wall_rect.top:
                                self.player.position.y = wall_rect.top - self.player.size
                            elif player_pos.y > wall_rect.bottom:
                                self.player.position.y = wall_rect.bottom + self.player.size
                    else:
                        # Handle circular walls (legacy)
                        wall_size = wall.get("size", 20)
                        distance = (player_pos - wall_pos).length()
                        if distance < self.player.size + wall_size:
                            # Push player away from wall
                            if distance > 0:
                                push_direction = (player_pos - wall_pos).normalize()
                                self.player.position = wall_pos + push_direction * (self.player.size + wall_size)
                            else:
                                # If player is exactly on wall, push in a random direction
                                self.player.position += pygame.Vector2(1, 0) * (self.player.size + wall_size)
            
            # Check collision with obstacles
            for obstacle in self.obstacles:
                obstacle_pos = obstacle["position"]
                obstacle_size = obstacle["size"]
                player_pos = self.player.position
                
                distance = (player_pos - obstacle_pos).length()
                if distance < self.player.size + obstacle_size:
                    # Push player away from obstacle
                    if distance > 0:
                        push_direction = (player_pos - obstacle_pos).normalize()
                        self.player.position = obstacle_pos + push_direction * (self.player.size + obstacle_size)
                    else:
                        # If player is exactly on obstacle, push in a random direction
                        self.player.position += pygame.Vector2(1, 0) * (self.player.size + obstacle_size)
        
        # Check item drop collection
        for drop in list(self.item_drops):
            if (self.player.position - drop.position).length() < 30:
                if drop.item_type == "gold":
                    amount = int(drop.item_name.split()[0])
                    self.player.inventory["Gold"] += amount
                    print(f"Collected {amount} gold!")
                else:
                    self.player.quest_items[drop.item_name] += 1
                    print(f"Collected {drop.item_name}!")
                self.item_drops.remove(drop)
        
        # Shooting mechanics - ONLY if not in any dialog
        if not self.show_quest_dialog and not self.show_quest_log and not self.show_inventory:
            mouse_pressed = pygame.mouse.get_pressed()
            current_time = self.game_time
            
            if mouse_pressed[0] and current_time - self.player.last_shot_time >= self.player.shoot_cooldown:
                self.shoot_at_target()
                self.player.last_shot_time = current_time
                
        # Update bullets
        for bullet in list(self.bullets):
            bullet.position += bullet.velocity * dt
            bullet.lifetime -= dt
            
            # Remove bullets that are too old or out of bounds
            if (bullet.lifetime <= 0 or 
                bullet.position.x < 0 or bullet.position.x > WORLD_WIDTH or
                bullet.position.y < 0 or bullet.position.y > WORLD_HEIGHT):
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                    
        # Update enemies with new AI
        for enemy in list(self.enemies):
            if enemy.is_dead():
                self.handle_enemy_death(enemy)
                self.enemies.remove(enemy)
                continue
                
            # Update enemy AI
            enemy.update_ai(dt, self.player.position, self.player.level)
            
            # Check enemy collision with obstacles and walls
            for obstacle in self.obstacles:
                obstacle_pos = obstacle["position"]
                obstacle_size = obstacle["size"]
                enemy_pos = enemy.position
                
                distance = (enemy_pos - obstacle_pos).length()
                if distance < enemy.size + obstacle_size:
                    # Push enemy away from obstacle
                    if distance > 0:
                        push_direction = (enemy_pos - obstacle_pos).normalize()
                        enemy.position = obstacle_pos + push_direction * (enemy.size + obstacle_size)
                    else:
                        # If enemy is exactly on obstacle, push in a random direction
                        enemy.position += pygame.Vector2(1, 0) * (enemy.size + obstacle_size)
            
            # Check enemy collision with village structures
            for wall in self.community_walls:
                if wall["type"] in ["wall", "wall_rect", "house", "guild_house", "gate_pillar", "bank", "respawn_point", "respawn_area"]:
                    wall_pos = wall["position"]
                    enemy_pos = enemy.position
                    
                    # Handle rectangular walls
                    if wall["type"] == "wall_rect":
                        width = wall.get("width", 20)
                        height = wall.get("height", 20)
                        wall_rect = pygame.Rect(wall_pos.x - width // 2, wall_pos.y - height // 2, width, height)
                        enemy_rect = pygame.Rect(enemy_pos.x - enemy.size, enemy_pos.y - enemy.size, 
                                               enemy.size * 2, enemy.size * 2)
                        
                        if wall_rect.colliderect(enemy_rect):
                            # Push enemy away from rectangular wall
                            if enemy_pos.x < wall_rect.left:
                                enemy.position.x = wall_rect.left - enemy.size
                            elif enemy_pos.x > wall_rect.right:
                                enemy.position.x = wall_rect.right + enemy.size
                            elif enemy_pos.y < wall_rect.top:
                                enemy.position.y = wall_rect.top - enemy.size
                            elif enemy_pos.y > wall_rect.bottom:
                                enemy.position.y = wall_rect.bottom + enemy.size
                    else:
                        # Handle circular walls (legacy)
                        wall_size = wall.get("size", 20)
                        distance = (enemy_pos - wall_pos).length()
                        if distance < enemy.size + wall_size:
                            # Push enemy away from wall
                            if distance > 0:
                                push_direction = (enemy_pos - wall_pos).normalize()
                                enemy.position = wall_pos + push_direction * (enemy.size + wall_size)
                            else:
                                # If enemy is exactly on wall, push in a random direction
                                enemy.position += pygame.Vector2(1, 0) * (enemy.size + wall_size)
            
            # Check if enemy attacks player
            if not self.player.is_dead:
                distance_to_player = (enemy.position - self.player.position).length()
                if distance_to_player < enemy.size + self.player.size:
                    # Enemy attacks player
                    self.player.hp -= enemy.attack * dt
                    if self.player.hp <= 0:
                        self.player.die()
                    
        # Check bullet collisions
        for bullet in list(self.bullets):
            for enemy in list(self.enemies):
                if (bullet.position - enemy.position).length() < enemy.size + bullet.radius:
                    enemy.take_damage(40)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
                    
        # Handle enemy respawning
        self.handle_enemy_respawning(dt)
                    
        # Check portal interaction
        for portal in self.portals:
            if (self.player.position - portal["position"]).length() < 30:
                required_level = portal["required_level"]
                if self.player.level >= required_level:
                    # Check if all quests are completed
                    available_quests = [q for q in self.player.active_quests.values() if not q.completed]
                    if not available_quests:
                        self.current_domain = portal["target_domain"]
                        self.player.current_domain = self.current_domain
                        self.player.position = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
                        self.generate_world()
                        
                        # Generate new quests for the new domain
                        new_quests = self.generate_quests_for_level(self.current_domain)
                        for quest in new_quests:
                            self.player.active_quests[quest.name] = quest
                        print(f"Welcome to Domain {self.current_domain}!")
                        break
                    else:
                        print("Complete all quests before entering the next domain!")
                else:
                    print(f"You need level {required_level} to enter this domain!")
                        
    def shoot_at_target(self):
        """Shoot at the nearest enemy within range"""
        mouse_pos = pygame.mouse.get_pos()
        world_mouse_pos = pygame.Vector2(
            mouse_pos[0] + self.camera.x,
            mouse_pos[1] + self.camera.y
        )
        
        # Find the nearest enemy within shooting range (150 pixels)
        nearest_enemy = None
        nearest_distance = float('inf')
        shooting_range = 150  # Maximum shooting range
        
        for enemy in self.enemies:
            distance = (enemy.position - self.player.position).length()
            if distance <= shooting_range:  # Only consider enemies within range
                # Target priority: Red > Orange > Yellow > Green > Gray
                priority = self.get_target_priority(enemy)
                adjusted_distance = distance / (1 + priority * 0.1)  # Prefer higher priority
                
                if adjusted_distance < nearest_distance:
                    nearest_enemy = enemy
                    nearest_distance = adjusted_distance
        
        if nearest_enemy:
            # Shoot at the nearest enemy within range
            direction = nearest_enemy.position - self.player.position
            if direction.length() > 0:
                direction.normalize_ip()
                bullet = Bullet(self.player.position.copy(), direction * 400, 3, 2.0)
                self.bullets.append(bullet)
        else:
            # Don't shoot if no enemy is within range
            print("No enemies within shooting range!")
                
    def get_target_priority(self, enemy):
        """Get target priority based on difficulty color (higher number = higher priority)"""
        color = enemy.get_difficulty_color(self.player.level)
        if color == RED:
            return 5  # Highest priority
        elif color == ORANGE:
            return 4
        elif color == YELLOW:
            return 3
        elif color == GREEN:
            return 2
        elif color == GRAY:
            return 1  # Lowest priority
        else:
            return 0
        
    def handle_enemy_death(self, enemy):
        # Calculate EXP based on level difference and chance
        chance = enemy.exp_chance(self.player.level)
        exp_gained = False
        
        if random.random() <= chance:
            base = 25 + max(0, enemy.level - self.player.level) * 5
            self.player.gain_exp(base)
            exp_gained = True
            
        # Update quest progress - ALWAYS update when enemy dies, regardless of EXP gain
        enemy_name_lower = enemy.name.lower()
        
        if enemy_name_lower == "wolf":
            self.player.wolves_killed += 1
        elif enemy_name_lower == "bear":
            self.player.bears_killed += 1
        elif enemy_name_lower == "snake":
            self.player.snakes_killed += 1
        elif enemy_name_lower == "boar":
            self.player.boars_killed += 1
        elif enemy_name_lower == "bandit":
            self.player.bandits_killed += 1
            
        # Update ALL quests that target this enemy type - ALWAYS update
        quest_updated = False
        for quest in self.player.active_quests.values():
            if quest.target_mob.lower() == enemy_name_lower and not quest.completed:
                quest.current_kills += 1
                quest_updated = True
                print(f"Quest progress: {quest.name} - {quest.get_progress_text()}")
                
                # For collect quests, also increase item count
                if quest.quest_type == "collect" and quest.quest_item:
                    if random.random() < 0.7:  # 70% chance to get quest item
                        quest.current_items += 1
                        self.player.quest_items[quest.quest_item] += 1
                        print(f"Found {quest.quest_item}!")
                        
                        # Create visual item drop
                        drop = ItemDrop(enemy.position.copy(), quest.quest_item, "quest")
                        self.item_drops.append(drop)
        
        # Print confirmation of enemy death and quest update
        if exp_gained:
            print(f"Killed {enemy.name} (Level {enemy.level}) - Gained EXP!")
        else:
            print(f"Killed {enemy.name} (Level {enemy.level}) - No EXP (too low level)")
            
        if quest_updated:
            print(f"Quest progress updated for {enemy.name}!")
        else:
            print(f"No active quests for {enemy.name}")
                    
        # Random loot drop
        if random.random() < 0.4:
            gold_drop = random.randint(5, 20)
            self.player.inventory["Gold"] += gold_drop
            print(f"Found {gold_drop} gold!")
            
            # Create visual gold drop
            drop = ItemDrop(enemy.position.copy(), f"{gold_drop} Gold", "gold")
            self.item_drops.append(drop)
            
        # Quest item drops (independent of quest progress)
        if enemy.name.lower() == "bandit" and random.random() < 0.6:
            self.player.quest_items["Bandit Head"] += 1
            print("Found Bandit Head!")
            
            # Create visual item drop
            drop = ItemDrop(enemy.position.copy(), "Bandit Head", "quest")
            self.item_drops.append(drop)
            
        elif enemy.name.lower() == "wolf" and random.random() < 0.5:
            self.player.quest_items["Wolf Fang"] += 1
            print("Found Wolf Fang!")
            
            # Create visual item drop
            drop = ItemDrop(enemy.position.copy(), "Wolf Fang", "quest")
            self.item_drops.append(drop)
        elif enemy.name.lower() == "snake" and random.random() < 0.4:
            self.player.quest_items["Snake Venom"] += 1
            print("Found Snake Venom!")
        elif enemy.name.lower() == "boar" and random.random() < 0.5:
            self.player.quest_items["Boar Tusk"] += 1
            print("Found Boar Tusk!")
            
    def handle_enemy_respawning(self, dt):
        """Handle enemy respawning"""
        # Count current enemies by type
        enemy_counts = {}
        for enemy in self.enemies:
            enemy_counts[enemy.name] = enemy_counts.get(enemy.name, 0) + 1
        
        # Check respawn timers and spawn new enemies
        for spawn_point in self.enemy_spawn_points:
            enemy_name = spawn_point["name"]
            current_count = enemy_counts.get(enemy_name, 0)
            
            if current_count < self.max_enemies_per_type:
                # Check if it's time to respawn
                respawn_key = f"{enemy_name}_{spawn_point['position']}"
                if respawn_key not in self.enemy_respawn_timers:
                    # Start respawn timer
                    self.enemy_respawn_timers[respawn_key] = random.uniform(5.0, 10.0)
                else:
                    self.enemy_respawn_timers[respawn_key] -= dt
                    
                    if self.enemy_respawn_timers[respawn_key] <= 0:
                        # Spawn new enemy
                        new_enemy = Mob(
                            spawn_point["name"],
                            spawn_point["level"],
                            spawn_point["max_hp"],
                            8 + spawn_point["level"] * 2,
                            spawn_point["exp_reward"],
                            spawn_point["position"].copy()
                        )
                        self.enemies.append(new_enemy)
                        del self.enemy_respawn_timers[respawn_key]
                    
    def render(self):
        """Render the game"""
        # Clear screen with white background (will be covered by UI elements)
        self.screen.fill(WHITE)
        
        # Update camera to follow player
        self.camera.x = self.player.position.x - WINDOW_WIDTH // 2
        self.camera.y = self.player.position.y - WINDOW_HEIGHT // 2
        
        # Clamp camera to world bounds
        self.camera.x = max(0, min(self.camera.x, WORLD_WIDTH - WINDOW_WIDTH))
        self.camera.y = max(0, min(self.camera.y, WORLD_HEIGHT - WINDOW_HEIGHT))
        
        # Draw community walls
        for wall in self.community_walls:
            self.draw_wall(wall)
            
        # Draw domain indicator
        for indicator in self.domain_indicators:
            self.draw_domain_indicator(indicator)
            
        # Draw graveyard
        self.draw_graveyard()
        
        # Draw forest indicators
        self.draw_forest_areas()
            
        # Draw obstacles
        for obstacle in self.obstacles:
            self.draw_obstacle(obstacle)
            
        # Draw portals
        for portal in self.portals:
            self.draw_portal(portal)
            
        # Draw enemies
        for enemy in self.enemies:
            self.draw_enemy(enemy)
            
        # Draw bullets
        for bullet in self.bullets:
            self.draw_bullet(bullet)
            
        # Draw item drops
        for drop in self.item_drops:
            self.draw_item_drop(drop)
            
        # Draw player
        self.draw_player()
        
        # Draw NPC
        self.draw_npc()
        
        # Draw UI
        self.draw_ui()
        
        # Draw dialogs (on top of everything)
        if self.show_quest_dialog:
            self.draw_quest_dialog()
            
        if self.show_quest_log:
            self.draw_quest_log()
            
        if self.show_inventory:
            self.draw_inventory()
            
        # Draw death screen
        if self.player.is_dead:
            self.draw_death_screen()
            
    def draw_grid(self):
        start_x = int(self.camera.x // 64) * 64
        start_y = int(self.camera.y // 64) * 64
        
        for x in range(start_x, int(self.camera.x + WINDOW_WIDTH) + 64, 64):
            for y in range(start_y, int(self.camera.y + WINDOW_HEIGHT) + 64, 64):
                rect = pygame.Rect(int(x - self.camera.x), int(y - self.camera.y), 64, 64)
                color = (0, 80, 0) if ((x // 64 + y // 64) % 2) == 0 else (0, 100, 0)
                pygame.draw.rect(self.screen, color, rect)
                
    def draw_player(self):
        """Draw the player character"""
        x = int(self.player.position.x - self.camera.x)
        y = int(self.player.position.y - self.camera.y)
        
        # Draw player body
        pygame.draw.circle(self.screen, BLUE, (x, y), self.player.size)
        pygame.draw.circle(self.screen, BLACK, (x, y), self.player.size, 2)
        
        # Draw player name and level
        name_text = self.font.render(f"Player Lv{self.player.level}", True, WHITE)
        self.screen.blit(name_text, (x - name_text.get_width() // 2, y - self.player.size - 25))
        
        # Draw HP bar
        hp_ratio = self.player.hp / max(1, self.player.max_hp)
        hp_width = 40
        hp_height = 6
        
        hp_bg = pygame.Rect(x - hp_width // 2, y - self.player.size - 15, hp_width, hp_height)
        hp_fill = pygame.Rect(x - hp_width // 2, y - self.player.size - 15, int(hp_width * hp_ratio), hp_height)
        
        pygame.draw.rect(self.screen, BLACK, hp_bg)
        pygame.draw.rect(self.screen, GREEN, hp_fill)
        
        # Draw shooting range indicator (when left clicking)
        if pygame.mouse.get_pressed()[0]:  # Left mouse button
            pygame.draw.circle(self.screen, (255, 255, 0, 100), (x, y), 150, 3)
            
    def draw_enemy(self, enemy):
        x = int(enemy.position.x - self.camera.x)
        y = int(enemy.position.y - self.camera.y)
        
        # Draw enemy body
        color = enemy.get_difficulty_color(self.player.level)
        pygame.draw.circle(self.screen, color, (x, y), enemy.size)
        pygame.draw.circle(self.screen, BLACK, (x, y), enemy.size, 2)
        
        # Draw enemy name and level
        name_text = self.font.render(f"{enemy.name} Lv{enemy.level}", True, WHITE)
        self.screen.blit(name_text, (x - name_text.get_width() // 2, y - enemy.size - 25))
        
        # Draw HP bar
        hp_ratio = enemy.hp / max(1, enemy.max_hp)
        hp_width = 30
        hp_height = 4
        
        hp_bg = pygame.Rect(x - hp_width // 2, y - enemy.size - 15, hp_width, hp_height)
        hp_fill = pygame.Rect(x - hp_width // 2, y - enemy.size - 15, int(hp_width * hp_ratio), hp_height)
        
        pygame.draw.rect(self.screen, BLACK, hp_bg)
        pygame.draw.rect(self.screen, color, hp_fill)
        
    def draw_bullet(self, bullet):
        x = int(bullet.position.x - self.camera.x)
        y = int(bullet.position.y - self.camera.y)
        pygame.draw.circle(self.screen, YELLOW, (x, y), bullet.radius)
        
    def draw_item_drop(self, drop):
        """Draw item drops on the ground"""
        x = int(drop.position.x - self.camera.x)
        y = int(drop.position.y - self.camera.y + drop.bob_offset)
        
        # Draw item shape
        color = drop.get_color()
        if drop.item_type == "quest":
            # Draw diamond shape for quest items
            points = [
                (x, y - 8),
                (x + 8, y),
                (x, y + 8),
                (x - 8, y)
            ]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, WHITE, points, 2)
        else:
            # Draw circle for gold
            pygame.draw.circle(self.screen, color, (x, y), 6)
            pygame.draw.circle(self.screen, WHITE, (x, y), 6, 2)
        
        # Draw item label
        label_text = self.font.render(drop.item_name, True, WHITE)
        self.screen.blit(label_text, (x - label_text.get_width() // 2, y - 20))
        
        # Draw lifetime indicator
        lifetime_ratio = drop.lifetime / 10.0
        lifetime_width = 20
        lifetime_height = 2
        
        lifetime_bg = pygame.Rect(x - lifetime_width // 2, y + 15, lifetime_width, lifetime_height)
        lifetime_fill = pygame.Rect(x - lifetime_width // 2, y + 15, int(lifetime_width * lifetime_ratio), lifetime_height)
        
        pygame.draw.rect(self.screen, BLACK, lifetime_bg)
        pygame.draw.rect(self.screen, GREEN, lifetime_fill)
        
    def draw_obstacle(self, obstacle):
        x = int(obstacle["position"].x - self.camera.x)
        y = int(obstacle["position"].y - self.camera.y)
        size = obstacle["size"]
        
        if obstacle["type"] == "stone":
            color = GRAY
        elif obstacle["type"] == "tree":
            color = DARK_GREEN
        else:  # wall
            color = DARK_GRAY
            
        pygame.draw.circle(self.screen, color, (x, y), size)
        pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
        
    def draw_portal(self, portal):
        x = int(portal["position"].x - self.camera.x)
        y = int(portal["position"].y - self.camera.y)
        
        # Animated portal
        time_factor = (self.game_time * 2) % (2 * math.pi)
        size = 20 + int(5 * math.sin(time_factor))
        
        required_level = portal["required_level"]
        
        if self.player.level >= required_level:
            color = GREEN
        else:
            color = RED
            
        pygame.draw.circle(self.screen, color, (x, y), size)
        pygame.draw.circle(self.screen, WHITE, (x, y), size - 5)
        
        # Portal label
        label = self.font.render(f"Domain {portal['target_domain']}", True, WHITE)
        self.screen.blit(label, (x - label.get_width() // 2, y - 30))
        
        # Level requirement
        req_label = self.font.render(f"Level {required_level}+", True, WHITE)
        self.screen.blit(req_label, (x - req_label.get_width() // 2, y - 15))
        
    def draw_wall(self, wall):
        x = int(wall["position"].x - self.camera.x)
        y = int(wall["position"].y - self.camera.y)
        size = wall.get("size", 20)  # Default size for circular walls
        wall_type = wall["type"]
        
        if wall_type == "wall":
            # Village wall (circular - legacy)
            pygame.draw.circle(self.screen, DARK_GRAY, (x, y), size)
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
        elif wall_type == "wall_rect":
            # Rectangular wall
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, DARK_GRAY, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
        elif wall_type == "house":
            # Village house
            house_color = (139, 69, 19)  # Brown
            pygame.draw.circle(self.screen, house_color, (x, y), size)
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
            
            # House roof
            roof_size = size + 5
            pygame.draw.circle(self.screen, (101, 67, 33), (x, y - 8), roof_size)
            pygame.draw.circle(self.screen, BLACK, (x, y - 8), roof_size, 1)
            
            # House number
            house_num = self.font.render(str(wall.get("house_id", 1)), True, WHITE)
            self.screen.blit(house_num, (x - house_num.get_width() // 2, y - house_num.get_height() // 2))
        elif wall_type == "guild_house":
            # Guild house (rectangular)
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, (180, 180, 180), rect)  # Light grey
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # Guild house label
            guild_text = self.font.render("Guild House", True, BLACK)
            self.screen.blit(guild_text, (x - guild_text.get_width() // 2, y - guild_text.get_height() // 2))
        elif wall_type == "gate_pillar":
            # Gate pillar
            pygame.draw.circle(self.screen, (105, 105, 105), (x, y), size)
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
        elif wall_type == "gate_arch":
            # Gate arch
            pygame.draw.circle(self.screen, (169, 169, 169), (x, y), size)
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
            
            # Gate label
            gate_text = self.font.render("GATE", True, WHITE)
            self.screen.blit(gate_text, (x - gate_text.get_width() // 2, y - gate_text.get_height() // 2))
        elif wall_type == "road":
            # Road
            pygame.draw.circle(self.screen, (160, 82, 45), (x, y), size)
            pygame.draw.circle(self.screen, (139, 69, 19), (x, y), size, 1)
        elif wall_type == "guild_quest":
            # Guild Quest area (rectangular)
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, (200, 200, 200), rect)  # Slightly darker grey
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # Quest marker
            quest_text = self.font.render("Guild Quest", True, BLACK)
            self.screen.blit(quest_text, (x - quest_text.get_width() // 2, y - quest_text.get_height() // 2))
            
            # Yellow exclamation mark
            exclamation_text = self.font.render("!", True, (255, 215, 0))  # Gold color
            self.screen.blit(exclamation_text, (x - exclamation_text.get_width() // 2, y - height // 2 - 15))
        elif wall_type == "npc_quest":
            # NPC Quest (rectangular)
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, (100, 100, 100), rect)  # Dark grey
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # NPC label
            npc_text = self.font.render("NPC Quest", True, BLACK)
            self.screen.blit(npc_text, (x - npc_text.get_width() // 2, y - npc_text.get_height() // 2))
            
            # Yellow exclamation mark
            exclamation_text = self.font.render("!", True, (255, 215, 0))  # Gold color
            self.screen.blit(exclamation_text, (x - exclamation_text.get_width() // 2, y - height // 2 - 15))
        elif wall_type == "fountain":
            # Fountain in center
            pygame.draw.circle(self.screen, (169, 169, 169), (x, y), size)  # Light gray
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 3)
            
            # Fountain water effect
            pygame.draw.circle(self.screen, (135, 206, 235), (x, y), size - 5)  # Sky blue
            pygame.draw.circle(self.screen, BLACK, (x, y), size - 5, 1)
            
            # Fountain label
            fountain_text = self.font.render("FOUNTAIN", True, BLACK)
            self.screen.blit(fountain_text, (x - fountain_text.get_width() // 2, y - fountain_text.get_height() // 2))
        elif wall_type == "portal":
            # Domain portal
            portal_id = wall.get("portal_id", 1)
            pygame.draw.circle(self.screen, (135, 206, 235), (x, y), size)  # Light blue
            pygame.draw.circle(self.screen, WHITE, (x, y), size, 2)
            
            # Portal number
            portal_text = self.font.render(f"P{portal_id}", True, BLACK)
            self.screen.blit(portal_text, (x - portal_text.get_width() // 2, y - portal_text.get_height() // 2))
        elif wall_type == "main_path":
            # Main path running through center
            pygame.draw.circle(self.screen, (200, 200, 200), (x, y), size)  # Light grey
            pygame.draw.circle(self.screen, (150, 150, 150), (x, y), size, 1)  # Darker outline
        elif wall_type == "guard":
            # Gate guard
            pygame.draw.circle(self.screen, (100, 100, 100), (x, y), size)  # Dark grey
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
            
            # Guard label
            guard_text = self.font.render("Guard", True, BLACK)
            self.screen.blit(guard_text, (x - guard_text.get_width() // 2, y - size - 20))
        elif wall_type == "bank":
            # Bank building
            pygame.draw.rect(self.screen, (120, 120, 120), (x - size, y - size, size * 2, size * 2))  # Grey rectangle
            pygame.draw.rect(self.screen, BLACK, (x - size, y - size, size * 2, size * 2), 2)
            
            # Bank label
            bank_text = self.font.render("Bank", True, BLACK)
            self.screen.blit(bank_text, (x - bank_text.get_width() // 2, y - bank_text.get_height() // 2))
        elif wall_type == "blacksmith":
            # Blacksmith NPC
            pygame.draw.circle(self.screen, (80, 80, 80), (x, y), size)  # Dark grey
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
            
            # Blacksmith label
            blacksmith_text = self.font.render("Blacksmith", True, BLACK)
            self.screen.blit(blacksmith_text, (x - blacksmith_text.get_width() // 2, y - size - 15))
        elif wall_type == "traveler":
            # Traveler NPC
            pygame.draw.circle(self.screen, (80, 80, 80), (x, y), size)  # Dark grey
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
            
            # Traveler label
            traveler_text = self.font.render("Traveler", True, BLACK)
            self.screen.blit(traveler_text, (x - traveler_text.get_width() // 2, y - size - 15))
        elif wall_type == "villager":
            # Villager NPC
            villager_id = wall.get("villager_id", 1)
            pygame.draw.circle(self.screen, (80, 80, 80), (x, y), size)  # Dark grey
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 2)
            
            # Villager label
            villager_text = self.font.render(f"Villager {villager_id}", True, BLACK)
            self.screen.blit(villager_text, (x - villager_text.get_width() // 2, y - size - 15))
        elif wall_type == "npc_trainer":
            # NPC Trainer (rectangular)
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, (100, 100, 100), rect)  # Dark grey
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # Trainer label
            trainer_text = self.font.render("NPC Trainer", True, BLACK)
            self.screen.blit(trainer_text, (x - trainer_text.get_width() // 2, y - trainer_text.get_height() // 2))
            
            # Yellow exclamation mark
            exclamation_text = self.font.render("!", True, (255, 215, 0))  # Gold color
            self.screen.blit(exclamation_text, (x - exclamation_text.get_width() // 2, y - height // 2 - 15))
        elif wall_type == "central_portal":
            # Central portal
            pygame.draw.circle(self.screen, (169, 169, 169), (x, y), size)  # Light grey outer ring
            pygame.draw.circle(self.screen, BLACK, (x, y), size, 3)
            
            # White inner circle
            pygame.draw.circle(self.screen, WHITE, (x, y), size - 8)
            pygame.draw.circle(self.screen, BLACK, (x, y), size - 8, 1)
            
            # Portal label
            portal_text = self.font.render("PORTAL", True, BLACK)
            self.screen.blit(portal_text, (x - portal_text.get_width() // 2, y - portal_text.get_height() // 2))
        elif wall_type == "respawn_point":
            # Respawn point
            pygame.draw.rect(self.screen, (120, 120, 120), (x - size, y - size, size * 2, size * 2))  # Grey rectangle
            pygame.draw.rect(self.screen, BLACK, (x - size, y - size, size * 2, size * 2), 2)
            
            # Respawn label
            respawn_text = self.font.render("Respawn", True, BLACK)
            self.screen.blit(respawn_text, (x - respawn_text.get_width() // 2, y - respawn_text.get_height() // 2))
        elif wall_type == "respawn_area":
            # Respawn area (rectangular)
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, (100, 100, 100), rect)  # Dark grey
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # Respawn area label
            respawn_text = self.font.render("Respawn Area", True, BLACK)
            self.screen.blit(respawn_text, (x - respawn_text.get_width() // 2, y - respawn_text.get_height() // 2))
        elif wall_type == "gate_label":
            # Gate label
            width = wall.get("width", size)
            height = wall.get("height", size)
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            pygame.draw.rect(self.screen, (150, 150, 150), rect)  # Light grey
            pygame.draw.rect(self.screen, BLACK, rect, 1)
            
            # Gate label
            gate_text = self.font.render("GATE", True, BLACK)
            self.screen.blit(gate_text, (x - gate_text.get_width() // 2, y - gate_text.get_height() // 2))
        
    def draw_domain_indicator(self, indicator):
        x = int(indicator["position"].x - self.camera.x)
        y = int(indicator["position"].y - self.camera.y)
        
        # Draw domain name background
        name_text = self.big_font.render(indicator["name"], True, WHITE)
        bg_rect = pygame.Rect(x - name_text.get_width() // 2 - 10, y - 10, name_text.get_width() + 20, 30)
        pygame.draw.rect(self.screen, DARK_GRAY, bg_rect)
        pygame.draw.rect(self.screen, WHITE, bg_rect, 2)
        
        # Draw domain name
        self.screen.blit(name_text, (x - name_text.get_width() // 2, y - 5))
        
        # Draw domain level
        level_text = self.font.render(f"Domain {indicator['level']}", True, YELLOW)
        self.screen.blit(level_text, (x - level_text.get_width() // 2, y + 15))
        
    def draw_graveyard(self):
        x = int(self.player.graveyard_position.x - self.camera.x)
        y = int(self.player.graveyard_position.y - self.camera.y)
        
        # Draw graveyard area
        pygame.draw.circle(self.screen, DARK_GRAY, (x, y), 40)
        pygame.draw.circle(self.screen, BLACK, (x, y), 40, 3)
        
        # Draw gravestones
        for i in range(3):
            stone_x = x - 20 + i * 20
            stone_y = y + 10
            pygame.draw.rect(self.screen, GRAY, (stone_x - 5, stone_y - 15, 10, 20))
            pygame.draw.rect(self.screen, BLACK, (stone_x - 5, stone_y - 15, 10, 20), 1)
        
        # Draw graveyard label
        label = self.font.render("Graveyard", True, WHITE)
        self.screen.blit(label, (x - label.get_width() // 2, y - 60))
        
    def draw_death_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Death message
        death_text = self.big_font.render("YOU DIED", True, RED)
        self.screen.blit(death_text, (WINDOW_WIDTH // 2 - death_text.get_width() // 2, WINDOW_HEIGHT // 2 - 50))
        
        # Respawn timer
        timer_text = self.font.render(f"Respawning in {self.player.death_timer:.1f} seconds...", True, WHITE)
        self.screen.blit(timer_text, (WINDOW_WIDTH // 2 - timer_text.get_width() // 2, WINDOW_HEIGHT // 2))
        
        # Instructions
        instruction_text = self.font.render("You will respawn at the graveyard", True, WHITE)
        self.screen.blit(instruction_text, (WINDOW_WIDTH // 2 - instruction_text.get_width() // 2, WINDOW_HEIGHT // 2 + 30))
        
    def draw_forest_areas(self):
        """Draw forest area indicators"""
        center_x = self.player.community_center.x
        center_y = self.player.community_center.y
        
        # Forest areas (same as enemy spawning)
        forest_areas = [
            # Top forest (north of village)
            {"x_range": (center_x - 400, center_x + 400), "y_range": (50, center_y - 200)},
            # Left forest (west of village)
            {"x_range": (50, center_x - 200), "y_range": (center_y - 300, center_y + 300)},
            # Right forest (east of village)
            {"x_range": (center_x + 200, WORLD_WIDTH - 50), "y_range": (center_y - 300, center_y + 300)},
            # Bottom forest (south of village)
            {"x_range": (center_x - 400, center_x + 400), "y_range": (center_y + 200, WORLD_HEIGHT - 50)}
        ]
        
        for i, forest in enumerate(forest_areas):
            # Draw forest boundary indicators
            x1 = int(forest["x_range"][0] - self.camera.x)
            y1 = int(forest["y_range"][0] - self.camera.y)
            x2 = int(forest["x_range"][1] - self.camera.x)
            y2 = int(forest["y_range"][1] - self.camera.y)
            
            # Draw forest label at center of each area
            forest_center_x = (forest["x_range"][0] + forest["x_range"][1]) // 2
            forest_center_y = (forest["y_range"][0] + forest["y_range"][1]) // 2
            
            label_x = int(forest_center_x - self.camera.x)
            label_y = int(forest_center_y - self.camera.y)
            
            # Only draw if forest area is visible on screen
            if (0 <= label_x <= WINDOW_WIDTH and 0 <= label_y <= WINDOW_HEIGHT):
                forest_names = ["North Forest", "West Forest", "East Forest", "South Forest"]
                forest_text = self.font.render(forest_names[i], True, DARK_GREEN)
                self.screen.blit(forest_text, (label_x - forest_text.get_width() // 2, label_y - forest_text.get_height() // 2))
        
    def draw_npc(self):
        x = int(self.npc_position.x - self.camera.x)
        y = int(self.npc_position.y - self.camera.y)
        
        # Draw NPC body (inside guild house)
        pygame.draw.rect(self.screen, (180, 220, 255), pygame.Rect(x - 8, y - 12, 16, 24))
        pygame.draw.rect(self.screen, BLACK, pygame.Rect(x - 8, y - 12, 16, 24), 2)
        
        # Draw NPC name
        name = self.font.render("Guild Master", True, WHITE)
        self.screen.blit(name, (x - name.get_width() // 2, y - 45))
        
        # Draw quest indicator (always visible since NPC is in guild house)
        bubble_radius = 12
        bubble_x = x
        bubble_y = y - 35
        
        pygame.draw.circle(self.screen, YELLOW, (bubble_x, bubble_y), bubble_radius)
        pygame.draw.circle(self.screen, ORANGE, (bubble_x, bubble_y), bubble_radius, 2)
        
        exclamation = self.font.render("!", True, RED)
        self.screen.blit(exclamation, (bubble_x - exclamation.get_width() // 2, bubble_y - exclamation.get_height() // 2))
        
        # Check if player is near NPC (inside guild house)
        player_distance = (self.player.position - self.npc_position).length()
        
        if player_distance < 40:  # Smaller interaction radius since it's inside
            # Draw interaction prompt
            prompt_text = self.font.render("Press E for quests", True, GREEN)
            self.screen.blit(prompt_text, (x - prompt_text.get_width() // 2, y + 20))
            
    def draw_ui(self):
        # Character UI Layout (based on image)
        ui_x = 20
        ui_y = 20
        
        # 1. Circular profile icon with human silhouette
        profile_radius = 30
        profile_center = (ui_x + profile_radius, ui_y + profile_radius)
        
        # Draw white circle with black outline
        pygame.draw.circle(self.screen, WHITE, profile_center, profile_radius)
        pygame.draw.circle(self.screen, BLACK, profile_center, profile_radius, 3)
        
        # Draw human silhouette inside
        # Head
        head_center = (profile_center[0], profile_center[1] - 8)
        pygame.draw.circle(self.screen, BLACK, head_center, 8, 2)
        
        # Body (shoulders)
        body_start = (profile_center[0] - 12, profile_center[1] + 5)
        body_end = (profile_center[0] + 12, profile_center[1] + 5)
        pygame.draw.line(self.screen, BLACK, body_start, body_end, 2)
        
        # 2. Player name (to the right of profile icon)
        name_x = ui_x + profile_radius * 2 + 15
        name_y = ui_y + 5
        name_text = self.big_font.render("Player One", True, BLACK)
        self.screen.blit(name_text, (name_x, name_y))
        
        # 3. Level indicator (below profile icon)
        level_x = ui_x + profile_radius - 20
        level_y = ui_y + profile_radius * 2 + 5
        level_text = self.font.render(f"Level {self.player.level}", True, BLACK)
        self.screen.blit(level_text, (level_x, level_y))
        
        # 4. HP bar (below player name)
        hp_bar_x = name_x
        hp_bar_y = name_y + 35
        hp_bar_width = 200
        hp_bar_height = 20
        
        # HP bar background (white with black outline)
        hp_bar_rect = pygame.Rect(hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height)
        pygame.draw.rect(self.screen, WHITE, hp_bar_rect)
        pygame.draw.rect(self.screen, BLACK, hp_bar_rect, 2)
        
        # HP bar fill (green, rounded effect)
        hp_ratio = self.player.hp / max(1, self.player.max_hp)
        hp_fill_width = int(hp_bar_width * hp_ratio)
        if hp_fill_width > 4:
            hp_fill_rect = pygame.Rect(hp_bar_x + 2, hp_bar_y + 2, hp_fill_width - 4, hp_bar_height - 4)
            pygame.draw.rect(self.screen, GREEN, hp_fill_rect)
        
        # HP text centered in bar
        hp_text = self.font.render(f"HP: {int(self.player.hp)}/{self.player.max_hp}", True, BLACK)
        hp_text_x = hp_bar_x + (hp_bar_width - hp_text.get_width()) // 2
        hp_text_y = hp_bar_y + (hp_bar_height - hp_text.get_height()) // 2
        self.screen.blit(hp_text, (hp_text_x, hp_text_y))
        
        # 5. EXP bar (below HP bar)
        exp_bar_x = name_x
        exp_bar_y = hp_bar_y + hp_bar_height + 10
        exp_bar_width = 200
        exp_bar_height = 16
        
        # EXP bar background (white with black outline)
        exp_bar_rect = pygame.Rect(exp_bar_x, exp_bar_y, exp_bar_width, exp_bar_height)
        pygame.draw.rect(self.screen, WHITE, exp_bar_rect)
        pygame.draw.rect(self.screen, BLACK, exp_bar_rect, 2)
        
        # EXP bar fill (light blue, rounded effect)
        exp_ratio = self.player.exp / max(1, self.player.get_exp_needed())
        exp_fill_width = int(exp_bar_width * exp_ratio)
        if exp_fill_width > 4:
            exp_fill_rect = pygame.Rect(exp_bar_x + 2, exp_bar_y + 2, exp_fill_width - 4, exp_bar_height - 4)
            pygame.draw.rect(self.screen, (135, 206, 235), exp_fill_rect)  # Light blue
        
        # EXP text centered in bar
        exp_text = self.font.render(f"EXP: {int(self.player.exp)}/{self.player.get_exp_needed()}", True, BLACK)
        exp_text_x = exp_bar_x + (exp_bar_width - exp_text.get_width()) // 2
        exp_text_y = exp_bar_y + (exp_bar_height - exp_text.get_height()) // 2
        self.screen.blit(exp_text, (exp_text_x, exp_text_y))
        
        # Draw main game area/map (minimap)
        self.draw_main_game_area()
        
        # Draw active quest panel (bottom right)
        self.draw_active_quest_panel()
        
        # Domain info
        domain_text = self.font.render(f"Domain {self.current_domain}", True, YELLOW)
        self.screen.blit(domain_text, (WINDOW_WIDTH - 150, 40))
        
        # Hearthstone cooldown
        if self.player.hearthstone_cooldown > 0:
            hearthstone_text = self.font.render(f"Hearthstone: {self.player.hearthstone_cooldown:.1f}s", True, ORANGE)
        else:
            hearthstone_text = self.font.render("Hearthstone: Ready (H)", True, GREEN)
        self.screen.blit(hearthstone_text, (WINDOW_WIDTH - 200, 60))
        
        # Controls help
        controls = [
            "WASD: Move | Left Click: Shoot | E: Quest | Q: Quest Log | B: Inventory | H: Hearthstone"
        ]
        for i, control in enumerate(controls):
            control_text = self.font.render(control, True, WHITE)
            self.screen.blit(control_text, (20, WINDOW_HEIGHT - 20))
        
    def draw_main_game_area(self):
        """Draw minimap with light green background"""
        # Minimap size (top right corner)
        minimap_size = 150
        minimap_x = WINDOW_WIDTH - minimap_size - 20
        minimap_y = 20
        minimap_rect = pygame.Rect(minimap_x, minimap_y, minimap_size, minimap_size)
        
        # Light green background
        pygame.draw.rect(self.screen, (144, 238, 144), minimap_rect)  # Light green
        pygame.draw.rect(self.screen, BLACK, minimap_rect, 2)  # Black border
        
        # Draw minimap content
        self.draw_minimap_content(minimap_x, minimap_y, minimap_size)
        
    def draw_minimap_content(self, minimap_x, minimap_y, minimap_size):
        """Draw minimap content (player, enemies, etc.)"""
        # Player position on minimap
        player_x = minimap_x + (self.player.position.x / WORLD_WIDTH) * minimap_size
        player_y = minimap_y + (self.player.position.y / WORLD_HEIGHT) * minimap_size
        pygame.draw.circle(self.screen, BLUE, (int(player_x), int(player_y)), 3)
        
        # Enemy positions on minimap
        for enemy in self.enemies:
            enemy_x = minimap_x + (enemy.position.x / WORLD_WIDTH) * minimap_size
            enemy_y = minimap_y + (enemy.position.y / WORLD_HEIGHT) * minimap_size
            pygame.draw.circle(self.screen, RED, (int(enemy_x), int(enemy_y)), 2)
        
        # NPC position on minimap
        npc_x = minimap_x + (self.npc_position.x / WORLD_WIDTH) * minimap_size
        npc_y = minimap_y + (self.npc_position.y / WORLD_HEIGHT) * minimap_size
        pygame.draw.circle(self.screen, YELLOW, (int(npc_x), int(npc_y)), 3)
        
    def draw_active_quest_panel(self):
        """Draw active quest panel in bottom right corner"""
        if not self.show_quest_panel:
            # Draw small "Show" button when panel is hidden
            self.draw_show_button()
            return  # Don't draw full panel if hidden
            
        # Panel dimensions and position
        panel_width = 250
        panel_height = 150
        panel_x = WINDOW_WIDTH - panel_width - 20
        panel_y = WINDOW_HEIGHT - panel_height - 20
        
        # Light red/pink background with black border
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (255, 182, 193), panel_rect)  # Light pink
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)  # Black border
        
        # Title "Active Quest:"
        title_text = self.big_font.render("Active Quest:", True, BLACK)
        self.screen.blit(title_text, (panel_x + 10, panel_y + 10))
        
        # Quest list
        quest_y = panel_y + 40
        quest_number = 1
        
        # Show active quests
        active_quests = [q for q in self.player.active_quests.values() if not q.completed]
        completed_quests = self.completed_quests
        
        # Check if there are any quests
        if not active_quests and not completed_quests:
            # Show "No quest" indicator
            no_quest_text = self.font.render("No quest", True, (139, 0, 0))  # Dark red
            self.screen.blit(no_quest_text, (panel_x + 15, quest_y))
        else:
            # Display active quests first
            for quest in active_quests[:2]:  # Show max 2 quests
                quest_text = self.font.render(f"{quest_number}. {quest.name}: {quest.get_progress_text()}", True, (139, 0, 0))  # Dark red
                self.screen.blit(quest_text, (panel_x + 15, quest_y))
                
                # Status "Active" in green
                status_text = self.font.render("Active", True, GREEN)
                self.screen.blit(status_text, (panel_x + 25, quest_y + 18))
                
                quest_y += 40
                quest_number += 1
            
            # Display completed quests
            for quest in completed_quests[:2]:  # Show max 2 completed
                quest_text = self.font.render(f"{quest_number}. {quest.name}: {quest.get_progress_text()}", True, (139, 0, 0))  # Dark red
                self.screen.blit(quest_text, (panel_x + 15, quest_y))
                
                # Status "Completed" in green
                status_text = self.font.render("Completed", True, GREEN)
                self.screen.blit(status_text, (panel_x + 25, quest_y + 18))
                
                quest_y += 40
                quest_number += 1
        
        # Hide/Show button (bottom right of panel)
        button_width = 80
        button_height = 25
        button_x = panel_x + panel_width - button_width - 10
        button_y = panel_y + panel_height - button_height - 10
        
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, (144, 238, 144), button_rect)  # Light green
        pygame.draw.rect(self.screen, BLACK, button_rect, 2)  # Black border
        
        button_text = self.font.render("Hide/Show", True, BLACK)
        button_text_x = button_x + (button_width - button_text.get_width()) // 2
        button_text_y = button_y + (button_height - button_text.get_height()) // 2
        self.screen.blit(button_text, (button_text_x, button_text_y))
        
        # Store button rect for click detection
        self.hide_show_button_rect = button_rect
        
    def draw_show_button(self):
        """Draw small Show button when quest panel is hidden"""
        # Small button in bottom right corner
        button_width = 60
        button_height = 25
        button_x = WINDOW_WIDTH - button_width - 20
        button_y = WINDOW_HEIGHT - button_height - 20
        
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, (144, 238, 144), button_rect)  # Light green
        pygame.draw.rect(self.screen, BLACK, button_rect, 2)  # Black border
        
        button_text = self.font.render("Show", True, BLACK)
        button_text_x = button_x + (button_width - button_text.get_width()) // 2
        button_text_y = button_y + (button_height - button_text.get_height()) // 2
        self.screen.blit(button_text, (button_text_x, button_text_y))
        
        # Store show button rect for click detection
        self.show_button_rect = button_rect
        
    def handle_hide_show_button_click(self, event):
        """Handle click on Hide/Show button"""
        mouse_pos = pygame.mouse.get_pos()
        
        # Check if clicked on Hide/Show button (when panel is visible)
        if hasattr(self, 'hide_show_button_rect'):
            if self.hide_show_button_rect.collidepoint(mouse_pos):
                self.show_quest_panel = not self.show_quest_panel
                return
        
        # Check if clicked on Show button (when panel is hidden)
        if hasattr(self, 'show_button_rect'):
            if self.show_button_rect.collidepoint(mouse_pos):
                self.show_quest_panel = True
                return
        
    def draw_quest_status_bar(self):
        # Quest status bar below minimap
        status_y = 150  # Below minimap
        status_width = 180
        status_height = 20
        
        # Background
        status_bg = pygame.Rect(WINDOW_WIDTH - 200, status_y, status_width, status_height)
        pygame.draw.rect(self.screen, DARK_GRAY, status_bg)
        pygame.draw.rect(self.screen, WHITE, status_bg, 2)
        
        # Title
        title_text = self.font.render("Active Quests:", True, WHITE)
        self.screen.blit(title_text, (WINDOW_WIDTH - 195, status_y + 2))
        
        # Show active quests
        active_quests = [q for q in self.player.active_quests.values() if not q.completed]
        if active_quests:
            quest_y = status_y + 25
            for i, quest in enumerate(active_quests[:3]):  # Show max 3 quests
                quest_text = self.font.render(quest.get_short_description(), True, WHITE)
                self.screen.blit(quest_text, (WINDOW_WIDTH - 195, quest_y))
                quest_y += 18
                
                # Show completion status
                if quest.is_complete():
                    complete_text = self.font.render("✓ READY", True, GREEN)
                    self.screen.blit(complete_text, (WINDOW_WIDTH - 195, quest_y))
                    quest_y += 18
        else:
            no_quest_text = self.font.render("No active quests", True, GRAY)
            self.screen.blit(no_quest_text, (WINDOW_WIDTH - 195, status_y + 25))
        
    def draw_skill_bars(self):
        skill_y = WINDOW_HEIGHT - 80
        skill_width = 60
        skill_height = 20
        spacing = 10
        
        for i, skill in enumerate(self.player.skills):
            x = 16 + i * (skill_width + spacing)
            
            # Skill background
            skill_rect = pygame.Rect(x, skill_y, skill_width, skill_height)
            pygame.draw.rect(self.screen, DARK_GRAY, skill_rect)
            pygame.draw.rect(self.screen, WHITE, skill_rect, 2)
            
            # Skill number
            num_text = self.font.render(str(i + 1), True, WHITE)
            self.screen.blit(num_text, (x + 5, skill_y + 2))
            
            # Cooldown overlay
            if not self.player.skills[i]["last_used"] == 0:
                cooldown_ratio = (self.game_time - self.player.skills[i]["last_used"]) / self.player.skills[i]["cooldown"]
                if cooldown_ratio < 1.0:
                    cooldown_height = int(skill_height * (1 - cooldown_ratio))
                    if cooldown_height > 0:
                        cooldown_rect = pygame.Rect(x, skill_y + skill_height - cooldown_height, skill_width, cooldown_height)
                        pygame.draw.rect(self.screen, (100, 50, 50), cooldown_rect)
            
            # Unlocked indicator
            if i + 1 in self.player.unlocked_skills:
                pygame.draw.rect(self.screen, GREEN, skill_rect, 3)
            else:
                # Locked skill
                pygame.draw.rect(self.screen, GRAY, skill_rect)
                lock_text = self.font.render("🔒", True, WHITE)
                self.screen.blit(lock_text, (x + skill_width//2 - 5, skill_y + 2))
                
    def draw_minimap(self):
        """Draw minimap with mob density indicators"""
        # Minimap background
        minimap_size = 150
        minimap_x = WINDOW_WIDTH - minimap_size - 20
        minimap_y = 20
        
        minimap_rect = pygame.Rect(minimap_x, minimap_y, minimap_size, minimap_size)
        pygame.draw.rect(self.screen, BLACK, minimap_rect)
        pygame.draw.rect(self.screen, WHITE, minimap_rect, 2)
        
        # Calculate scale
        scale_x = minimap_size / WORLD_WIDTH
        scale_y = minimap_size / WORLD_HEIGHT
        
        # Draw player on minimap
        player_x = minimap_x + int(self.player.position.x * scale_x)
        player_y = minimap_y + int(self.player.position.y * scale_y)
        pygame.draw.circle(self.screen, BLUE, (player_x, player_y), 3)
        
        # Draw NPC on minimap
        npc_x = minimap_x + int(self.npc_position.x * scale_x)
        npc_y = minimap_y + int(self.npc_position.y * scale_y)
        pygame.draw.circle(self.screen, GREEN, (npc_x, npc_y), 3)
        
        # Draw enemies and calculate density
        enemy_density = {}
        for enemy in self.enemies:
            # Draw enemy on minimap
            enemy_x = minimap_x + int(enemy.position.x * scale_x)
            enemy_y = minimap_y + int(enemy.position.y * scale_y)
            color = enemy.get_difficulty_color(self.player.level)
            pygame.draw.circle(self.screen, color, (enemy_x, enemy_y), 1)
            
            # Calculate density in grid cells
            grid_x = int(enemy.position.x / 200)  # 200 pixel grid cells
            grid_y = int(enemy.position.y / 200)
            grid_key = f"{grid_x}_{grid_y}"
            
            if grid_key not in enemy_density:
                enemy_density[grid_key] = {"count": 0, "quest_mobs": 0}
            
            enemy_density[grid_key]["count"] += 1
            
            # Check if this enemy type is needed for quests
            for quest in self.player.active_quests.values():
                if not quest.completed and quest.target_mob.lower() == enemy.name.lower():
                    enemy_density[grid_key]["quest_mobs"] += 1
                    break
        
        # Draw density indicators
        for grid_key, density in enemy_density.items():
            if density["count"] >= 3:  # Show areas with 3+ enemies
                grid_x, grid_y = map(int, grid_key.split("_"))
                world_x = grid_x * 200
                world_y = grid_y * 200
                
                # Convert to minimap coordinates
                map_x = minimap_x + int(world_x * scale_x)
                map_y = minimap_y + int(world_y * scale_y)
                
                # Draw density indicator
                if density["quest_mobs"] > 0:
                    # Red for quest mobs
                    pygame.draw.circle(self.screen, RED, (map_x, map_y), 8, 2)
                else:
                    # Yellow for regular mobs
                    pygame.draw.circle(self.screen, YELLOW, (map_x, map_y), 6, 2)
        
        # Draw minimap title
        title_text = self.font.render("Minimap", True, WHITE)
        self.screen.blit(title_text, (minimap_x, minimap_y - 20))
        
    def draw_quest_dialog(self):
        """Draw quest dialog with one quest at a time"""
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT // 2 - 200, 600, 400)
        pygame.draw.rect(self.screen, DARK_GRAY, panel)
        pygame.draw.rect(self.screen, WHITE, panel, 3)
        
        # Check for completed quests first
        completed_quests = [q for q in self.player.active_quests.values() if q.is_complete()]
        available_quests = [q for q in self.available_quests if q.name not in self.player.active_quests]
        
        if completed_quests:
            # Show turn in dialog
            quest = completed_quests[0]  # Only show one completed quest
            
            # Quest title
            title = self.big_font.render("Quest Complete!", True, GREEN)
            self.screen.blit(title, (panel.x + 20, panel.y + 20))
            
            # Quest name
            name_text = self.big_font.render(quest.name, True, WHITE)
            self.screen.blit(name_text, (panel.x + 20, panel.y + 60))
            
            # Quest description
            desc_text = self.font.render(quest.description, True, WHITE)
            self.screen.blit(desc_text, (panel.x + 20, panel.y + 100))
            
            # Rewards
            rewards_text = self.font.render(f"Rewards: {quest.exp_reward} EXP", True, YELLOW)
            self.screen.blit(rewards_text, (panel.x + 20, panel.y + 140))
            
            # Turn In button
            turn_in_rect = pygame.Rect(panel.x + 20, panel.y + 200, 120, 40)
            pygame.draw.rect(self.screen, GREEN, turn_in_rect)
            pygame.draw.rect(self.screen, WHITE, turn_in_rect, 2)
            
            turn_in_text = self.font.render("Turn In", True, BLACK)
            self.screen.blit(turn_in_text, (turn_in_rect.x + 10, turn_in_rect.y + 10))
            
            # Instructions
            instruction_text = self.font.render("Click 'Turn In' or press ENTER to complete quest", True, WHITE)
            self.screen.blit(instruction_text, (panel.x + 20, panel.y + 260))
            
        elif available_quests:
            # Show accept dialog
            quest = available_quests[0]  # Only show one available quest
            
            # Quest title
            title = self.big_font.render("New Quest Available!", True, YELLOW)
            self.screen.blit(title, (panel.x + 20, panel.y + 20))
            
            # Quest name
            name_text = self.big_font.render(quest.name, True, WHITE)
            self.screen.blit(name_text, (panel.x + 20, panel.y + 60))
            
            # Quest description
            desc_text = self.font.render(quest.description, True, WHITE)
            self.screen.blit(desc_text, (panel.x + 20, panel.y + 100))
            
            # Objectives
            if quest.quest_type == "kill":
                obj_text = self.font.render(f"Objective: Slay {quest.required_kills} {quest.target_mob}", True, WHITE)
            elif quest.quest_type == "collect":
                obj_text = self.font.render(f"Objective: Collect {quest.required_items} {quest.quest_item}", True, WHITE)
            else:
                obj_text = self.font.render("Objective: Unknown", True, WHITE)
            self.screen.blit(obj_text, (panel.x + 20, panel.y + 140))
            
            # Rewards
            rewards_text = self.font.render(f"Rewards: {quest.exp_reward} EXP", True, YELLOW)
            self.screen.blit(rewards_text, (panel.x + 20, panel.y + 180))
            
            # Accept/Decline buttons
            accept_rect = pygame.Rect(panel.x + 20, panel.y + 220, 120, 40)
            decline_rect = pygame.Rect(panel.x + 160, panel.y + 220, 120, 40)
            
            pygame.draw.rect(self.screen, GREEN, accept_rect)
            pygame.draw.rect(self.screen, WHITE, accept_rect, 2)
            pygame.draw.rect(self.screen, RED, decline_rect)
            pygame.draw.rect(self.screen, WHITE, decline_rect, 2)
            
            accept_text = self.font.render("Accept", True, BLACK)
            decline_text = self.font.render("Decline", True, WHITE)
            self.screen.blit(accept_text, (accept_rect.x + 10, accept_rect.y + 10))
            self.screen.blit(decline_text, (decline_rect.x + 10, decline_rect.y + 10))
            
            # Instructions
            instruction_text = self.font.render("Click 'Accept' or 'Decline', or press ENTER/ESC", True, WHITE)
            self.screen.blit(instruction_text, (panel.x + 20, panel.y + 280))
        
    def draw_quest_log(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Quest log panel
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 350, WINDOW_HEIGHT // 2 - 250, 700, 500)
        pygame.draw.rect(self.screen, DARK_GRAY, panel)
        pygame.draw.rect(self.screen, WHITE, panel, 3)
        
        # Title
        title = self.big_font.render("Quest Log", True, WHITE)
        self.screen.blit(title, (panel.x + 20, panel.y + 20))
        
        active_quests = [q for q in self.player.active_quests.values() if not q.completed]
        completed_quests = self.completed_quests
        
        y = panel.y + 60
        
        # Active Quests Section
        active_title = self.big_font.render("Active Quests:", True, GREEN)
        self.screen.blit(active_title, (panel.x + 20, y))
        y += 30
        
        if active_quests:
            for quest in active_quests:
                # Quest name
                name_text = self.font.render(quest.name, True, WHITE)
                self.screen.blit(name_text, (panel.x + 20, y))
                y += 20
                
                # Quest description
                desc_text = self.font.render(quest.description, True, WHITE)
                self.screen.blit(desc_text, (panel.x + 20, y))
                y += 20
                
                # Progress
                if quest.quest_type == "kill":
                    progress_text = self.font.render(f"Progress: Slay {quest.target_mob} {quest.get_progress_text()}", True, YELLOW)
                else:  # collect
                    progress_text = self.font.render(f"Progress: Collect {quest.quest_item} {quest.get_progress_text()}", True, YELLOW)
                self.screen.blit(progress_text, (panel.x + 20, y))
                y += 20
                
                # Reward
                reward_text = self.font.render(f"Reward: {quest.exp_reward} EXP", True, GREEN)
                self.screen.blit(reward_text, (panel.x + 20, y))
                y += 25
                
                # Status
                if quest.is_complete():
                    status_text = self.font.render("✓ READY TO TURN IN", True, GREEN)
                    self.screen.blit(status_text, (panel.x + 20, y))
                    y += 20
                else:
                    status_text = self.font.render("⏳ IN PROGRESS", True, ORANGE)
                    self.screen.blit(status_text, (panel.x + 20, y))
                    y += 20
        else:
            no_active_text = self.font.render("No active quests", True, GRAY)
            self.screen.blit(no_active_text, (panel.x + 20, y))
            y += 30
        
        # Quest Items Section
        y += 20
        items_title = self.big_font.render("Quest Items:", True, PURPLE)
        self.screen.blit(items_title, (panel.x + 20, y))
        y += 30
        
        for item_name, count in self.player.quest_items.items():
            if count > 0:
                item_text = self.font.render(f"{item_name}: {count}", True, WHITE)
                self.screen.blit(item_text, (panel.x + 20, y))
                y += 20
        
        # Completed Quests Section
        y += 20
        completed_title = self.big_font.render("Completed Quests:", True, BLUE)
        self.screen.blit(completed_title, (panel.x + 20, y))
        y += 30
        
        if completed_quests:
            for quest in completed_quests:
                # Quest name
                name_text = self.font.render(quest.name, True, WHITE)
                self.screen.blit(name_text, (panel.x + 20, y))
                y += 20
                
                # Quest description
                desc_text = self.font.render(quest.description, True, WHITE)
                self.screen.blit(desc_text, (panel.x + 20, y))
                y += 20
                
                # Status
                status_text = self.font.render("✓ COMPLETED", True, GREEN)
                self.screen.blit(status_text, (panel.x + 20, y))
                y += 25
        else:
            no_completed_text = self.font.render("No completed quests", True, GRAY)
            self.screen.blit(no_completed_text, (panel.x + 20, y))
        
        # Instructions
        instructions = [
            "Press Esc to close quest log",
            "Press E near NPC to get new quests"
        ]
        y = panel.y + panel.height - 60
        for instruction in instructions:
            inst_text = self.font.render(instruction, True, WHITE)
            self.screen.blit(inst_text, (panel.x + 20, y))
            y += 20
    
    def handle_quest_interaction(self):
        """Handle quest interaction with NPC"""
        player_distance = (self.player.position - self.npc_position).length()
        
        if player_distance < 50:  # Within interaction range
            # Check for completed quests first
            completed_quests = [q for q in self.player.active_quests.values() if q.is_complete()]
            
            if completed_quests:
                # Show turn in dialog for completed quest
                self.show_quest_dialog = True
                self.selected_quest_index = 0
                print("Press E to turn in completed quest!")
            else:
                # Check if player has no active quests and no available quests
                if not self.player.active_quests and not self.available_quests:
                    # Generate new quest
                    self.available_quests = self.generate_quests_for_level(self.current_domain)
                
                if self.available_quests:
                    # Show accept dialog for available quest
                    self.show_quest_dialog = True
                    self.selected_quest_index = 0
                    print("Press E to accept new quest!")
                else:
                    print("No quests available at the moment!")
        else:
            print("You need to get closer to the NPC!")
    
    def handle_quest_dialog_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_quest_dialog = False
            elif event.key == pygame.K_RETURN:
                completed_quests = [q for q in self.player.active_quests.values() if q.is_complete()]
                if completed_quests:
                    self.turn_in_quest()
                else:
                    self.accept_quest()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            # Check if clicked on Accept, Decline, or Turn In buttons
            mouse_pos = pygame.mouse.get_pos()
            panel = pygame.Rect(WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT // 2 - 200, 600, 400)
            
            completed_quests = [q for q in self.player.active_quests.values() if q.is_complete()]
            available_quests = [q for q in self.available_quests if q.name not in self.player.active_quests]
            
            if completed_quests:
                # Turn In button
                turn_in_rect = pygame.Rect(panel.x + 20, panel.y + 200, 120, 40)
                if turn_in_rect.collidepoint(mouse_pos):
                    self.turn_in_quest()
                    return  # Prevent shooting
            elif available_quests:
                # Accept/Decline buttons
                accept_rect = pygame.Rect(panel.x + 20, panel.y + 220, 120, 40)
                decline_rect = pygame.Rect(panel.x + 160, panel.y + 220, 120, 40)
                
                if accept_rect.collidepoint(mouse_pos):
                    self.accept_quest()
                    return  # Prevent shooting
                elif decline_rect.collidepoint(mouse_pos):
                    self.show_quest_dialog = False
                    return  # Prevent shooting
    
    def handle_quest_log_input(self, event):
        """Handle input when the quest log is open."""
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.show_quest_log = False
    
    def accept_quest(self):
        """Accept the current available quest"""
        available_quests = [q for q in self.available_quests if q.name not in self.player.active_quests]
        
        if available_quests:
            selected_quest = available_quests[0]  # Only one quest available
            
            # Add quest to active quests
            self.player.active_quests[selected_quest.name] = selected_quest
            
            # Remove from available quests
            self.available_quests.remove(selected_quest)
            
            # Close dialog
            self.show_quest_dialog = False
            print(f"Quest accepted: {selected_quest.name}")
    
    def turn_in_quest(self):
        """Turn in the completed quest"""
        completed_quests = [q for q in self.player.active_quests.values() if q.is_complete()]
        
        if completed_quests:
            # Turn in the completed quest
            selected_quest = completed_quests[0]  # Only one quest to turn in
            
            # Give rewards
            self.player.gain_exp(selected_quest.exp_reward)
            print(f"Quest completed: {selected_quest.name}!")
            print(f"Received {selected_quest.exp_reward} experience points!")
            
            # Mark as completed and move to completed log
            selected_quest.completed = True
            self.completed_quests.append(selected_quest)
            
            # Remove from active quests
            del self.player.active_quests[selected_quest.name]
            
            # Generate new quest if no active quests
            if not self.player.active_quests and not self.available_quests:
                self.available_quests = self.generate_quests_for_level(self.current_domain)
                print("New quests are now available!")
                
            # Close dialog
            self.show_quest_dialog = False
    
    def draw_inventory(self):
        """Draw the inventory/bag interface with grid slots and currency"""
        # Create inventory panel (light grey background)
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 300, WINDOW_HEIGHT // 2 - 250, 600, 500)
        pygame.draw.rect(self.screen, (200, 200, 200), panel)  # Light grey
        pygame.draw.rect(self.screen, BLACK, panel, 2)
        
        # Title
        title = self.big_font.render("Inventory / Bag", True, BLACK)
        self.screen.blit(title, (panel.x + 20, panel.y + 20))
        
        # Create grid of inventory slots (4 rows x 6 columns = 24 slots)
        slot_size = 80
        slot_spacing = 10
        grid_start_x = panel.x + 20
        grid_start_y = panel.y + 60
        
        # Draw grid slots
        for row in range(4):
            for col in range(6):
                slot_x = grid_start_x + col * (slot_size + slot_spacing)
                slot_y = grid_start_y + row * (slot_size + slot_spacing)
                slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
                
                # Draw slot background (slightly darker grey)
                pygame.draw.rect(self.screen, (180, 180, 180), slot_rect)
                pygame.draw.rect(self.screen, WHITE, slot_rect, 1)  # White border
        
        # Fill slots with items
        slot_index = 0
        for item_name, count in self.player.quest_items.items():
            if count > 0 and slot_index < 24:  # Only show items with count > 0
                row = slot_index // 6
                col = slot_index % 6
                slot_x = grid_start_x + col * (slot_size + slot_spacing)
                slot_y = grid_start_y + row * (slot_size + slot_spacing)
                
                # Draw item text in slot
                item_text = self.font.render(f"{item_name} {count}x", True, BLACK)
                text_x = slot_x + (slot_size - item_text.get_width()) // 2
                text_y = slot_y + (slot_size - item_text.get_height()) // 2
                self.screen.blit(item_text, (text_x, text_y))
                
                slot_index += 1
        
        # Currency display at bottom
        currency_y = panel.y + panel.height - 40
        
        # Gold (bottom left)
        gold_text = self.font.render(f"{self.player.inventory['Gold']}g", True, BLACK)
        self.screen.blit(gold_text, (panel.x + 20, currency_y))
        
        # Silver and Bronze (bottom center)
        silver_amount = self.player.inventory.get("Silver", 0)
        bronze_amount = self.player.inventory.get("Bronze", 0)
        currency_text = self.font.render(f"{silver_amount}s {bronze_amount}b", True, BLACK)
        currency_x = panel.x + (panel.width - currency_text.get_width()) // 2
        self.screen.blit(currency_text, (currency_x, currency_y))
        
        # Instructions
        instruction_text = self.font.render("Press ESC or B to close inventory", True, BLACK)
        self.screen.blit(instruction_text, (panel.x + 20, panel.y + panel.height - 20))
    
    def run(self):
        """Main game loop"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.show_quest_dialog:
                            self.show_quest_dialog = False
                        elif self.show_quest_log:
                            self.show_quest_log = False
                        elif self.show_inventory:
                            self.show_inventory = False
                        else:
                            running = False
                    elif event.key == pygame.K_e:
                        if not self.show_quest_dialog and not self.show_quest_log and not self.show_inventory:
                            self.handle_quest_interaction()
                    elif event.key == pygame.K_q:
                        if not self.show_quest_dialog and not self.show_inventory:
                            self.show_quest_log = not self.show_quest_log
                    elif event.key == pygame.K_b:
                        if not self.show_quest_dialog and not self.show_quest_log:
                            self.show_inventory = not self.show_inventory
                    elif event.key == pygame.K_h:
                        if not self.player.is_dead:
                            self.player.use_hearthstone(self.game_time)
                    elif self.show_quest_dialog:
                        self.handle_quest_dialog_input(event)
                    elif self.show_quest_log:
                        self.handle_quest_log_input(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                    # Handle mouse clicks for dialogs
                    if self.show_quest_dialog:
                        self.handle_quest_dialog_input(event)
                    else:
                        # Handle Hide/Show button click
                        self.handle_hide_show_button_click(event)
            
            # Update game state
            self.update(dt)
            
            # Render everything
            self.render()
            
            # Update display
            pygame.display.flip()
        
        pygame.quit()

class ItemDrop:
    def __init__(self, position, item_name, item_type="quest"):
        self.position = position
        self.item_name = item_name
        self.item_type = item_type
        self.lifetime = 10.0  # Items disappear after 10 seconds
        self.bob_offset = 0
        self.bob_speed = 3.0
        
    def update(self, dt):
        self.lifetime -= dt
        self.bob_offset = math.sin(self.bob_speed * (10.0 - self.lifetime)) * 3
        
    def is_expired(self):
        return self.lifetime <= 0
        
    def get_color(self):
        if self.item_type == "quest":
            return PURPLE
        elif self.item_type == "gold":
            return YELLOW
        else:
            return WHITE

if __name__ == "__main__":
    game = Game()
    game.run()