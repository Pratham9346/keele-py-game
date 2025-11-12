import random
import time
import tkinter as tk
from dataclasses import dataclass

WIDTH, HEIGHT = 600, 400
PLAYER_SIZE = 24
ENEMY_SIZE = 20
COIN_SIZE = 14
SPAWN_ENEMY_MS = 1200
SPAWN_COIN_MS = 900
TICK_MS = 16  # ~60 FPS

@dataclass
class Entity:
    kind: str
    x: float
    y: float
    vx: float
    vy: float
    size: int
    canvas_id: int | None = None

class Game:
    def __init__(self, root: tk.Tk):  # ✅ fixed (was _init_)
        self.root = root
        self.root.title("Dodge & Collect — Tkinter Mini Game")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()
        self.hud = self.canvas.create_text(
            WIDTH // 2, 16, fill="white", font=("Arial", 14), text=""
        )

        self.keys = set()
        self.player: Entity | None = None
        self.entities: list[Entity] = []
        self.score = 0
        self.start_time = time.time()
        self.game_over = False
        self.paused = False

        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)

        self.reset()
        self.loop()
        self.schedule_spawns()

    # ----------------------- Input -----------------------
    def on_key_down(self, e: tk.Event):
        self.keys.add(e.keysym)
        if e.keysym.lower() == "p" and not self.game_over:
            self.paused = not self.paused
        if e.keysym.lower() == "r" and self.game_over:
            self.reset()

    def on_key_up(self, e: tk.Event):
        self.keys.discard(e.keysym)

    # ----------------------- Game Core -----------------------
    def reset(self):
        self.canvas.delete("all")
        self.hud = self.canvas.create_text(
            WIDTH // 2, 16, fill="white", font=("Arial", 14), text=""
        )
        self.entities.clear()
        self.score = 0
        self.start_time = time.time()
        self.game_over = False
        self.paused = False

        px, py = WIDTH // 2, HEIGHT - 40
        self.player = Entity("player", px, py, 0, 0, PLAYER_SIZE)
        self.player.canvas_id = self.canvas.create_rectangle(
            px - PLAYER_SIZE, py - PLAYER_SIZE,
            px + PLAYER_SIZE, py + PLAYER_SIZE,
            outline="", fill="#2ecc71"
        )

        for _ in range(3):
            self.spawn_coin()
        self.spawn_enemy()

    def loop(self):
        if not self.game_over and not self.paused:
            self.update_player()
            self.update_entities()
            self.check_collisions()
            self.draw_hud()
        self.root.after(TICK_MS, self.loop)

    def schedule_spawns(self):
        if not self.game_over:
            self.spawn_enemy()
            self.root.after(SPAWN_ENEMY_MS, self.schedule_spawns)
        if not self.game_over:
            self.spawn_coin()
            self.root.after(SPAWN_COIN_MS, self.schedule_spawns)

    def update_player(self):
        if not self.player:
            return
        speed = 6
        dx = dy = 0
        if "Left" in self.keys or "a" in self.keys:
            dx -= speed
        if "Right" in self.keys or "d" in self.keys:
            dx += speed
        if "Up" in self.keys or "w" in self.keys:
            dy -= speed
        if "Down" in self.keys or "s" in self.keys:
            dy += speed

        new_x = max(PLAYER_SIZE, min(WIDTH - PLAYER_SIZE, self.player.x + dx))
        new_y = max(PLAYER_SIZE, min(HEIGHT - PLAYER_SIZE, self.player.y + dy))
        self.player.x, self.player.y = new_x, new_y
        self.canvas.coords(
            self.player.canvas_id,
            new_x - PLAYER_SIZE, new_y - PLAYER_SIZE,
            new_x + PLAYER_SIZE, new_y + PLAYER_SIZE
        )

    def update_entities(self):
        new_list: list[Entity] = []
        for ent in self.entities:
            ent.x += ent.vx
            ent.y += ent.vy
            if ent.y > HEIGHT + ent.size or ent.x < -50 or ent.x > WIDTH + 50:
                if ent.canvas_id is not None:
                    self.canvas.delete(ent.canvas_id)
                continue

            if ent.canvas_id is not None:
                if ent.kind == "enemy":
                    self.canvas.coords(
                        ent.canvas_id,
                        ent.x - ENEMY_SIZE, ent.y - ENEMY_SIZE,
                        ent.x + ENEMY_SIZE, ent.y + ENEMY_SIZE
                    )
                elif ent.kind == "coin":
                    self.canvas.coords(
                        ent.canvas_id,
                        ent.x - COIN_SIZE, ent.y - COIN_SIZE,
                        ent.x + COIN_SIZE, ent.y + COIN_SIZE
                    )
            new_list.append(ent)
        self.entities = new_list

    def draw_hud(self):
        elapsed = int(time.time() - self.start_time)
        status = f"Score: {self.score}   Time: {elapsed}s"
        if self.paused:
            status += "   [PAUSED — Press G]"
        self.canvas.itemconfig(self.hud, text=status)

    # ----------------------- Spawning -----------------------
    def spawn_enemy(self):
        if self.game_over:
            return
        x = random.randint(ENEMY_SIZE, WIDTH - ENEMY_SIZE)
        y = -ENEMY_SIZE
        vy = random.uniform(2.2, 6.5)
        vx = random.uniform(-0.8, 8.8)
        ent = Entity("enemy", x, y, vx, vy, ENEMY_SIZE)
        ent.canvas_id = self.canvas.create_oval(
            x - ENEMY_SIZE, y - ENEMY_SIZE, x + ENEMY_SIZE, y + ENEMY_SIZE,
            outline="", fill="#e74c3c"
        )
        self.entities.append(ent)

    def spawn_coin(self):
        if self.game_over:
            return
        x = random.randint(COIN_SIZE, WIDTH - COIN_SIZE)
        y = -COIN_SIZE
        vy = random.uniform(1.5, 2.8)
        ent = Entity("coin", x, y, 0, vy, COIN_SIZE)
        ent.canvas_id = self.canvas.create_oval(
            x - COIN_SIZE, y - COIN_SIZE, x + COIN_SIZE, y + COIN_SIZE,
            outline="", fill="#f1c40f"
        )
        self.entities.append(ent)

    # ----------------------- Collisions -----------------------
    def check_collisions(self):
        if not self.player:
            return
        px, py = self.player.x, self.player.y
        keep: list[Entity] = []
        for ent in self.entities:
            if ent.kind == "enemy":
                if self._overlap(px, py, self.player.size, ent.x, ent.y, ent.size):
                    self._trigger_game_over()
                    self.canvas.delete(ent.canvas_id)
                    continue
                keep.append(ent)
            elif ent.kind == "coin":
                if self._overlap(px, py, self.player.size, ent.x, ent.y, ent.size):
                    self.score += 1
                    self.canvas.delete(ent.canvas_id)
                    continue
                keep.append(ent)
        self.entities = keep

    @staticmethod
    def _overlap(x1, y1, r1, x2, y2, r2) -> bool:
        dx = x1 - x2
        dy = y1 - y2
        return (dx * dx + dy * dy) <= ((r1 + r2) * (r1 + r2))

    def _trigger_game_over(self):
        self.game_over = True
        elapsed = int(time.time() - self.start_time)
        msg = f"GAME OVER\nScore {self.score}  Time {elapsed}s\n\nPress R to restart"
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            fill="white", font=("Arial", 18), text=msg, justify="center"
        )

def main():
    root = tk.Tk()
    Game(root)
    root.mainloop()

if __name__ == "__main__":  # ✅ fixed (was _name_ == "_main_")
    main()
