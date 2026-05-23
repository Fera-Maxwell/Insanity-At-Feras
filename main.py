#!/bin/
# WHAT ARE YOU DOING HERE!?
# Alright fine
# Since you came here, BOTHERED TO COME
# I will give you a secret
# In the MAIN MENU press "CTRL+SHIFT+M" to 100% the game
# DON'T TELL ANYONE










































































































import arcade
import random
import os
import sys
import json
import logging
import platform
import threading

# i added pygame AND opencv JUST for this. you're welcome.
import pygame
import cv2

logging.getLogger("arcade").setLevel(logging.CRITICAL)


# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
def get_save_dir():
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    save_dir = os.path.join(base, "FNAF-Fera")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


SAVE_PATH   = os.path.join(get_save_dir(), "save.json")
CONFIG_PATH = os.path.join(get_save_dir(), "settings.json")


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE  = "Insanity At Fera's"
BG_WIDTH      = 1920

STATIC_MIN  = 0.2
STATIC_MAX  = 1.0
STATIC_FADE = 1.5

# ─────────────────────────────────────────────────────────────────────────────
# DEV MODE
# ─────────────────────────────────────────────────────────────────────────────
DEV_MODE = False

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
def load_settings():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return {
                    "subtitles": bool(data.get("subtitles", True)),
                    "static_fx": bool(data.get("static_fx", True)),
                }
        except:
            pass
    return {"subtitles": True, "static_fx": True}


def save_settings():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(SETTINGS, f)
    except:
        pass


SETTINGS = load_settings()


# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────
def load_save():
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r") as f:
                return json.load(f)
        except:
            pass
    return {"night": 1, "night6_unlocked": False, "custom_unlocked": False}


def write_save(data):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)
    except:
        pass


def wipe_save():
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED STATIC DRAW
# ─────────────────────────────────────────────────────────────────────────────
def draw_static(alpha, glitch_y, glitch_height, glitch_offset):
    if not SETTINGS["static_fx"]:
        return

    a = alpha
    bar_height = 3
    for y in range(0, SCREEN_HEIGHT, bar_height):
        c  = random.randint(80, 220)
        al = int(random.randint(120, 220) * a)
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, y, y + bar_height, (c, c, c, al))

    if glitch_height > 0:
        band_top = glitch_y + glitch_height
        arcade.draw_lrbt_rectangle_filled(
            glitch_offset, SCREEN_WIDTH + glitch_offset,
            glitch_y, band_top, (200, 200, 200, int(180 * a)))
        core_c = random.randint(200, 255)
        arcade.draw_lrbt_rectangle_filled(
            0, SCREEN_WIDTH,
            glitch_y + glitch_height // 3,
            band_top - glitch_height // 3,
            (core_c, core_c, core_c, int(230 * a)))

    edge = 80
    arcade.draw_lrbt_rectangle_filled(0,                   edge,         0, SCREEN_HEIGHT, (0, 0, 0, 160))
    arcade.draw_lrbt_rectangle_filled(SCREEN_WIDTH - edge, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (0, 0, 0, 160))
    arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0,                   edge,          (0, 0, 0, 160))
    arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT - edge, SCREEN_HEIGHT, (0, 0, 0, 160))

    if random.randint(1, 60) == 1:
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
                                          (255, 255, 255, int(random.randint(30, 80) * a)))


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
HALL_TO_DOOR_CAM = {"03": "06", "04": "07"}
DOOR_CAM_TO_SIDE = {"06": "LEFT", "07": "RIGHT"}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────────────
class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.save = load_save()
        self.selected = 0

        self.static_alpha  = 0.15
        self.static_timer  = 0.0
        self.glitch_y      = 0
        self.glitch_height = 0
        self.glitch_offset = 0

        self.blink_timer   = 0.0
        self.blink_visible = True

        self.secret_buffer = ""

    def get_menu_items(self):
        night    = self.save.get("night", 1)
        custom   = self.save.get("custom_unlocked", False)
        has_save = night > 1
        return [
            ("CONTINUE",     has_save),
            ("NEW GAME",     True),
            ("CUSTOM NIGHT", custom),
            ("CREDITS",      True),
            ("EXIT",         True),
        ]

    def on_show_view(self):
        self.save = load_save()

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (5, 5, 5, 255))
        draw_static(self.static_alpha, self.glitch_y, self.glitch_height, self.glitch_offset)

        arcade.Text("INSANITY AT FERA'S",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120,
                    arcade.color.WHITE, font_size=42, font_name="Arial",
                    bold=True, anchor_x="center").draw()

        if self.blink_visible:
            arcade.Text("_",
                        SCREEN_WIDTH // 2 + 280, SCREEN_HEIGHT - 120,
                        arcade.color.WHITE, font_size=42, font_name="Arial",
                        bold=True, anchor_x="left").draw()

        arcade.Text("a0.0.4 — ALPHA",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 160,
                    (120, 120, 120, 255), font_size=13, font_name="Arial",
                    anchor_x="center").draw()

        if DEV_MODE:
            arcade.Text("[DEV MODE ON]",
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT - 185,
                        (255, 80, 80, 255), font_size=11, font_name="Arial",
                        anchor_x="center").draw()

        items   = self.get_menu_items()
        start_y = SCREEN_HEIGHT // 2 + 80
        spacing = 60

        for i, (label, enabled) in enumerate(items):
            y           = start_y - i * spacing
            is_selected = i == self.selected

            if not enabled:
                color = (60, 60, 60, 255)
            elif is_selected:
                color = arcade.color.LIME_GREEN
            else:
                color = (180, 180, 180, 255)

            if is_selected and enabled and self.blink_visible:
                arcade.Text(">", SCREEN_WIDTH // 2 - 180, y,
                            arcade.color.LIME_GREEN, font_size=20, font_name="Arial",
                            anchor_x="center", anchor_y="center").draw()

            arcade.Text(label, SCREEN_WIDTH // 2, y,
                        color, font_size=24, font_name="Arial",
                        bold=is_selected and enabled,
                        anchor_x="center", anchor_y="center").draw()

            if not enabled:
                arcade.Text("[LOCKED]", SCREEN_WIDTH // 2 + 160, y,
                            (80, 80, 80, 255), font_size=11, font_name="Arial",
                            anchor_x="center", anchor_y="center").draw()

        arcade.Text("OPTIONS  [O]",
                    SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20,
                    (100, 100, 100, 255), font_size=12, font_name="Arial",
                    anchor_x="right", anchor_y="top").draw()

        arcade.Text("UP / DOWN  NAVIGATE      ENTER  SELECT",
                    SCREEN_WIDTH // 2, 30,
                    (70, 70, 70, 255), font_size=11, font_name="Arial",
                    anchor_x="center").draw()

    def on_update(self, delta_time):
        self.static_timer += delta_time
        if self.static_timer >= 0.15:
            self.static_timer  = 0.0
            self.glitch_y      = random.randint(0, SCREEN_HEIGHT - 60)
            self.glitch_height = random.randint(0, 40)
            self.glitch_offset = random.randint(-20, 20)

        self.blink_timer += delta_time
        if self.blink_timer >= 0.5:
            self.blink_visible = not self.blink_visible
            self.blink_timer   = 0.0

    def on_key_press(self, key, modifiers):
        global DEV_MODE

        # ── RAT TRAP — Ctrl+Shift+M ───────────────────────────────────────
        # ${\color{#0d1117}\text{CTRL+SHIFT+M. you have been warned.}}$
        if (key == arcade.key.M and
                (modifiers & arcade.key.MOD_CTRL) and
                (modifiers & arcade.key.MOD_SHIFT)):
            trigger_rat_trap()
            return

        if arcade.key.A <= key <= arcade.key.Z:
            char = chr(key).lower()
            self.secret_buffer += char
            if not "fera".startswith(self.secret_buffer):
                self.secret_buffer = char
                if not "fera".startswith(self.secret_buffer):
                    self.secret_buffer = ""
            if self.secret_buffer == "fera":
                DEV_MODE = not DEV_MODE
                self.secret_buffer = ""
                print(f"DEV MODE: {'ON' if DEV_MODE else 'OFF'}")
                return

        items = self.get_menu_items()

        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(items)
            while not items[self.selected][1]:
                self.selected = (self.selected - 1) % len(items)

        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(items)
            while not items[self.selected][1]:
                self.selected = (self.selected + 1) % len(items)

        elif key == arcade.key.ENTER:
            label, enabled = items[self.selected]
            if not enabled:
                return
            if label == "CONTINUE":
                self.window.show_view(FerasGame(night=self.save.get("night", 1)))
            elif label == "NEW GAME":
                self.window.show_view(ConfirmationView(self))
            elif label == "CUSTOM NIGHT":
                self.window.show_view(CustomNightView())
            elif label == "CREDITS":
                self.window.show_view(CreditsView())
            elif label == "EXIT":
                arcade.exit()

        elif key == arcade.key.O:
            self.window.show_view(OptionsView())

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        items   = self.get_menu_items()
        start_y = SCREEN_HEIGHT // 2 + 80
        spacing = 60
        for i, (label, enabled) in enumerate(items):
            btn_y = start_y - i * spacing
            if not enabled:
                continue
            if abs(y - btn_y) < 30:
                self.selected = i
                self.on_key_press(arcade.key.ENTER, 0)
                return

    def on_mouse_motion(self, x, y, dx, dy):
        items   = self.get_menu_items()
        start_y = SCREEN_HEIGHT // 2 + 80
        spacing = 60
        for i, (label, enabled) in enumerate(items):
            btn_y = start_y - i * spacing
            if enabled and abs(y - btn_y) < 30:
                self.selected = i
                break


# ─────────────────────────────────────────────────────────────────────────────
# CREDITS
# ─────────────────────────────────────────────────────────────────────────────
class CreditsView(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (8, 8, 8, 255))
        arcade.Text("CREDITS", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                    arcade.color.WHITE, font_size=36, bold=True,
                    anchor_x="center", font_name="Arial").draw()
        arcade.Text("Developer: Fera Maxwell\nAssisted by: Claude (Anthropic)\nCompiled for Windows by: Bluu",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40,
            arcade.color.GRAY, font_size=20,
            anchor_x="center", anchor_y="center",
            font_name="Arial", multiline=True,
            width=SCREEN_WIDTH, align="center").draw()

        arcade.Text('Testers = ["Crash", "Bluu"]',
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
            arcade.color.GRAY, font_size=20,
            anchor_x="center", anchor_y="center",
            font_name="Monospace").draw()
        arcade.Text("ESC to go back", SCREEN_WIDTH // 2, 40,
                    (70, 70, 70, 255), font_size=12,
                    anchor_x="center", font_name="Arial").draw()

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.ESCAPE, arcade.key.ENTER):
            self.window.show_view(MainMenuView())


# ─────────────────────────────────────────────────────────────────────────────
# OPTIONS
# ─────────────────────────────────────────────────────────────────────────────
class OptionsView(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected = 0
        self.rows = [
            ("SUBTITLES", "subtitles"),
            ("STATIC FX", "static_fx"),
            ("BACK",       None),
        ]

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (8, 8, 8, 255))

        arcade.Text("OPTIONS",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                    arcade.color.WHITE, font_size=36, font_name="Arial",
                    bold=True, anchor_x="center").draw()

        start_y = SCREEN_HEIGHT // 2 + 60
        for i, (label, key) in enumerate(self.rows):
            y     = start_y - i * 70
            color = arcade.color.LIME_GREEN if i == self.selected else (160, 160, 160, 255)

            if key is not None:
                val_text  = "ON" if SETTINGS[key] else "OFF"
                val_color = (100, 220, 100, 255) if SETTINGS[key] else (180, 80, 80, 255)
                arcade.Text(label, SCREEN_WIDTH // 2 - 80, y,
                            color, font_size=22, font_name="Arial",
                            anchor_x="right", anchor_y="center").draw()
                arcade.Text(val_text, SCREEN_WIDTH // 2 + 80, y,
                            val_color, font_size=22, font_name="Arial",
                            bold=True, anchor_x="left", anchor_y="center").draw()
            else:
                arcade.Text(label, SCREEN_WIDTH // 2, y,
                            color, font_size=22, font_name="Arial",
                            anchor_x="center", anchor_y="center").draw()

        arcade.Text("UP / DOWN  NAVIGATE      ENTER / LEFT / RIGHT  TOGGLE      ESC  BACK",
                    SCREEN_WIDTH // 2, 30,
                    (70, 70, 70, 255), font_size=11, font_name="Arial",
                    anchor_x="center").draw()

    def _toggle(self):
        label, key = self.rows[self.selected]
        if key is None:
            self.window.show_view(MainMenuView())
            return
        SETTINGS[key] = not SETTINGS[key]
        save_settings()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.rows)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.rows)
        elif key in (arcade.key.ENTER, arcade.key.LEFT, arcade.key.RIGHT):
            self._toggle()
        elif key in (arcade.key.ESCAPE, arcade.key.BACKSPACE):
            self.window.show_view(MainMenuView())


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM NIGHT
# ─────────────────────────────────────────────────────────────────────────────
class CustomNightView(arcade.View):
    def __init__(self):
        super().__init__()
        self.sliders = {"Fera": 0, "Jason": 0, "May": 0, "Jay": 0}
        self.names   = list(self.sliders.keys())
        self.selected = 0

        self.code_buffer       = ""
        self.code_mode         = False
        self.cursor_timer      = 0.0
        self.cursor_visible    = True
        self.code_error        = False
        self.code_error_timer  = 0.0
        self.code_secret       = False
        self.code_secret_timer = 0.0

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (8, 8, 8, 255))

        arcade.Text("CUSTOM NIGHT",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
                    arcade.color.WHITE, font_size=36, font_name="Arial",
                    bold=True, anchor_x="center").draw()

        arcade.Text("Set AI levels (0 = inactive, 20 = max)",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120,
                    (100, 100, 100, 255), font_size=13, font_name="Arial",
                    anchor_x="center").draw()

        start_y = SCREEN_HEIGHT // 2 + 80
        for i, name in enumerate(self.names):
            y      = start_y - i * 80
            level  = self.sliders[name]
            is_sel = i == self.selected
            color  = arcade.color.LIME_GREEN if is_sel else (160, 160, 160, 255)

            arcade.Text(name, SCREEN_WIDTH // 2 - 260, y,
                        color, font_size=20, font_name="Arial",
                        anchor_x="left", anchor_y="center", bold=is_sel).draw()

            bar_x = SCREEN_WIDTH // 2 - 60
            bar_w = 300
            bar_h = 18
            arcade.draw_lrbt_rectangle_filled(
                bar_x, bar_x + bar_w,
                y - bar_h // 2, y + bar_h // 2, (30, 30, 30, 255))

            fill_w = int(bar_w * (level / 20))
            if fill_w > 0:
                bar_color = arcade.color.LIME_GREEN if is_sel else (80, 140, 80, 255)
                arcade.draw_lrbt_rectangle_filled(
                    bar_x, bar_x + fill_w,
                    y - bar_h // 2, y + bar_h // 2, bar_color)

            arcade.Text(str(level), bar_x + bar_w + 20, y,
                        color, font_size=18, font_name="Arial",
                        anchor_x="left", anchor_y="center").draw()

        if self.code_mode:
            cursor = "_" if self.cursor_visible else " "
            arcade.Text(f"CODE: {self.code_buffer}{cursor}",
                        SCREEN_WIDTH // 2, 120,
                        arcade.color.LIME_GREEN, font_size=18,
                        font_name="Arial", anchor_x="center").draw()
        else:
            arcade.Text("Press C to enter a secret code",
                        SCREEN_WIDTH // 2, 120,
                        (50, 50, 50, 255), font_size=12,
                        font_name="Arial", anchor_x="center").draw()

        arcade.Text("[ ENTER ] START NIGHT",
                    SCREEN_WIDTH // 2, 70,
                    (140, 200, 140, 255), font_size=16,
                    font_name="Arial", anchor_x="center").draw()

        arcade.Text("UP / DOWN  SELECT      LEFT / RIGHT  ADJUST      ESC  BACK",
                    SCREEN_WIDTH // 2, 30,
                    (70, 70, 70, 255), font_size=11, font_name="Arial",
                    anchor_x="center").draw()

        if self.code_error:
            arcade.Text("WRONG CODE", SCREEN_WIDTH // 2, 150,
                        (200, 50, 50, 255), font_size=16, font_name="Arial",
                        anchor_x="center").draw()
        if self.code_secret:
            arcade.Text("OOooo Funny Number!!!", SCREEN_WIDTH // 2, 150,
                        (200, 50, 50, 255), font_size=16, font_name="Arial",
                        anchor_x="center").draw()

    def on_update(self, delta_time):
        self.cursor_timer += delta_time
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer   = 0.0
        if self.code_error:
            self.code_error_timer -= delta_time
            if self.code_error_timer <= 0:
                self.code_error = False
        if self.code_secret:
            self.code_secret_timer -= delta_time
            if self.code_secret_timer <= 0:
                self.code_secret = False

    def on_key_press(self, key, modifiers):
        if self.code_mode:
            if key == arcade.key.ENTER:
                self.process_code()
                self.code_mode   = False
                self.code_buffer = ""
            elif key == arcade.key.ESCAPE:
                self.code_mode   = False
                self.code_buffer = ""
            elif key == arcade.key.BACKSPACE:
                self.code_buffer = self.code_buffer[:-1]
            elif arcade.key.KEY_0 <= key <= arcade.key.KEY_9:
                self.code_buffer += chr(key)
            return

        if key == arcade.key.ESCAPE:
            self.window.show_view(MainMenuView())
        elif key == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.names)
        elif key == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.names)
        elif key == arcade.key.LEFT:
            name = self.names[self.selected]
            self.sliders[name] = max(0, self.sliders[name] - 1)
        elif key == arcade.key.RIGHT:
            name = self.names[self.selected]
            self.sliders[name] = min(20, self.sliders[name] + 1)
        elif key == arcade.key.ENTER:
            self.window.show_view(FerasGame(night=7, custom_ai=dict(self.sliders)))
        elif key == arcade.key.C:
            self.code_mode   = True
            self.code_buffer = ""

    def process_code(self):
        if self.code_buffer == "6969":
            self.code_secret       = True
            self.code_secret_timer = 2.0
        else:
            self.code_error       = True
            self.code_error_timer = 2.0


# ─────────────────────────────────────────────────────────────────────────────
# CONFIRMATION
# ─────────────────────────────────────────────────────────────────────────────
class ConfirmationView(arcade.View):
    def __init__(self, previous_view):
        super().__init__()
        self.previous_view = previous_view

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (10, 10, 10, 200))
        arcade.Text("ERASE DATA AND START NEW GAME?",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40,
                    arcade.color.RED, font_size=20, anchor_x="center").draw()
        arcade.Text("[Y] YES, WIPE SAVE    [N] NO, GO BACK",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
                    arcade.color.WHITE, font_size=16, anchor_x="center").draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Y:
            wipe_save()
            self.window.show_view(FerasGame(night=1))
        elif key == arcade.key.N:
            self.window.show_view(self.previous_view)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GAME
# ─────────────────────────────────────────────────────────────────────────────
class FerasGame(arcade.View):
    def __init__(self, night=1, custom_ai=None):
        super().__init__()
        self.night     = night
        self.custom_ai = custom_ai

        self.cam_nodes = ["01","02","03","04","05","06","07","08","09","10","11","12"]
        self.cam_names = {
            "01": "Stage",          "02": "Dining Area",    "03": "Left Hall",
            "04": "Right Hall",     "05": "Backstage",      "06": "Left Door",
            "07": "Right Door",     "08": "Kitchen",        "09": "Jay's curtain",
            "10": "Outdoors",       "11": "Cleaning Closet","12": "????",
        }

        self.ai_levels = custom_ai if custom_ai else {"Fera": 2, "Jason": 0, "May": 2, "Jay": 0}
        self.locations = {"Fera": "01", "Jason": "01", "May": "01", "Jay": "09"}

        self.stages      = {name: "roaming" for name in self.locations}
        self.door_timers = {name: 0.0      for name in self.locations}
        self.door_side   = {name: None     for name in self.locations}

        self.jay_video_time = 100.0

        self.current_index  = 0
        self.camera_up      = False
        self.game_over      = False
        self.game_over_by   = ""
        self.won            = False
        self.null_triggered = False

        self.ai_timer    = 0.0
        self.ai_interval = 5.0

        self.pan_offset = 320.0
        self.pan_target = 320.0
        self.pan_speed  = 8.0

        self.ui_text = arcade.Text("", 20, 20, arcade.color.LIME_GREEN,
                                   font_size=25, font_name="Arial")
        self.heartbeat_text = arcade.Text("", SCREEN_WIDTH - 20, 20, arcade.color.RED,
                                          font_size=20, anchor_x="right", font_name="Arial")
        self.power_text = arcade.Text("", 20, 60, arcade.color.LIME_GREEN,
                                      font_size=18, font_name="Arial")
        self.clock_text = arcade.Text("", 20, 90, arcade.color.LIME_GREEN,
                                      font_size=18, font_name="Arial")
        self.center_text = arcade.Text("", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                       arcade.color.WHITE, 50,
                                       anchor_x="center", anchor_y="center",
                                       font_name="Arial", multiline=True,
                                       width=SCREEN_WIDTH, align="center")

        self.typing_mode    = False
        self.input_buffer   = ""
        self.cursor_timer   = 0.0
        self.cursor_visible = True

        try:
            self.crt_hum = arcade.load_sound(resource_path(os.path.join("assets", "crt_hum.wav")))
        except:
            self.crt_hum = None
        self.hum_player = None

        self.power      = 100.0
        self.game_hour  = 6
        self.game_timer = 0.0

        self.static_timer  = 0.0
        self.glitch_offset = 0
        self.glitch_y      = 0
        self.glitch_height = 0
        self.static_alpha  = STATIC_MIN

        self.left_door_closed  = False
        self.right_door_closed = False
        self.left_door_light   = False
        self.right_door_light  = False

        try:
            self.office_bg = arcade.load_texture(resource_path(os.path.join("assets", "Office_ALPHA.png")))
        except:
            self.office_bg = None

    def shock_static(self):
        self.static_alpha = STATIC_MAX

    def check_null_spawn(self):
        if DEV_MODE:
            return
        if random.randint(1, 420) == 1:
            self.trigger_null_crash()

    def trigger_null_crash(self):
        self.null_triggered = True
        print("CRITICAL ERROR: NULL INTERCEPTED CAMERA FEED.")
        if self.hum_player:
            arcade.stop_sound(self.hum_player)
        arcade.schedule(lambda dt: sys.exit(), 2.0)

    def door_closed_for_side(self, side):
        if side == "LEFT":
            return self.left_door_closed
        return self.right_door_closed

    def spawn_for(self, name):
        return "09" if name == "Jay" else "01"

    def advance_pipeline(self, name, delta_time):
        stage = self.stages[name]
        loc   = self.locations[name]

        if stage == "roaming":
            if loc in HALL_TO_DOOR_CAM:
                self.stages[name] = "hall"
                if DEV_MODE:
                    print(f"DEV | {name} entered hall at CAM_{loc}")

        elif stage == "door_cam":
            if loc in DOOR_CAM_TO_SIDE:
                self.door_side[name]   = DOOR_CAM_TO_SIDE[loc]
                self.stages[name]      = "at_door"
                self.door_timers[name] = 20.0
                if DEV_MODE:
                    print(f"DEV | {name} reached {self.door_side[name]} door, 20s timer started")

        elif stage == "at_door":
            side = self.door_side[name]
            if self.door_closed_for_side(side) and self.door_timers[name] > 5.0:
                self.door_timers[name] = 5.0
            self.door_timers[name] -= delta_time
            if self.door_timers[name] <= 0:
                if self.door_closed_for_side(side):
                    self.locations[name]   = self.spawn_for(name)
                    self.stages[name]      = "roaming"
                    self.door_timers[name] = 0.0
                    self.door_side[name]   = None
                    if DEV_MODE:
                        print(f"DEV | {name} blocked and retreated to spawn")
                else:
                    self.trigger_game_over(name)

    def trigger_game_over(self, attacker):
        self.game_over    = True
        self.game_over_by = attacker
        print(f"DEAD BY {attacker}")
        if self.hum_player:
            arcade.stop_sound(self.hum_player)

    def move_character(self, name):
        stage = self.stages[name]
        if stage == "hall":
            door_cam = HALL_TO_DOOR_CAM.get(self.locations[name])
            if door_cam:
                self.locations[name] = door_cam
                self.stages[name]    = "door_cam"
                if DEV_MODE:
                    print(f"DEV | {name} forced to CAM_{door_cam}")
            return
        if stage in ("door_cam", "at_door"):
            return
        paths = {
            "01": ["02", "05"], "02": ["03", "04", "08", "09", "10"],
            "03": ["06"],        "04": ["07"],        "05": ["01", "02"],
            "06": ["01"],        "07": ["01"],        "08": ["02"],
            "10": ["02"],
        }
        current_loc    = self.locations[name]
        possible_moves = paths.get(current_loc, ["01"])
        self.locations[name] = random.choice(possible_moves)
        if DEV_MODE:
            print(f"DEV | {name} moved to CAM_{self.locations[name]}  Jay video={int(self.jay_video_time)}%")

    def draw_dev_overlay(self):
        y = SCREEN_HEIGHT - 30
        for name, loc in self.locations.items():
            cam_label = self.cam_names.get(loc, loc)
            stage     = self.stages[name]
            timer_str = f"  T={self.door_timers[name]:.1f}s" if stage == "at_door" else ""
            side_str  = f" [{self.door_side[name]}]" if self.door_side[name] else ""
            if name == "Jay":
                line = f"JAY: CAM_{loc} ({cam_label})  VIDEO={int(self.jay_video_time)}%"
            else:
                line = f"{name.upper()}: CAM_{loc} ({cam_label})  [{stage}]{side_str}{timer_str}"
            arcade.Text(line, 10, y, (255, 80, 80, 220), font_size=11, font_name="Arial").draw()
            y -= 18
        arcade.Text("[DEV MODE]", SCREEN_WIDTH - 10, SCREEN_HEIGHT - 20,
                    (255, 80, 80, 255), font_size=11, font_name="Arial",
                    anchor_x="right").draw()
        left_color = (40, 40, 80, 220) if self.left_door_closed else (20, 20, 20, 120)
        arcade.draw_lrbt_rectangle_filled(0, 120, 100, SCREEN_HEIGHT - 100, left_color)
        arcade.Text("CLOSED" if self.left_door_closed else "OPEN", 60, 65,
                    (100, 200, 100, 255) if self.left_door_closed else (200, 80, 80, 255),
                    10, anchor_x="center").draw()
        right_color = (40, 40, 80, 220) if self.right_door_closed else (20, 20, 20, 120)
        arcade.draw_lrbt_rectangle_filled(SCREEN_WIDTH - 120, SCREEN_WIDTH, 100, SCREEN_HEIGHT - 100, right_color)
        arcade.Text("CLOSED" if self.right_door_closed else "OPEN", SCREEN_WIDTH - 60, 65,
                    (100, 200, 100, 255) if self.right_door_closed else (200, 80, 80, 255),
                    10, anchor_x="center").draw()

    def on_draw(self):
        self.clear()
        if self.null_triggered:
            return
        if self.game_over:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, (0, 0, 0, 255))
            arcade.Text(f"DEAD BY {self.game_over_by.upper()}",
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                        arcade.color.RED, font_size=40, font_name="Arial",
                        bold=True, anchor_x="center", anchor_y="center").draw()
            arcade.Text("PRESS ENTER TO RETURN TO MENU",
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70,
                        (120, 120, 120, 255), 18, anchor_x="center").draw()
            return
        if self.won:
            self.center_text.text = "SHIFT COMPLETE\nYOU SURVIVED"
            self.center_text.draw()
            arcade.Text("PRESS ENTER TO CONTINUE",
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
                        (120, 120, 120, 255), 18, anchor_x="center").draw()
            return
        if not self.camera_up:
            if self.office_bg:
                src_x = int(self.pan_offset)
                arcade.draw_texture_rect(
                    self.office_bg,
                    arcade.LRBT(-src_x, BG_WIDTH - src_x, 0, SCREEN_HEIGHT)
                )
            arcade.Text("[ SPACE ] Open cameras",
                        SCREEN_WIDTH // 2, 50,
                        (50, 50, 50, 255), font_size=12, font_name="Arial",
                        anchor_x="center").draw()
            arcade.Text("[ A / D ] Close Left / Right door      [ Q / E ] Door lights      [ ESC ] Menu",
                        SCREEN_WIDTH // 2, 30,
                        (50, 50, 50, 255), font_size=12, font_name="Arial",
                        anchor_x="center").draw()
        else:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, arcade.color.BLACK)
            current_cam = self.cam_nodes[self.current_index]
            cam_name    = self.cam_names.get(current_cam, "Unknown")
            draw_static(self.static_alpha, self.glitch_y, self.glitch_height, self.glitch_offset)
            if self.typing_mode:
                cursor = "_" if self.cursor_visible else " "
                self.ui_text.text = f"DIAL: {self.input_buffer}{cursor}"
                self.ui_text.x, self.ui_text.y, self.ui_text.anchor_x = \
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, "center"
            else:
                self.ui_text.text = f"{current_cam} - {cam_name}"
                self.ui_text.x, self.ui_text.y, self.ui_text.anchor_x = 20, 20, "left"
            self.ui_text.draw()
            npc_count = sum(1 for loc in self.locations.values() if loc == current_cam)
            self.heartbeat_text.text = f"Heart beats in this room: {npc_count}"
            self.heartbeat_text.draw()
            self.power_text.text = f"POWER: {int(self.power)}%"
            display_hour = 12 if self.game_hour % 12 == 0 else self.game_hour % 12
            am_pm = "AM" if self.game_hour < 12 else "PM"
            self.clock_text.text = f"TIME: {display_hour:02}:{int(self.game_timer):02} {am_pm}"
            self.power_text.draw()
            self.clock_text.draw()
            arcade.Text(f"NIGHT {self.night}", 20, 115,
                        arcade.color.LIME_GREEN, font_size=18, font_name="Arial").draw()
        if DEV_MODE:
            self.draw_dev_overlay()

    def on_update(self, delta_time):
        if self.won or self.game_over or self.null_triggered:
            return
        if self.static_alpha > STATIC_MIN:
            self.static_alpha -= STATIC_FADE * delta_time
            if self.static_alpha < STATIC_MIN:
                self.static_alpha = STATIC_MIN
        self.static_timer += delta_time
        if self.static_timer >= 0.1:
            self.static_timer  = 0.0
            self.glitch_y      = random.randint(0, SCREEN_HEIGHT - 60)
            self.glitch_height = random.randint(0, 80)
            self.glitch_offset = random.randint(-40, 40)
        self.cursor_timer += delta_time
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer   = 0.0
        if not self.camera_up:
            self.pan_offset += (self.pan_target - self.pan_offset) * self.pan_speed * delta_time
            self.pan_offset  = max(0.0, min(float(BG_WIDTH - SCREEN_WIDTH), self.pan_offset))
        drain_rate = self.ai_levels.get("Jay", 0) * 0.5
        if drain_rate > 0:
            current_cam  = self.cam_nodes[self.current_index]
            watching_jay = self.camera_up and current_cam == "09"
            if not watching_jay:
                self.jay_video_time = max(0.0, self.jay_video_time - drain_rate * delta_time)
            else:
                self.jay_video_time = min(100.0, self.jay_video_time + delta_time * 2.0)
        for name in list(self.locations.keys()):
            self.advance_pipeline(name, delta_time)
            if self.game_over:
                return
        self.ai_timer += delta_time
        if self.ai_timer >= self.ai_interval:
            self.ai_timer = 0.0
            for name, level in self.ai_levels.items():
                if level > 0 and random.randint(1, 20) <= level:
                    self.move_character(name)
        if self.camera_up and self.hum_player:
            if self.hum_player.volume > 0.2:
                self.hum_player.volume -= delta_time * 2.0
        self.game_timer += delta_time
        if self.game_timer >= 60.0:
            self.game_timer = 0.0
            self.game_hour += 1
        if self.game_hour == 12 and ("PM" if self.game_hour >= 12 else "AM") == "PM":
            self.won = True
            if self.hum_player:
                arcade.stop_sound(self.hum_player)
            self._on_night_complete()
        if self.camera_up:
            self.power -= delta_time * 0.2
            if self.power <= 0:
                self.power = 0
                self.camera_up = False
                if self.hum_player:
                    arcade.stop_sound(self.hum_player)
        else:
            if self.power < 100:
                self.power += delta_time * 0.0166
        if self.left_door_closed:
            self.power -= delta_time * 0.1
        if self.right_door_closed:
            self.power -= delta_time * 0.1

    def _on_night_complete(self):
        if self.custom_ai:
            return
        save = load_save()
        if self.night < 5:
            save["night"] = self.night + 1
        elif self.night == 5:
            save["custom_unlocked"] = True
        write_save(save)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.camera_up:
            return
        max_pan = float(BG_WIDTH - SCREEN_WIDTH)
        self.pan_target = (x / SCREEN_WIDTH) * max_pan

    def on_key_press(self, key, modifiers):
        required_mods = arcade.key.MOD_CTRL | arcade.key.MOD_ALT | arcade.key.MOD_SHIFT
        if key == arcade.key.W and (modifiers & required_mods) == required_mods:
            self.game_hour = 12
            return
        if self.game_over:
            if key == arcade.key.ENTER:
                self.window.show_view(MainMenuView())
            return
        if self.won:
            if key == arcade.key.ENTER:
                self.window.show_view(MainMenuView())
            return
        if key == arcade.key.ESCAPE:
            if self.hum_player:
                arcade.stop_sound(self.hum_player)
            self.window.show_view(MainMenuView())
            return
        if DEV_MODE:
            if key == arcade.key.F1:
                self.locations["Fera"] = "03"
                self.stages["Fera"]    = "hall"
                print("DEV | Fera teleported to Left Hall")
            if key == arcade.key.F2:
                self.locations["May"] = "04"
                self.stages["May"]    = "hall"
                print("DEV | May teleported to Right Hall")
        if key == arcade.key.SPACE:
            if not self.camera_up and self.power > 0:
                self.camera_up = True
                self.shock_static()
                if self.crt_hum:
                    self.hum_player = arcade.play_sound(self.crt_hum, volume=1.0, loop=True)
            else:
                self.camera_up = False
                if self.hum_player:
                    arcade.stop_sound(self.hum_player)
            self.typing_mode = False
            return
        if key == arcade.key.K and self.camera_up:
            self.typing_mode  = True
            self.input_buffer = ""
            return
        if not self.camera_up and not self.typing_mode:
            if key == arcade.key.A:
                self.left_door_closed = not self.left_door_closed
            if key == arcade.key.D:
                self.right_door_closed = not self.right_door_closed
            if key == arcade.key.Q:
                self.left_door_light = not self.left_door_light
            if key == arcade.key.E:
                self.right_door_light = not self.right_door_light
        if self.typing_mode:
            if key == arcade.key.ENTER:
                self.process_dial_in()
                self.typing_mode = False
            elif key == arcade.key.BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            elif (arcade.key.KEY_0 <= key <= arcade.key.KEY_9) or (arcade.key.A <= key <= arcade.key.Z):
                self.input_buffer += chr(key).upper()
            return
        if self.camera_up:
            if key in (arcade.key.RIGHT, arcade.key.LEFT):
                if key == arcade.key.RIGHT:
                    self.current_index = (self.current_index + 1) % len(self.cam_nodes)
                else:
                    self.current_index = (self.current_index - 1) % len(self.cam_nodes)
                self.shock_static()
                self.check_null_spawn()
                if self.hum_player:
                    self.hum_player.volume = 1.0

    def process_dial_in(self):
        name_map   = {v.upper(): k for k, v in self.cam_names.items()}
        target     = self.input_buffer.strip().upper()
        if target.isdigit():
            target = target.zfill(2)
        if target == "RANDOM":
            self.current_index = random.randrange(len(self.cam_nodes))
            self.shock_static()
            self.check_null_spawn()
        elif target in self.cam_nodes or target in name_map:
            final_code         = target if target in self.cam_nodes else name_map[target]
            self.current_index = self.cam_nodes.index(final_code)
            self.shock_static()
            self.check_null_spawn()

PUNISHMENT_PACKS = [
    "catlaugh.mp4",
    "rattrap.mp4",
    "anime.mp4",
    "wayw.mp4",
]

def volume_to_max():
    """Shotgun every audio system. No survivors."""
    os.system("pactl set-sink-volume @DEFAULT_SINK@ 100%")        # pulseaudio / pipewire
    os.system("wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.0")        # pipewire native
    os.system("amixer set Master 100% unmute")                     # alsa
    os.system("amixer -D pulse set Master 100% unmute")            # alsa via pulse
    os.system("amixer -D pipewire set Master 100% unmute")         # alsa via pipewire
    os.system(                                                     # windows: spam vol up key 15x
        'powershell -c "(New-Object -comObject WScript.Shell)'
        '.SendKeys([char]175+[char]175+[char]175+[char]175+[char]175'
        '+[char]175+[char]175+[char]175+[char]175+[char]175'
        '+[char]175+[char]175+[char]175+[char]175+[char]175)"'
    )
    os.system("nircmd.exe setsysvolume 65535")                     # windows nircmd if installed


def trigger_rat_trap():
    """Picked randomly. All options are bad. This is intentional."""
    filename = random.choice(PUNISHMENT_PACKS)
    vid_path = resource_path(os.path.join("assets", ".secret", filename))

    def _run():
        volume_to_max()

        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        info   = pygame.display.Info()
        sw, sh = info.current_w, info.current_h
        screen = pygame.display.set_mode((sw, sh), pygame.NOFRAME)
        pygame.display.set_caption("")

        cap = cv2.VideoCapture(vid_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        # Extract and play audio via a temp wav dump
        # pygame can't decode mp4 audio directly so we rip it with opencv's backend
        # if that fails we just play silent — the video alone is punishment enough
        try:
            import subprocess
            tmp_audio = os.path.join(os.path.dirname(vid_path), ".tmp_audio.wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", vid_path, "-vn", "-ar", "44100",
                 "-ac", "2", "-f", "wav", tmp_audio],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            pygame.mixer.music.load(tmp_audio)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
        except:
            pass  # silent punishment is still punishment

        clock  = pygame.time.Clock()
        running = True

        while running:
            ret, frame = cap.read()
            if not ret:
                break  # video finished

            # opencv gives BGR, pygame wants RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (sw, sh))
            surf  = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            screen.blit(surf, (0, 0))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            clock.tick(fps)

        cap.release()
        pygame.quit()

        # clean up temp audio
        try:
            os.remove(tmp_audio)
        except:
            pass

        # Take the main game down with it. No escape.
        os._exit(0)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False)
    window.show_view(MainMenuView())
    arcade.run()


if __name__ == "__main__":
    main()
