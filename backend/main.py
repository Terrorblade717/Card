import json
import os
import random
from collections import defaultdict
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# =========================
# КОНФИГУРАЦИЯ
# =========================
PLAYERS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bot/players.json"))
BASE_BATTLE_LIMIT = 20
MAX_EXTRA_BATTLES = 5
HP_REDUCTION_FACTOR = 1.5

# =========================
# МОДЕЛИ
# =========================
class DeckRequest(BaseModel):
    deck: Dict[str, str]

class BattleResponse(BaseModel):
    winner: bool
    logs: List[str]
    new_rating: int
    battles_left: int
    events: List[Dict] = Field(default_factory=list)  # ← КРИТИЧЕСКИ ВАЖНОЕ ИЗМЕНЕНИЕ
    player_team: List[str] = Field(default_factory=list)
    enemy_team: List[str] = Field(default_factory=list)
    player_max_hp: Dict[str, int] = Field(default_factory=dict)
    enemy_max_hp: Dict[str, int] = Field(default_factory=dict)

# =========================
# ИНИЦИАЛИЗАЦИЯ FASTAPI
# =========================
app = FastAPI(title="TON Arena Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================
def load_players():
    if os.path.exists(PLAYERS_FILE):
        try:
            with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки players.json: {e}")
            return {}
    return {}

def save_players(data):
    os.makedirs(os.path.dirname(PLAYERS_FILE), exist_ok=True)
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_player():
    return {
        "rating": 0,
        "ton_balance": 0.0,
        "deck": {},
        "battles_used": 0,
        "extra_battles": 0
    }

# =========================
# БОЕВОЙ ДВИЖОК
# =========================

class BattleLogger:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.logs = []

    def log(self, text):
        if self.enabled:
            self.logs.append(text)
    
    def get_logs(self):
        return self.logs

class Hero:
    def __init__(self, name, role, hp, atk, armor, speed, ability=None):
        self.name = name
        self.role = role
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.base_atk = atk
        self.armor = armor
        self.speed = speed
        self.base_speed = speed
        self.ability = ability
        self.taunt = False
        self.stun = 0
        self.silence = 0
        self.barrier = 0
        self.immortal = 0
        self.reflect = 0
        self.dot_turns = 0
        self.dot_damage = 0
        self.cooldown = 0
        self.alive = True

    def reset(self):
        self.hp = self.max_hp
        self.atk = self.base_atk
        self.speed = self.base_speed
        self.taunt = False
        self.stun = 0
        self.silence = 0
        self.barrier = 0
        self.immortal = 0
        self.reflect = 0
        self.dot_turns = 0
        self.dot_damage = 0
        self.cooldown = 0
        self.alive = True

    def take_damage(self, dmg, ignore_armor=False):
        if not self.alive or dmg <= 0:
            return
        if self.name == "Marksman" and random.random() < 0.10:
            return
        if self.immortal > 0:
            self.immortal -= 1
            return
        if not ignore_armor:
            dmg = max(1, dmg - self.armor)
        if self.barrier > 0:
            absorbed = min(self.barrier, dmg)
            self.barrier -= absorbed
            dmg -= absorbed
        if dmg > 0:
            self.hp -= dmg
            if self.hp <= 0:
                self.hp = 0
                self.alive = False

# СПОСОБНОСТИ
def taunt(hero, allies, enemies):
    hero.taunt = True
    return {"targets": [hero.name]}
def armor_aura(hero, allies, enemies):
    for a in allies: a.armor += 1
    return {"targets": [a.name for a in allies]}
def reduce_enemy_damage(hero, allies, enemies):
    for e in enemies: e.atk = max(1, e.atk - 1)
    return {"targets": [e.name for e in enemies]}
def barrier(hero, allies, enemies):
    hero.barrier += 20
    return {"targets": [hero.name]}
def thorns(hero, allies, enemies):
    hero.reflect = 0.3
    return {"targets": [hero.name]}
def line_pressure(hero, allies, enemies):
    hero.atk += 1.4
    return {"targets": [hero.name]}
def scaling(hero, allies, enemies):
    hero.atk += 1
    return {"targets": [hero.name]}
def debuff(hero, allies, enemies):
    if enemies:
        target = random.choice(enemies)
        target.armor = max(0, target.armor - 2)
        return {"targets": [target.name]}
    return None
def dot(hero, allies, enemies):
    if enemies:
        target = random.choice(enemies)
        target.dot_turns = 2
        target.dot_damage = 5
        return {"targets": [target.name]}
    return None
def silence(hero, allies, enemies):
    if enemies:
        target = random.choice(enemies)
        target.silence = 1
        return {"targets": [target.name]}
    return None
def aoe(hero, allies, enemies):
    for e in enemies: e.take_damage(hero.atk // 2)
    return {"targets": [e.name for e in enemies]}
def heal(hero, allies, enemies):
    if allies:
        target = min(allies, key=lambda a: a.hp)
        target.hp = min(target.max_hp, target.hp + 25)
        return {"targets": [target.name]}
    return None
def buff(hero, allies, enemies):
    for a in allies: a.atk += 0.5
    return {"targets": [a.name for a in allies]}
def immortal(hero, allies, enemies):
    if allies:
        target = random.choice(allies)
        target.immortal = 1
        return {"targets": [target.name]}
    return None
def stun(hero, allies, enemies):
    if enemies:
        target = random.choice(enemies)
        target.stun = 1
        return {"targets": [target.name]}
    return None
def aoe_stun(hero, allies, enemies):
    if hero.cooldown == 0:
        for e in enemies: e.stun = 1
        hero.cooldown = 3
        return {"targets": [e.name for e in enemies]}
    else:
        hero.cooldown -= 1
    return None

# ГЕРОИ
HEROES = [
    Hero("Bulwark","Tank",180,7,7,2,taunt),
    Hero("Sentinel","Tank",160,8,5,3,armor_aura),
    Hero("Ironbound","Tank",170,7,6,2,reduce_enemy_damage),
    Hero("Shieldbearer","Tank",165,7,5,2,barrier),
    Hero("Warden","Tank",270,6,4,1,thorns),
    Hero("Vanguard","Fighter",130,13,4,4,line_pressure),
    Hero("Skirmisher","Fighter",120,14,3,5,None),
    Hero("Duelist","Fighter",115,15,3,5,None),
    Hero("Breaker","Fighter",125,13,3,4,None),
    Hero("Ravager","Fighter",130,12,3,4,scaling),
    Hero("Striker","DPS",100,17,2,7,None),
    Hero("Blade","DPS",100,16,2,6,None),
    Hero("Lurker","DPS",95,16,1,6,None),
    Hero("Marksman","DPS",105,15,1,6,None),
    Hero("Reaper","DPS",100,15,2,5,None),
    Hero("Arcanist","Mage",100,17,1,4,None),
    Hero("Hexer","Mage",105,14,2,4,debuff),
    Hero("Channeler","Mage",110,13,2,4,dot),
    Hero("Summoner","Mage",100,14,1,4,silence),
    Hero("Voidcaster","Mage",100,15,1,4,aoe),
    Hero("Medic","Support",120,8,3,4,heal),
    Hero("Enhancer","Support",110,9,3,4,buff),
    Hero("Protector","Support",120,7,4,3,immortal),
    Hero("Oracle","Support",105,8,3,4,stun),
    Hero("Harmonist","Support",115,7,3,3,aoe_stun),
]

for hero in HEROES:
    hero.max_hp = max(1, int(round(hero.max_hp / HP_REDUCTION_FACTOR)))
    hero.hp = hero.max_hp

def pick_target(attacker, enemies):
    if attacker.name == "Lurker":
        return min(enemies, key=lambda e: e.hp)
    taunters = [e for e in enemies if e.taunt]
    return random.choice(taunters if taunters else enemies)


def apply_dot_tick(hero, events):
    if hero.alive and hero.dot_turns > 0 and hero.dot_damage > 0:
        old_hp = hero.hp
        hero.take_damage(hero.dot_damage, ignore_armor=True)
        hero.dot_turns -= 1
        damage = old_hp - hero.hp
        if damage > 0:
            events.append({
                "type": "dot",
                "target": hero.name,
                "damage": damage,
                "target_hp": hero.hp,
            })


def trigger_reaper_execute(reaper, enemy_team, events):
    if not reaper.alive or reaper.name != "Reaper":
        return

    for e in enemy_team:
        if e.alive and e.hp > 0 and (e.hp / e.max_hp) < 0.25 and random.random() < 0.2:
            e.hp = 0
            e.alive = False
            events.append({
                "type": "execute",
                "attacker": reaper.name,
                "target": e.name,
            })

def simulate_battle(team_a, team_b, logger=None):
    if logger is None:
        logger = BattleLogger(enabled=False)
    for h in team_a + team_b:
        h.reset()
    logger.log("=== НАЧАЛО БОЯ ===")
    
    events = []
    
    for round_num in range(1, 31):
        alive_units = [h for h in team_a + team_b if h.alive]
        if not alive_units: break
        units = sorted(alive_units, key=lambda x: -x.speed)
        for h in units:
            if not h.alive: continue
            apply_dot_tick(h, events)
            if not h.alive:
                continue
            if h.stun > 0:
                h.stun = 0
                continue
            enemies = [e for e in (team_b if h in team_a else team_a) if e.alive]
            if not enemies:
                winner = h in team_a
                events.append({"type": "end", "winner": winner})
                return winner, events
            allies = team_a if h in team_a else team_b
            if h.ability and h.silence == 0:
                skill_event = {"type": "skill", "hero": h.name, "ability": h.ability.__name__}
                payload = h.ability(h, allies, enemies)
                if payload:
                    skill_event.update(payload)
                events.append(skill_event)
            elif h.silence > 0:
                h.silence = 0

            if h.name == "Reaper":
                trigger_reaper_execute(h, enemies, events)
                enemies = [e for e in enemies if e.alive]
                if not enemies:
                    winner = h in team_a
                    events.append({"type": "end", "winner": winner})
                    return winner, events

            target = pick_target(h, enemies)
            
            old_hp = target.hp
            
            if h.name == "Breaker":
                target.take_damage(h.atk, ignore_armor=True)
            else:
                dmg = h.atk
                if h.name == "Blade" and random.random() < 0.25:
                    dmg *= 2
                target.take_damage(dmg)
            
            damage_dealt = old_hp - target.hp
            if damage_dealt > 0:
                events.append({
                    "type": "attack",
                    "attacker": h.name,
                    "target": target.name,
                    "damage": damage_dealt,
                    "target_hp": target.hp
                })

                if target.reflect > 0 and h.alive:
                    reflected_damage = max(1, int(round(damage_dealt * target.reflect)))
                    old_attacker_hp = h.hp
                    h.take_damage(reflected_damage, ignore_armor=True)
                    reflected = old_attacker_hp - h.hp
                    if reflected > 0:
                        events.append({
                            "type": "reflect",
                            "attacker": target.name,
                            "target": h.name,
                            "damage": reflected,
                            "target_hp": h.hp,
                        })
            
            if h.name == "Duelist":
                h.atk += 2
            if h.name == "Striker":
                h.speed += 1
            if h.name == "Arcanist" and random.random() < 0.25 and target.alive:
                old_hp2 = target.hp
                target.take_damage(h.atk)
                extra_dmg = old_hp2 - target.hp
                if extra_dmg > 0:
                    events.append({
                        "type": "attack",
                        "attacker": h.name,
                        "target": target.name,
                        "damage": extra_dmg,
                        "target_hp": target.hp
                    })

        if not any(e.alive for e in team_b):
            events.append({"type": "end", "winner": True})
            return True, events
        if not any(e.alive for e in team_a):
            events.append({"type": "end", "winner": False})
            return False, events
    winner = random.choice([True, False])
    events.append({"type": "end", "winner": winner})
    return winner, events

def build_team_from_names(hero_names_dict, all_heroes):
    role_order = ["Tank", "Fighter", "DPS", "Mage", "Support"]
    name_to_hero = {h.name: h for h in all_heroes}
    team = []
    for role in role_order:
        name = hero_names_dict[role]
        hero = name_to_hero[name]
        team.append(hero)
    return team

# =========================
# API ЭНДПОИНТЫ
# =========================

@app.get("/api/user")
async def get_user(user_id: str):
    players = load_players()
    if user_id not in players:
        players[user_id] = create_player()
        save_players(players)
    data = players[user_id]
    total_battles = BASE_BATTLE_LIMIT + data.get("extra_battles", 0)
    battles_left = max(0, total_battles - data["battles_used"])
    return {
        "rating": data["rating"],
        "ton_balance": data["ton_balance"],
        "deck": data["deck"],
        "battles_left": battles_left,
        "battles_used": data["battles_used"],
        "extra_battles": data["extra_battles"]
    }

@app.post("/api/deck")
async def save_deck(user_id: str, request: DeckRequest):
    players = load_players()
    if user_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    expected_roles = {"Tank", "Fighter", "DPS", "Mage", "Support"}
    if set(request.deck.keys()) != expected_roles:
        raise HTTPException(status_code=400, detail="Invalid deck roles")
    
    hero_names = {h.name for h in HEROES}
    for name in request.deck.values():
        if name not in hero_names:
            raise HTTPException(status_code=400, detail=f"Hero {name} not found")
    
    players[user_id]["deck"] = request.deck
    save_players(players)
    return {"status": "ok"}

@app.post("/api/battle", response_model=BattleResponse)
async def start_battle(user_id: str):
    players = load_players()
    if user_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player = players[user_id]
    total_battles = BASE_BATTLE_LIMIT + player.get("extra_battles", 0)
    if player["battles_used"] >= total_battles:
        raise HTTPException(status_code=400, detail="No battles left")
    
    if not player["deck"]:
        raise HTTPException(status_code=400, detail="Deck not set")
    
    team_a = build_team_from_names(player["deck"], HEROES)
    grouped = defaultdict(list)
    for h in HEROES:
        grouped[h.role].append(h)
    team_b = [random.choice(grouped[role]) for role in ["Tank", "Fighter", "DPS", "Mage", "Support"]]
    
    winner, events = simulate_battle(team_a, team_b)
    
    player["battles_used"] += 1
    if winner:
        player["rating"] += 10
    else:
        player["rating"] += 5
    
    players[user_id] = player
    save_players(players)
    
    total_battles = BASE_BATTLE_LIMIT + player.get("extra_battles", 0)
    battles_left = max(0, total_battles - player["battles_used"])
    
    text_logs = []
    for ev in events:
        if ev["type"] == "attack":
            text_logs.append(f"{ev['attacker']} нанёс {ev['damage']} урона {ev['target']}.")
        elif ev["type"] == "execute":
            text_logs.append(f"{ev['target']} был уничтожен!")
    
    return BattleResponse(
        winner=winner,
        logs=text_logs,
        new_rating=player["rating"],
        battles_left=battles_left,
        events=events,
        player_team=[h.name for h in team_a],
        enemy_team=[h.name for h in team_b],
        player_max_hp={h.name: h.max_hp for h in team_a},
        enemy_max_hp={h.name: h.max_hp for h in team_b},
    )

@app.get("/api/rating")
async def get_rating():
    players = load_players()
    rating_list = []
    for uid, data in players.items():
        rating_list.append({"user_id": uid, "rating": data["rating"]})
    rating_list.sort(key=lambda x: x["rating"], reverse=True)
    return {"top": rating_list[:10]}

# =========================
# ОТДАЧА WEBAPP
# =========================
webapp_dir = os.path.join(os.path.dirname(__file__), "webapp")
if os.path.isdir(webapp_dir):
    app.mount("/", StaticFiles(directory=webapp_dir, html=True), name="webapp")
else:
    if os.path.isfile(os.path.join(os.path.dirname(__file__), "index.html")):
        app.mount("/", StaticFiles(directory=os.path.dirname(__file__), html=True), name="static")
    else:
        @app.get("/")
        async def root_fallback():
            return {"error": "WebApp not found. Place 'index.html' in ../webapp/ or backend/ folder."}
