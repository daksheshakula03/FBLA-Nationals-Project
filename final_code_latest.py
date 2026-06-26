# ============================================================
# 2000's TRIVIA CHALLENGE
# A pygame-based trivia quiz game with login/registration,
# light/dark theming, procedurally generated sound effects,
# category-based quizzes, and bonus questions.
# ============================================================

import io
import json
import math
import os
import random
import sys
import array
import pygame


pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

# Core window settings used throughout the game.
WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2000's Trivia Challenge")

# File locations: user accounts/high scores are stored as JSON next to
# this script, and question images live in an "images" subfolder.
DATA_FILE = os.path.join(os.path.dirname(__file__), "user_data.json")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
PICTURES_DIR = os.path.join(os.path.dirname(__file__), "pictures")
FALLBACK_PICTURES_DIR = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    "FBLA-Nationals-Project",
    "FBLA-Nationals-Project-main",
    "pictures",
)

# ----- Color palette (RGB tuples) used across both themes -----
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 180, 255)
GREEN = (80, 200, 120)
RED = (255, 0, 0)
GRAY = (220, 220, 220)
PURPLE = (201, 185, 255)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144, 238, 144)
NAVY = (15, 22, 52)
GOLD = (240, 190, 60)
LIGHT = (235, 236, 242)
PINK = (255, 192, 203)
BLUE_OPTION = (70, 120, 255)


# Fonts (Comic Sans for a playful, 2000s nostalgic feel) at different
# sizes/weights for titles, questions, answer options, feedback text, etc.
title_font = pygame.font.SysFont("comic sans ms", 36, bold=True)
question_font = pygame.font.SysFont("comic sans ms", 20)
option_font = pygame.font.SysFont("comic sans ms", 24)
feedback_font = pygame.font.SysFont("comic sans ms", 30, bold=True)
small_font = pygame.font.SysFont("comic sans ms", 16)
prompt_font = pygame.font.SysFont("comic sans ms", 22, bold=True)

# THEMES holds two complete color schemes (light/dark). Each screen's
# draw() call looks up colors by key (e.g. theme["background"]) instead
# of hardcoding colors, so the whole UI can be re-skinned by changing
# theme_mode below.
THEMES = {
    "light": {
        "background": WHITE,
        "surface": (245, 245, 245),
        "text": BLACK,
        "title": BLACK,
        "button": (220, 220, 220),
        "button_selected": (80, 80, 80),
        "button_text": BLACK,
        "input_bg": WHITE,
        "input_border": (60, 60, 60),
        "input_text": BLACK,
        "accent": (60, 60, 60),
        "feedback_shadow": (200, 200, 200),
    },
    "dark": {
        "background": BLACK,
        "surface": (30, 30, 30),
        "text": WHITE,
        "title": WHITE,
        "button": (100, 180, 255),
        "button_selected": (200, 200, 200),
        "button_text": BLACK,
        "input_bg": (40, 40, 40),
        "input_border": (180, 180, 180),
        "input_text": WHITE,
        "accent": (200, 200, 200),
        "feedback_shadow": (50, 50, 50),
    }
}

# Tracks which theme ("light" or "dark") is currently active. Toggled by
# clicking the theme button; read by draw() to pick colors from THEMES.
theme_mode = "light"


def load_image(filename, max_size=(520, 240)):
    """Load an image for a question from the images folder, scaled down
    to fit within max_size while preserving aspect ratio. Returns None if
    no filename is given, the file doesn't exist, or it fails to load,
    so the game can run fine without artwork for every question."""
    if not filename:
        return None
    candidate_paths = [
        os.path.join(PICTURES_DIR, filename),
        os.path.join(FALLBACK_PICTURES_DIR, filename),
        os.path.join(IMAGE_DIR, filename),
        os.path.join(os.path.dirname(__file__), filename),
    ]
    path = None
    for candidate in candidate_paths:
        if os.path.isfile(candidate):
            path = candidate
            break
    if path is None:
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
        iw, ih = image.get_size()
        mw, mh = max_size
        # Scale down only (never up) so small images aren't stretched/blurred.
        scale = min(mw / iw, mh / ih, 1)
        image = pygame.transform.smoothscale(image, (int(iw * scale), int(ih * scale)))
        return image
    except pygame.error:
        return None


def round_image_corners(image, radius=15):
    """Create a copy of the image with rounded corners."""
    if image is None:
        return None
    
    # Create a new surface with per-pixel alpha
    rounded = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    
    # Draw rounded rectangle mask
    rect = rounded.get_rect()
    pygame.draw.ellipse(rounded, (255, 255, 255, 255), pygame.Rect(0, 0, radius * 2, radius * 2))
    pygame.draw.ellipse(rounded, (255, 255, 255, 255), pygame.Rect(rect.width - radius * 2, 0, radius * 2, radius * 2))
    pygame.draw.ellipse(rounded, (255, 255, 255, 255), pygame.Rect(0, rect.height - radius * 2, radius * 2, radius * 2))
    pygame.draw.ellipse(rounded, (255, 255, 255, 255), pygame.Rect(rect.width - radius * 2, rect.height - radius * 2, radius * 2, radius * 2))
    pygame.draw.rect(rounded, (255, 255, 255, 255), pygame.Rect(radius, 0, rect.width - radius * 2, rect.height))
    pygame.draw.rect(rounded, (255, 255, 255, 255), pygame.Rect(0, radius, rect.width, rect.height - radius * 2))
    
    # Apply the mask to the image
    rounded.blit(image, (0, 0))
    return rounded


def create_tone_sound(frequency, duration=0.35, amplitude=14000):
    """Generate a single sine-wave tone as a pygame Sound, entirely in
    code (no external audio files). An attack/release envelope fades the
    volume in and out so the tone doesn't click or pop."""
    sample_rate = 44100
    samples = array.array('h')
    total_samples = int(sample_rate * duration)
    attack = int(total_samples * 0.15)
    release = int(total_samples * 0.2)

    for i in range(total_samples):
        phase = i / sample_rate
        envelope = 1.0
        if i < attack:
            envelope = i / attack
        elif i > total_samples - release:
            envelope = (total_samples - i) / release

        value = int(amplitude * envelope * math.sin(2 * math.pi * frequency * phase))
        samples.append(value)

    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


# --- The functions below (create_correct_sound, create_login_intro,
# create_background_music, create_wrong_sound, create_celebration_sound)
# all follow the same pattern as create_tone_sound above: build a buffer
# of raw audio samples sample-by-sample using sine waves, apply a
# fade-in/fade-out envelope to avoid clicks, and wrap the result in a
# pygame.mixer.Sound. They differ only in which frequencies/durations/
# volumes they use to produce a distinct musical effect for each
# in-game event. ---

def create_correct_sound():
    """Create an ascending three-note melody for correct answers."""
    sample_rate = 44100
    duration = 0.6
    frequencies = [523, 659, 784]  # C, E, G (ascending notes)
    note_duration = duration / len(frequencies)
    samples = array.array('h')

    for note_idx, freq in enumerate(frequencies):
        note_samples = int(sample_rate * note_duration)
        attack = int(note_samples * 0.1)
        release = int(note_samples * 0.3)

        for i in range(note_samples):
            phase = i / sample_rate
            envelope = 1.0
            if i < attack:
                envelope = i / attack
            elif i > note_samples - release:
                envelope = (note_samples - i) / release

            value = int(16000 * envelope * math.sin(2 * math.pi * freq * phase))
            samples.append(value)

    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


def create_login_intro():
    """Create a slow, gentle startup sound for the login screen."""
    sample_rate = 44100
    duration = 5.6
    # Warm ascending notes with long sustain for a calm intro.
    notes = [220, 262, 294, 330]  # A3, C4, D4, E4
    note_duration = duration / len(notes)
    samples = array.array('h')

    for freq in notes:
        note_samples = int(sample_rate * note_duration)
        attack = int(note_samples * 0.2)
        release = int(note_samples * 0.45)

        for i in range(note_samples):
            phase = i / sample_rate
            envelope = 1.0
            if i < attack:
                envelope = i / attack
            elif i > note_samples - release:
                envelope = (note_samples - i) / release

            # Keep harmonics subtle to avoid harshness.
            value = int(10000 * envelope * (
                0.85 * math.sin(2 * math.pi * freq * phase) +
                0.12 * math.sin(2 * math.pi * freq * 2 * phase) +
                0.03 * math.sin(2 * math.pi * freq * 3 * phase)
            ))
            samples.append(value)

    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


def create_background_music():
    """Create engaging looping background music with rhythm and harmony."""
    sample_rate = 44100
    duration = 6.0  # 6 seconds of music that will loop
    samples = array.array('h')

    # Create a more complex musical pattern
    # Pattern: bass + melody with rhythm
    total_samples = int(sample_rate * duration)

    for i in range(total_samples):
        time = i / sample_rate
        phase = time

        # Bass line - steady low note with rhythm
        bass_freq = 110  # A2
        bass_volume = 8000

        # Melody line - cycles through a fixed list of notes, picking the
        # current note based on how far through the loop we are.
        melody_freqs = [440, 494, 523, 587, 659, 587, 523, 494]  # A, B, C, D, E, D, C, B
        melody_pos = int((time % duration) * len(melody_freqs) / duration)
        melody_freq = melody_freqs[melody_pos % len(melody_freqs)]
        melody_volume = 7000

        # Add some swing/rhythm to melody with envelope: the melody fades
        # in and out twice per second to create a pulsing rhythmic feel.
        beat_phase = (time * 2) % 1.0  # 2 beats per second
        if beat_phase < 0.3:
            melody_envelope = beat_phase / 0.3
        elif beat_phase < 0.6:
            melody_envelope = 1.0
        else:
            melody_envelope = max(0, (1.0 - beat_phase) / 0.4)

        # Harmony - minor third above bass, adds fullness to the mix
        harmony_freq = 440 * 1.2  # Creates nice harmony
        harmony_volume = 5000

        # Generate each layer's waveform, then mix (add) them together.
        bass_wave = math.sin(2 * math.pi * bass_freq * phase) * bass_volume
        melody_wave = math.sin(2 * math.pi * melody_freq * phase) * melody_volume * melody_envelope
        harmony_wave = math.sin(2 * math.pi * harmony_freq * phase) * harmony_volume * 0.5

        # Combine with slight compression, then clamp to the valid
        # 16-bit signed sample range so the mixed audio doesn't clip/wrap.
        combined = (bass_wave + melody_wave + harmony_wave) * 0.9
        value = int(max(-32768, min(32767, combined)))
        samples.append(value)

    try:
        sound = pygame.mixer.Sound(buffer=samples)
        return sound
    except Exception:
        return None



def create_wrong_sound():
    """Create a descending two-note buzz for wrong answers."""
    sample_rate = 44100
    duration = 0.5
    frequencies = [440, 220]  # A, A (lower octave)
    note_duration = duration / len(frequencies)
    samples = array.array('h')

    for note_idx, freq in enumerate(frequencies):
        note_samples = int(sample_rate * note_duration)
        attack = int(note_samples * 0.05)
        release = int(note_samples * 0.4)

        for i in range(note_samples):
            phase = i / sample_rate
            envelope = 1.0
            if i < attack:
                envelope = i / attack
            elif i > note_samples - release:
                envelope = (note_samples - i) / release

            value = int(12000 * envelope * math.sin(2 * math.pi * freq * phase))
            samples.append(value)

    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


def create_celebration_sound():
    """Create a short three-tone fanfare for a perfect/near-perfect score."""
    sample_rate = 44100
    duration = 0.8
    frequencies = [660, 880, 1040]
    samples = array.array('h')
    total_samples = int(sample_rate * duration)

    for i in range(total_samples):
        phase = i / sample_rate
        # Split the total duration evenly between the three frequencies.
        freq = frequencies[min(i // (total_samples // len(frequencies)), len(frequencies) - 1)]
        amplitude = int(18000 * math.sin(2 * math.pi * freq * phase))
        samples.append(amplitude)

    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


def create_yay_sound():
    """Create an upbeat, celebratory happy melody for quiz completion.
    Different from the intro - this is fast, cheerful, and uses a recognizable
    musical pattern (ascending then sustained notes for a 'victory' feel)."""
    sample_rate = 44100
    duration = 2.0  # Longer, more elaborate melody
    
    # Create a melodic pattern: ascending sequence followed by a triumphant hold
    # Pattern: C5 -> E5 -> G5 -> C6 (triumphant) with varying durations
    notes_with_durations = [
        (523, 0.3),   # C5 - quick start
        (659, 0.3),   # E5 - ascending
        (784, 0.3),   # G5 - continuing up
        (1047, 0.8),  # C6 - triumphant high note, held longer
        (880, 0.2),   # B5 - cascade down slightly
    ]
    
    samples = array.array('h')
    
    for freq, note_dur in notes_with_durations:
        note_samples = int(sample_rate * note_dur)
        attack = int(note_samples * 0.08)
        release = int(note_samples * 0.2)
        
        for i in range(note_samples):
            phase = i / sample_rate
            envelope = 1.0
            if i < attack:
                envelope = i / attack
            elif i > note_samples - release:
                envelope = (note_samples - i) / release
            
            # Bright, cheerful amplitude
            value = int(17000 * envelope * math.sin(2 * math.pi * freq * phase))
            samples.append(value)
    
    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


def play_sound(sound):
    """Safely play a Sound object, ignoring errors (e.g. if sound
    generation failed earlier and `sound` is None)."""
    if sound:
        try:
            sound.play()
        except Exception:
            pass


# Pre-generate every sound effect once at startup so there's no delay
# during gameplay when a sound needs to play.
celebration_sound = create_celebration_sound()
correct_sound = create_correct_sound()
wrong_sound = create_wrong_sound()
login_intro_sound = create_login_intro()
background_music = create_background_music()
yay_sound = create_yay_sound()

# One-shot flags so intro/celebration sounds only play once per screen
# visit instead of replaying every frame.
celebration_played = False
login_intro_played = False
background_music_playing = False
yay_played = False
music_muted = False


class AuthManager:
    """Handles everything to do with checking, creating, and storing accounts."""
    def __init__(self, data_filepath):
        self.filepath = data_filepath
        # Load all saved accounts/high scores into memory once at startup.
        self.user_data = self._load_all_data()

    def _load_all_data(self):
        """Read the JSON save file into a dict. Returns an empty dict if
        the file doesn't exist yet or is corrupted/unreadable."""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError):
            return {}

    def _save_all_data(self):
        """Write the current in-memory user_data dict back out to disk
        as JSON. Silently ignores write errors (e.g. read-only disk)."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(self.user_data, file, indent=2)
        except OSError:
            pass

    def register_user(self, username, password):
        """Create a new account if the username/password are valid and
        the username isn't already taken. Returns (success, message)."""
        if not username or not password:
            return False, "Enter a username and password to register."
        if username in self.user_data:
            return False, "Username already exists. Choose another name."

        self.user_data[username] = {
            "password": password,
            "high_score": 0
        }
        self._save_all_data()
        return True, "Account created! You may sign in now."

    def authenticate(self, username, password):
        """Check a username/password pair against stored accounts.
        Returns (success, message)."""
        if not username or not password:
            return False, "Please fill in both fields."
        if username in self.user_data and self.user_data[username]["password"] == password:
            return True, "Loaded your profile."
        return False, "Invalid username or password."

    def save_high_score(self, username, final_score):
        """Update the player's stored high score if their latest run beat
        it. Guest sessions are never saved since there's no account."""
        if username == "Guest":
            return
        if username in self.user_data:
            if final_score > self.user_data[username].get("high_score", 0):
                self.user_data[username]["high_score"] = final_score
                self._save_all_data()


class InputBox:
    """A clickable, typeable text field used for the username/password
    fields on the login screen. Supports an optional password-mask mode
    and a temporary blinking-border 'hint' to draw the player's eye."""
    def __init__(self, rect, placeholder="", is_password=False):
        self.rect = pygame.Rect(rect)
        self.color = WHITE
        self.text = ""
        self.active = False  # True when this box currently has focus
        self.placeholder = placeholder
        self.hint_blink_until = 0  # timestamp (ms) the blink effect ends
        self.is_password = is_password

    def trigger_hint_blink(self, duration_ms=2800):
        """Start a temporary blinking-gold-border effect on this box,
        e.g. to draw attention to the sign-in fields after registering."""
        self.hint_blink_until = pygame.time.get_ticks() + duration_ms

    def handle_event(self, event):
        """Process a single pygame event: clicking focuses/unfocuses the
        box, and typing while focused edits its text (with backspace
        support and a max length of 18 characters)."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = GOLD if self.active else WHITE
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                pass  # Enter key does nothing here; sign-in needs a button click
            elif event.unicode.isprintable() and len(self.text) < 18:
                self.text += event.unicode

    def draw(self, surface, theme=None):
        # Use theme-aware colors when drawing inputs
        if theme is None:
            theme = THEMES[theme_mode]
        bg = theme.get("input_bg", LIGHT)
        border = theme.get("input_border", WHITE)
        text_color = theme.get("input_text", BLACK)
        placeholder_color = theme.get("text", GRAY)
        now = pygame.time.get_ticks()

        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        border_color = border if not self.active else theme.get("button_selected", GOLD)

        # Briefly blink the border after account creation to prompt sign-in fields.
        if now < self.hint_blink_until:
            blink_on = ((now // 220) % 2) == 0
            if blink_on:
                border_color = GOLD

        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)
        if self.text:
            # Show dots instead of real characters for password fields.
            display_text = "•" * len(self.text) if self.is_password else self.text
            txt = option_font.render(display_text, True, text_color)
            surface.blit(txt, (self.rect.x + 10, self.rect.y + 8))
        else:
            # No text typed yet: show the gray placeholder hint instead.
            txt = option_font.render(self.placeholder, True, placeholder_color)
            surface.blit(txt, (self.rect.x + 10, self.rect.y + 8))

        # Draw a blinking cursor in the active input box.
        if self.active and ((now // 500) % 2) == 0:
            cursor_text = "•" * len(self.text) if self.is_password else self.text
            rendered = option_font.render(cursor_text, True, text_color)
            caret_x = min(self.rect.right - 12, self.rect.x + 10 + rendered.get_width() + 2)
            caret_top = self.rect.y + 9
            caret_bottom = self.rect.y + self.rect.height - 9
            pygame.draw.line(surface, text_color, (caret_x, caret_top), (caret_x, caret_bottom), 2)


# Initialize Auth Layer
auth = AuthManager(DATA_FILE)
current_user = "Guest"

# State Control: tracks which screen is currently active, e.g.
# "login", "home", "category_select", "tutorial", "game",
# "bonus_offer", "facts_view", or "final_summary". The main loop's
# draw() and event-handling code both branch on this value.
game_state = "login"
auth_message = "Sign in or play as a guest player!"

# Input fields and system buttons
username_box = InputBox((220, 180, 360, 45), "Username")
password_box = InputBox((220, 240, 360, 45), "Password",is_password=True)


# All trivia questions, grouped by category. Each question dict has the
# question text, a list of answer options, the correct "answer" string
# (must exactly match one of the options), and an optional "image" file.
question_categories = {
    "Technology": [
        {
            "question": "Which social media platform was founded by Mark Zuckerberg in 2004?",
            "options": ["Twitter", "Facebook", "MySpace", "Friendster"],
            "answer": "Facebook",
            "image": "mark.png"
        },
        {
            "question": "What popular video-sharing website was founded in 2005?",
            "options": ["Vimeo", "YouTube", "Dailymotion", "Metacafe"],
            "answer": "YouTube",        
            "image": "computer.png"
        },
        {
            "question": "Which music player device was released by Apple in 2001?",
            "options": ["iPad", "iPod", "Apple Watch", "AirPods"],
            "answer": "iPod",           
            "image": "apple.png"
        },
        {
            "question": "What streaming technology did Netflix introduce in 2007?",
            "options": ["Internet streaming", "Downloading", "Satellite", "Bluetooth"],
            "answer": "Internet streaming",
            "image": "netflix.png"
        },
        {
            "question": "What year was the first iPhone released?",
            "options": ["2001", "2002", "2004", "2007"],
            "answer": "2007",
            "image": "iphone.png"
        },
        {
            "question": "Which gaming console was released by Microsoft in 2005?",
            "options": ["Xbox", "Xbox 360", "Wii", "PlayStation 2"],
            "answer": "Xbox 360",
            "image": "microsoft.png"
        }
    ],
    "Celebrities & More": [
        {
            "question": "Michael Jackson is known as the King of what?",
            "options": ["Jazz", "Rock", "Pop", "Blues"],
            "answer": "Pop",
            "image": "michael.png"
        },
        {
            "question": "Who did Michael Jackson start a band with?",
            "options": ["Brothers", "Parents", "Neighbors", "Cousins"],
            "answer": "Brothers",       
            "image": "band.png"
        },
        {
            "question": "What was the name of the lost clownfish that a father searches for across the ocean?",
            "options": ["Nemo", "Dory", "Shrek", "The Lord of the Rings"],
            "answer": "Nemo",       
            "image": "fish.png"
        },
        {
            "question": "Which girl group was a huge phenomenon in the early 2000s?",
            "options": ["The Pussycat Dolls", "Destiny's Child", "Spice Girls", "TLC"],
            "answer": "Destiny's Child",
            "image": "girl.png"         
        },
        {
            "question": "Which reality singing competition featured Jennifer Lopez, Simon Cowell, and Steve Tyler?",
            "options": ["The Voice", "American Idol", "The X Factor", "Dancing with Stars"],
            "answer": "American Idol",
            "image": "mic.png"          
        },
        {
            "question": "What movie was released in 2000?",
            "options": ["Gladiator", "The Matrix", "X-Men", "The Lord of the Rings"],
            "answer": "X-Men",      
            "image": "tv.png"
        }
    ],
    "Historical Events": [
        {
            "question": "What were the Twin Towers rebuilt as?",
            "options": ["One World Trade Center", "Empire State Building", "Burj Khalifa", "Shanghai Tower"],
            "answer": "One World Trade Center",
            "image": "tt.png"
        },
        {
            "question": "When did Hurricane Katrina hit New Orleans?",
            "options": ["Aug 22nd", "Aug 3rd", "Aug 23rd", "Aug 29th"],
            "answer": "Aug 29th",       
            "image": "hk.png"
        },
        {
            "question": "What was the financial crisis of 2008 primarily caused by?",
            "options": ["Dot-com bubble", "Housing market collapse", "Oil prices", "Tech stocks"],
            "answer": "Housing market collapse",
            "image": "sm.png"
        },
        {
            "question": "In what year did Barack Obama become the 44th President of the United States?",
            "options": ["2006", "2007", "2008", "2009"],
            "answer": "2008",
            "image": "house.png"                         
        },
        {
            "question": "Which movie featuring avatar-like aliens was released in 2009?",
            "options": ["Transformers", "Avatar", "Inception", "District 9"],
            "answer": "Avatar",
            "image": "alien.png"     
        },
        {
            "question": "Which pirate-themed movie franchise launched in 2003?",
            "options": ["Pirates of the Caribbean", "Treasure Island", "The Black Pirate", "Captain Hook"],
            "answer": "Pirates of the Caribbean",
            "image": "pirate.png"
        }
    ]
}

# Short trivia "fun facts" shown on the bonus-question offer screen,
# keyed by the same category names as question_categories.
category_facts = {
    "Technology": [
        "Facebook launched in 2004 and quickly became one of the most used social platforms.",
        "The first iPhone was released in 2007 and changed how people used smartphones.",
        "YouTube launched in 2005 and helped make video sharing a daily habit online."
    ],
    "Celebrities & More": [
        "Michael Jackson became known worldwide as the King of Pop.",
        "Disney Pixar's Finding Nemo was released in 2003 and became a huge family favorite.",
        "American Idol helped launch several major music careers in the 2000s."
    ],
    "Historical Events": [
        "The financial crisis of 2008 caused major changes in banking and housing markets.",
        "Barack Obama became the 44th U.S. President in 2009.",
        "Hurricane Katrina hit New Orleans in 2005 and became one of the most remembered disasters in U.S. history."
    ]
}

# Which category's facts to show, and which screen to return to
# afterward ("bonus_offer" by default).
facts_view_category = None
facts_return_state = "bonus_offer"

# ----- Core gameplay/progress state (all global, mutated by the
#       functions below as the player moves through the quiz) -----
current_questions = []      # The list of question dicts for the active round
question_index = 0          # Index into current_questions for the current question
score = 0                   # Running total of correct answers (current round)
total_questions = 0         # Running total of questions answered (current round)
session_base_score = 0      # Sum of base (non-bonus) points across all completed categories
current_category_base_score = 0  # Base points earned in the category currently in progress
bonus_points = 0            # Total bonus points earned this session
session_base_answered = 0   # Number of base questions answered this session
session_bonus_answered = 0  # Number of bonus questions answered this session
current_is_bonus = False    # True while the player is answering a bonus question
bonus_used = False          # True once the bonus offer has been accepted or declined
bonus_taken = False         # True if the player chose to attempt the bonus question
bonus_offer = False         # True while the bonus-offer screen is being shown
selected_category = None    # Category name currently being played
last_completed_category = None  # Most recently finished category (used for facts/bonus context)
completed_categories = set()     # Categories the player has already finished this session
selected_option = None      # The answer option text the player has clicked
current_question_image = None    # Loaded pygame Surface for the current question's image, if any
game_over = False           # True when the current round (5 questions + optional bonus) has ended
show_category_facts = False # (unused flag reserved for future use)
final_summary_confetti = []

# Prevent immediate mouse-click propagation when switching screens
ignore_mouse = False

feedback = ""
feedback_color = BLACK
bottom_question_prompt = "Please choose one of the answers above"


class Button:
    """A clickable rectangular button with text, used for nearly every
    interactive element in the game (menus, answer choices, etc.)."""
    def __init__(self, x, y, w, h, text, color=None, enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color  # Custom color override
        self.enabled = enabled

    def get_text_color(self, bg_color):
        """Return correct text color based on your rules."""
        special_colors = [BLUE, GREEN, GOLD, PINK, WHITE]

        if bg_color in special_colors:
            return BLACK
        return WHITE

    def draw(self, surface, selected=False, theme=None):
        if theme is None:
            theme = THEMES[theme_mode]

        # Determine base color: explicit override > selected/default theme color
        if self.color is not None:
            base_color = self.color
        else:
            base_color = theme["button_selected"] if selected else theme["button"]

        # Dark mode overrides: a couple of buttons get special colors
        # in dark mode so they stand out against the dark background.
        if theme_mode == "dark":
            if self.text.lower() == "next":
                base_color = PURPLE
            if "option" in self.text.lower():
                base_color = BLUE

        # Disabled state: gray out the button (e.g. a completed category).
        if not self.enabled:
            base_color = (120, 120, 120)

        # Draw button background + outline
        pygame.draw.rect(surface, base_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme["text"], self.rect, 2, border_radius=10)

        # Text color logic: use the theme's button_text color (black in
        # both light and dark themes) so option/answer text always
        # renders black.
        text_color = theme.get("button_text", self.get_text_color(base_color))

        if theme_mode == "light" and self.text.lower() == "next":
            text_color = BLACK

        if theme_mode == "dark" and self.text.lower() == "next":
            text_color = BLACK

        if self.text.lower() == "skip bonus":
            text_color = BLACK
        
        # Theme and music toggle buttons always use black text for visibility.
        if self.text in ["Dark Mode", "Light Mode", "Mute Music", "Unmute Music"]:
            text_color = BLACK

        # Render text centered on the button
        txt = option_font.render(self.text, True, text_color)
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def is_clicked(self, pos):
        """Return True if this button is enabled and pos (mouse
        coordinates) falls within its rectangle."""
        return self.enabled and self.rect.collidepoint(pos)

def create_buttons():
    """Create the 4 answer-option buttons used during gameplay. Their
    text/position get updated each question by load_question()."""
    buttons = []
    for i in range(4):
        buttons.append(Button(200, 150 + i * 60, 400, 45, ""))
    return buttons

buttons = create_buttons()
next_button = Button(620, 420, 150, 50, "NEXT")
theme_toggle_btn = Button(WIDTH - 180, 20, 160, 40, "Dark Mode")
music_toggle_btn = Button(20, 20, 160, 40, "Mute Music")
main_menu_button = Button(220, 320, 170, 45, "Continue", BLUE)
game_over_facts_btn = Button(410, 320, 170, 45, "View Facts", GREEN)
final_summary_menu_btn = Button(315, 430, 170, 45, "Back to Login", BLUE)
bonus_round_button = Button(410, 320, 170, 45, "Bonus 3", GREEN)

# Login system controls
login_btn = Button(220, 310, 170, 45, "Sign In", BLUE)
register_btn = Button(410, 310, 170, 45, "Register", GREEN)
guest_btn = Button(220, 370, 360, 45, "Play as Guest", GOLD)

# Home / Tutorial buttons (shown after successful login)
# Positioned higher so they don't overlap login buttons
home_start_btn = Button(220, 200, 170, 45, "Start Quiz", BLUE)
home_tutorial_btn = Button(410, 200, 170, 45, "Tutorial", GREEN)
home_logout_btn = Button(220, 260, 360, 45, "Log Out", GOLD)

# Category-selection screen buttons
category_tech_btn = Button(180, 180, 260, 60, "Technology", BLUE)
category_celebrity_btn = Button(180, 260, 260, 60, "Celebrities & More", GREEN)
category_history_btn = Button(180, 340, 260, 60, "Historical Events", GOLD)
category_back_btn = Button(460, 420, 260, 60, "Back", RED)

# Bonus-offer / facts-view screen buttons
bonus_question_button = Button(180, 320, 260, 55, "Bonus Question", BLUE)
skip_bonus_button = Button(460, 320, 260, 55, "Skip Bonus", GRAY)
facts_view_button = Button(315, 385, 170, 45, "View Facts", GREEN)
facts_back_button = Button(WIDTH // 2 - 85, HEIGHT - 70, 170, 45, "Back", BLUE)

# Tutorial screen buttons (different positions)
tutorial_start_btn = Button(220, 360, 170, 45, "Start Quiz", BLUE)
tutorial_back_btn = Button(410, 360, 170, 45, "Back", GREEN)


# Total number of "base" (non-bonus) questions across a full session:
# 5 questions per category times the number of categories.
TOTAL_BASE_QUESTIONS = len(question_categories) * 5
TOTAL_MAX_QUESTIONS = TOTAL_BASE_QUESTIONS + len(question_categories)
final_win_image = load_image("win.png", max_size=(220, 160))

def reset_quiz_progress():
    """Clear all session-wide progress tracking, e.g. when starting a
    brand-new playthrough after logging out or finishing all categories."""
    global completed_categories, session_base_score, current_category_base_score, bonus_points
    global session_base_answered, session_bonus_answered
    completed_categories = set()
    session_base_score = 0
    current_category_base_score = 0
    bonus_points = 0
    session_base_answered = 0
    session_bonus_answered = 0

def build_quiz_questions(source_questions, question_count=None):
    """Pick a random sample of questions from a category's question
    list (or all of them if question_count is None), and shuffle each
    question's answer options so the correct answer isn't always in the
    same position. Returns a fresh list of simplified question dicts
    (only question/options/answer; images are looked up separately)."""
    if question_count is None:
        question_count = len(source_questions)
    return [
        {
            "question": q["question"],
            "options": random.sample(q["options"], len(q["options"])),
            "answer": q["answer"],
            "image": q.get("image")
        }
        for q in random.sample(source_questions, question_count)
    ]


def start_game(question_list, starting_score=0, starting_total=None, reset_bonus=True, question_count=None, is_bonus=False):
    """Begin a new round of questions. Used both for starting a fresh
    category (5 random questions) and for setting up a single bonus
    question. Resets all the per-round tracking variables and loads
    the first question onto screen."""
    global current_questions, question_index, score, total_questions, bonus_used, selected_option, game_over, feedback, feedback_color, bonus_taken, bonus_offer, current_is_bonus, current_category_base_score
    print("DEBUG: start_game() called")
    if reset_bonus:
        bonus_used = False
        bonus_taken = False
        bonus_offer = False
    current_is_bonus = is_bonus
    # Only reset the category's base score when starting a brand-new
    # category (not when this call is for a bonus question).
    current_category_base_score = 0 if not is_bonus else current_category_base_score
    current_questions = build_quiz_questions(question_list, question_count)
    question_index = 0
    score = starting_score
    total_questions = len(current_questions) if starting_total is None else starting_total + len(current_questions)
    selected_option = None
    game_over = False
    feedback = ""
    feedback_color = BLACK
    load_question()


def start_category(category_name):
    """Kick off a 5-question round for the chosen category and switch
    the screen to "game"."""
    global selected_category, game_state, last_completed_category
    selected_category = category_name
    last_completed_category = None
    start_game(question_categories[category_name], question_count=5, is_bonus=False)
    game_state = "game"


def start_bonus_question():
    """Pick one random question from the current category that the
    player hasn't already seen this round, and present it as a single
    bonus question. If every question in the category has already been
    used, skip the bonus and end the round instead."""
    global current_questions, question_index, total_questions, bonus_used, bonus_taken, selected_option, feedback, feedback_color, game_state, game_over, bonus_offer, current_is_bonus
    used_questions = {q["question"] for q in current_questions}
    available_bonus = [q for q in question_categories[selected_category] if q["question"] not in used_questions]
    if not available_bonus:
        bonus_offer = False
        game_over = True
        auth.save_high_score(current_user, score)
        return

    bonus_q = random.choice(available_bonus)
    current_questions = [{
        "question": bonus_q["question"],
        "options": random.sample(bonus_q["options"], len(bonus_q["options"])),
        "answer": bonus_q["answer"],
        "image": bonus_q.get("image")
    }]
    question_index = 0
    total_questions += 1
    selected_option = None
    feedback = ""
    feedback_color = BLACK
    bonus_used = True
    bonus_taken = True
    bonus_offer = False
    current_is_bonus = True
    game_state = "game"
    game_over = False
    load_question()


def go_to_category_select():
    """Switch to the category-selection screen and stop the looping
    background music (it's only meant to play on the login/home screens)."""
    global game_state, background_music_playing
    game_state = "category_select"
    if background_music_playing:
        background_music.stop()
        background_music_playing = False


def open_facts_view(category_name, return_state="bonus_offer"):
    """Show the 'fun facts' screen for a category, remembering which
    screen to return to (Back button) afterward."""
    global game_state, facts_view_category, facts_return_state
    facts_view_category = category_name
    facts_return_state = return_state
    game_state = "facts_view"


def load_question():
    """Prepare the on-screen answer buttons for the current question:
    reset the selected answer, load the question's image (if any), and
    fill in each button's text from the shuffled answer options."""
    global selected_option, current_question_image
    selected_option = None
    q = current_questions[question_index]
    current_question_image = load_image(q.get("image"), max_size=(170, 120))
    for btn in buttons:
        btn.custom_color = BLUE_OPTION
    # NOTE: `btn` here is left over from the loop above (still refers to
    # the last button) and is drawn once outside the main draw() cycle;
    # this line has no visible effect since draw() redraws every frame.
    btn.draw(screen, selected=(selected_option == btn.text))
    for i in range(4):
        buttons[i].text = q["options"][i]
        buttons[i].color = None


def wrap_text(text, font, max_width):
    """Break a long string into multiple lines so it fits within
    max_width pixels when rendered with the given font, splitting on
    word boundaries (used for wrapping long question text)."""
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def create_final_summary_confetti(count=120):
    """Generate a static confetti field for the final summary screen."""
    confetti_colors = [LIGHT_BLUE, LIGHT_GREEN, GOLD, PINK, PURPLE, BLUE_OPTION, GREEN, RED]
    rng = random.Random(18)
    confetti = []
    for _ in range(count):
        confetti.append({
            "x": rng.randint(20, WIDTH - 20),
            "y": rng.randint(20, HEIGHT - 20),
            "w": rng.randint(4, 8),
            "h": rng.randint(8, 16),
            "color": rng.choice(confetti_colors),
        })
    return confetti


def check_answer():
    """Compare the player's selected option to the correct answer,
    update score/feedback, color-code the buttons (green for correct,
    red for an incorrect pick), and play the matching sound effect."""
    global feedback, feedback_color, score, session_base_score, current_category_base_score, bonus_points
    global session_base_answered, session_bonus_answered

    correct = current_questions[question_index]["answer"]

    # Make green less bright
    correct_highlight = (0, 180, 0)
    wrong_highlight = (200, 0, 0)

    # Highlight correct answer
    for btn in buttons:
        if btn.text == correct:
            btn.color = correct_highlight

    # Highlight wrong selected answer
    if selected_option != correct:
        for btn in buttons:
            if btn.text == selected_option:
                btn.color = wrong_highlight

    # Track every answered question so summary denominators can reflect
    # what the player actually attempted (including optional bonuses).
    if current_is_bonus:
        session_bonus_answered += 1
    else:
        session_base_answered += 1

    # Scoring logic + bottom-of-screen feedback text
    if selected_option == correct:
        score += 1
        # Bonus-question points are tracked separately from base
        # category points so the final summary can show both.
        if current_is_bonus:
            bonus_points += 1
        else:
            current_category_base_score += 1
        play_sound(correct_sound)
        feedback = "Correct!"
        feedback_color = (0, 170, 0)
    else:
        play_sound(wrong_sound)
        feedback = "Wrong!"
        feedback_color = (200, 0, 0)



def next_question():
    """Advance to the next question in the round, or, once the round's
    questions run out, either offer a bonus question or end the round
    entirely (saving the player's high score)."""
    global question_index, game_over, feedback, bonus_offer, bonus_taken, game_state, session_base_score, last_completed_category, selected_option, current_is_bonus
    question_index += 1
    feedback = ""

    if question_index >= len(current_questions):
        # First time finishing the 5 base questions: offer a bonus
        # question instead of ending immediately.
        if not bonus_taken and not bonus_offer:
            session_base_score += current_category_base_score
            last_completed_category = selected_category
            bonus_offer = True
            game_over = False
            selected_option = None
            current_is_bonus = False
            game_state = "bonus_offer"
            return
        # Reaching here means either the bonus question itself just
        # finished, or the bonus offer was already handled earlier.
        if not current_is_bonus:
            session_base_score += current_category_base_score
            completed_categories.add(selected_category)
            last_completed_category = selected_category
        game_over = True
        auth.save_high_score(current_user, score)
    else:
        load_question()



def draw():
    """Render the entire current frame. Branches on the global
    game_state to decide which screen's UI to draw: login, home,
    category_select, tutorial, game (questions + game-over summary),
    final_summary, bonus_offer, or facts_view. Called once per frame
    from the main loop before processing events."""
    global login_intro_played, background_music_playing, final_summary_confetti
    theme = THEMES[theme_mode]

    music_toggle_btn.text = "Unmute Music" if music_muted else "Mute Music"

    if game_state == "login":
        # Play the gentle intro chime once, the first time this screen
        # is shown, and start the looping background music.
        if not login_intro_played and not music_muted:
            play_sound(login_intro_sound)
            login_intro_played = True

        if music_muted and background_music_playing:
            background_music.stop()
            background_music_playing = False
        elif not music_muted and not background_music_playing:
            background_music.play(-1)  # Loop infinitely
            background_music_playing = True

        screen.fill(theme["background"])
        
        # Load and display the trivia.png image on the left side with rounded corners
        trivia_image = load_image("trivia.png", max_size=(180, 280))
        if trivia_image:
            trivia_image = round_image_corners(trivia_image, radius=15)
            img_y = HEIGHT // 2 - trivia_image.get_height() // 2
            screen.blit(trivia_image, (10, img_y))
        
        # Load and display the trivia2.png image on the right side with rounded corners
        trivia2_image = load_image("trivia2.png", max_size=(180, 280))
        if trivia2_image:
            trivia2_image = round_image_corners(trivia2_image, radius=15)
            img_y = HEIGHT // 2 - trivia2_image.get_height() // 2
            screen.blit(trivia2_image, (WIDTH - 190, img_y))
        
        title = title_font.render("2000's Trivia Challenge", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        username_box.draw(screen, theme)
        password_box.draw(screen, theme)

        login_btn.draw(screen, False, theme)
        register_btn.draw(screen, False, theme)
        guest_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)
        music_toggle_btn.draw(screen, False, theme)

        if auth_message:
            msg_surface = small_font.render(auth_message, True, theme["text"])
            screen.blit(msg_surface, (WIDTH // 2 - msg_surface.get_width() // 2, 440))

    elif game_state == "home":
        # Home screen: shown after a successful login or guest start.
        # Keep background music playing
        if music_muted and background_music_playing:
            background_music.stop()
            background_music_playing = False
        elif not music_muted and not background_music_playing:
            background_music.play(-1)  # Loop infinitely
            background_music_playing = True

        screen.fill(theme["background"])
        title = title_font.render("2000's Trivia Challenge", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        welcome_text = question_font.render(f"Welcome, {current_user}!", True, theme["text"])
        screen.blit(welcome_text, (WIDTH // 2 - welcome_text.get_width() // 2, 120))

        # Only show a high score for registered accounts (Guests don't
        # have saved data).
        if current_user != "Guest" and current_user in auth.user_data:
            high_score = auth.user_data[current_user].get("high_score", 0)
            high_score_text = question_font.render(f"High Score: {high_score} points", True, theme["accent"])
            screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, 160))

        home_start_btn.draw(screen, False, theme)
        home_tutorial_btn.draw(screen, False, theme)
        home_logout_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)
        music_toggle_btn.draw(screen, False, theme)

        # Load and display the trivia3.png image at the bottom with rounded corners
        trivia3_image = load_image("trivia3.png", max_size=(650, 120))
        if trivia3_image:
            trivia3_image = round_image_corners(trivia3_image, radius=15)
            img_x = WIDTH // 2 - trivia3_image.get_width() // 2
            screen.blit(trivia3_image, (img_x, HEIGHT - 150))

    elif game_state == "category_select":
        # Category-select screen: stop music here since gameplay
        # screens are meant to be quieter/more focused.
        if background_music_playing:
            background_music.stop()
            background_music_playing = False

        screen.fill(theme["background"])
        title = title_font.render("Choose a Quiz Category", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        if completed_categories:
            prompt = question_font.render("Completed categories are locked. Pick a new one:", True, theme["text"])
        else:
            prompt = question_font.render("Select one of the categories below:", True, theme["text"])
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 120))

        # Disable (gray out) any category the player has already finished.
        category_tech_btn.enabled = "Technology" not in completed_categories
        category_celebrity_btn.enabled = "Celebrities & More" not in completed_categories
        category_history_btn.enabled = "Historical Events" not in completed_categories

        category_tech_btn.draw(screen, False, theme)
        category_celebrity_btn.draw(screen, False, theme)
        category_history_btn.draw(screen, False, theme)
        category_back_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)

    elif game_state == "tutorial":
        # Simple instructions screen explaining how to play.
        screen.fill(theme["background"])
        title = title_font.render("2000's Trivia Challenge - Tutorial", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        tutorial_text = [
            "Welcome to the 2000's Trivia Challenge!",
            "",
            "1. Select a category to start a 5-question quiz.",
            "2. Answer each question and click NEXT.",
            "3. After your 5 questions, you can attempt a bonus question.",
            "4. A correct bonus answer adds one extra point.",
            "5. Your highest score is saved to your profile.",
            "",
            
        ]

        y_pos = 130
        for line in tutorial_text:
            text = question_font.render(line, True, theme["text"])
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y_pos))
            y_pos += 30

        tutorial_start_btn.draw(screen, False, theme)
        tutorial_back_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)

    elif game_state == "game":
        screen.fill(theme["surface"])

        title = title_font.render("2000's Trivia Challenge", True, theme["title"])
        screen.blit(title, (190, 30))

        if not game_over:
            q = current_questions[question_index]

            question_lines = wrap_text(q["question"], question_font, 520)
            for i, line in enumerate(question_lines):
                question_text = question_font.render(line, True, theme["text"])
                screen.blit(question_text, (150, 100 + i * 30))

            question_bottom = 100 + len(question_lines) * 30
            image_height = 0
            if current_question_image:
                img_rect = current_question_image.get_rect(topleft=(20, HEIGHT - current_question_image.get_height() - 20))
                screen.blit(current_question_image, img_rect)
                image_height = 0

            answer_start_y = question_bottom + image_height + 20
            choice_theme = dict(theme)
            choice_theme["button"] = BLUE_OPTION
            choice_theme["button_selected"] = GREEN
            choice_theme["button_text"] = BLACK
            for i, btn in enumerate(buttons):
                btn.rect.y = answer_start_y + i * 60
                btn.draw(screen, btn.text == selected_option, choice_theme)

            next_button.draw(screen, False, theme)

            score_text = option_font.render(f"Score: {score}/{total_questions}", True, theme["text"])
            screen.blit(score_text, (650, 20))

            if current_is_bonus:
                progress_label = "Bonus Question"
            else:
                progress_label = f"Question {question_index + 1}/{len(current_questions)}"
            progress_text = prompt_font.render(progress_label, True, theme["accent"])
            screen.blit(progress_text, (780 - progress_text.get_width(), 50))

            user_text = small_font.render(f"Player: {current_user}", True, theme["text"])
            screen.blit(user_text, (20, 20))

            if feedback:
                shadow = feedback_font.render(feedback, True, theme["feedback_shadow"])
                text = feedback_font.render(feedback, True, feedback_color)
                rect = text.get_rect(center=(WIDTH // 2, 440))
                screen.blit(shadow, (rect.x + 3, rect.y + 3))
                screen.blit(text, rect)
            else:
                prompt_text = prompt_font.render(bottom_question_prompt, True, theme["accent"])
                prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT - 16))
                screen.blit(prompt_text, prompt_rect)
        else:
            global celebration_played
            if not celebration_played:
                play_sound(celebration_sound)
                celebration_played = True

            # Celebration backdrop on the post-round screen.
            if theme_mode == "light":
                pygame.draw.circle(screen, (240, 190, 60), (90, 80), 55)
                pygame.draw.circle(screen, (173, 216, 230), (720, 90), 50)
                pygame.draw.circle(screen, (144, 238, 144), (740, 430), 70)
            else:
                pygame.draw.circle(screen, (240, 190, 60), (90, 80), 55)
                pygame.draw.circle(screen, (120, 170, 220), (720, 90), 50)
                pygame.draw.circle(screen, (96, 180, 120), (740, 430), 70)

            # Keep a compact score badge above text so sections do not collide.
            round_badge = pygame.Rect((WIDTH - 170) // 2, 118, 170, 82)
            pygame.draw.rect(screen, LIGHT_GREEN, round_badge, border_radius=16)
            pygame.draw.rect(screen, (110, 180, 110), round_badge, 2, border_radius=16)
            round_badge_title = small_font.render("Round Score", True, BLACK)
            round_badge_value = option_font.render(f"{score}/{total_questions}", True, BLACK)
            round_badge_title_rect = round_badge_title.get_rect(center=(round_badge.centerx, round_badge.y + 24))
            round_badge_value_rect = round_badge_value.get_rect(center=(round_badge.centerx, round_badge.y + 56))
            screen.blit(round_badge_title, round_badge_title_rect)
            screen.blit(round_badge_value, round_badge_value_rect)

            percentage = round((score / total_questions) * 100) if total_questions else 0
            final = question_font.render(f"Final Score: {score}/{total_questions} = {percentage}%", True, theme["text"])
            final_rect = final.get_rect(center=(WIDTH // 2, 232))
            screen.blit(final, final_rect)

            if score == total_questions == 10:
                msg = "🎉 UNBELIEVABLE! 10/10! 🎉"
            elif score == total_questions:
                msg = "🏆 Perfect Score!"
            elif score >= max(1, total_questions - 1):
                msg = "⭐ Great Job!"
            else:
                msg = "👍 Keep Practicing!"

            result = question_font.render(msg, True, theme["text"])
            result_rect = result.get_rect(center=(WIDTH // 2, 276))
            screen.blit(result, result_rect)

            main_menu_button.draw(screen, False, theme)
            game_over_facts_btn.draw(screen, False, theme)
            prompt = small_font.render("", True, theme["text"])
            screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 290))

    elif game_state == "final_summary":
        global yay_played
        if not yay_played:
            play_sound(yay_sound)
            yay_played = True

        if theme_mode == "light":
            screen.fill((248, 244, 255))
            pygame.draw.circle(screen, (173, 216, 230), (90, 80), 70)
            pygame.draw.circle(screen, (240, 190, 60), (720, 90), 55)
            pygame.draw.circle(screen, (144, 238, 144), (740, 430), 75)
        else:
            screen.fill((12, 16, 40))
            pygame.draw.circle(screen, (80, 120, 180), (90, 80), 70)
            pygame.draw.circle(screen, (240, 190, 60), (720, 90), 55)
            pygame.draw.circle(screen, (96, 180, 120), (740, 430), 75)

        title = title_font.render("Quiz Complete!", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 36))

        summary_card = pygame.Rect(80, 95, 640, 300)
        pygame.draw.rect(screen, (255, 255, 255), summary_card, border_radius=18)
        pygame.draw.rect(screen, GOLD, summary_card, 3, border_radius=18)

        accent_bar = pygame.Rect(summary_card.x, summary_card.y, summary_card.width, 18)
        pygame.draw.rect(screen, LIGHT_BLUE, accent_bar, border_radius=18)

        total_right = session_base_score + bonus_points
        total_answered = session_base_answered + session_bonus_answered
        base_percentage = round((session_base_score / session_base_answered) * 100) if session_base_answered else 0
        bonus_percentage = round((bonus_points / session_bonus_answered) * 100) if session_bonus_answered else 0

        base_text = question_font.render(
            f"Base Score: {session_base_score}/{session_base_answered} = {base_percentage}%",
            True,
            BLACK,
        )
        bonus_text = question_font.render(
            f"Bonus Score: {bonus_points}/{session_bonus_answered} = {bonus_percentage}%",
            True,
            BLACK,
        )
        total_text = question_font.render(
            f"Total Points: {total_right}/{total_answered}",
            True,
            BLACK,
        )
        extra_text = small_font.render("Final score uses every question you answered.", True, BLACK)

        screen.blit(base_text, (summary_card.x + 34, summary_card.y + 48))
        screen.blit(bonus_text, (summary_card.x + 34, summary_card.y + 92))
        screen.blit(total_text, (summary_card.x + 34, summary_card.y + 136))
        screen.blit(extra_text, (summary_card.x + 34, summary_card.y + 178))

        score_badge = pygame.Rect((WIDTH - 190) // 2, 296, 190, 84)
        pygame.draw.rect(screen, LIGHT_GREEN, score_badge, border_radius=18)
        pygame.draw.rect(screen, (110, 180, 110), score_badge, 2, border_radius=18)
        badge_title = small_font.render("Questions Right", True, BLACK)
        badge_value = title_font.render(str(total_right), True, BLACK)
        badge_title_rect = badge_title.get_rect(center=(score_badge.centerx, score_badge.y + 22))
        badge_value_rect = badge_value.get_rect(center=(score_badge.centerx, score_badge.y + 56))
        screen.blit(badge_title, badge_title_rect)
        screen.blit(badge_value, badge_value_rect)

        # Load and display the win image inside the gold card on the right blank side
        win_image = load_image("win.png", max_size=(220, 170))
        if win_image:
            # Right blank area of the card: x=430 to x=710, y=113 to y=295
            win_rect = win_image.get_rect(center=(590, 210))
            screen.blit(win_image, win_rect)

        final_summary_menu_btn.draw(screen, False, theme)

        prompt = small_font.render("Return to the home screen to view your profile.", True, theme["text"])
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 406))

    elif game_state == "bonus_offer":
        if theme_mode == "light":
            screen.fill((248, 244, 255))
            pygame.draw.circle(screen, (240, 190, 60), (100, 90), 60)
            pygame.draw.circle(screen, (201, 185, 255), (710, 95), 55)
            pygame.draw.circle(screen, (173, 216, 230), (740, 420), 85)
        else:
            screen.fill((13, 20, 32))
            pygame.draw.circle(screen, (240, 190, 60), (100, 90), 60)
            pygame.draw.circle(screen, (201, 185, 255), (710, 95), 55)
            pygame.draw.circle(screen, (173, 216, 230), (740, 420), 85)

        title = title_font.render("Bonus Question Offer", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 34))

        offer_card = pygame.Rect(100, 110, 600, 250)
        pygame.draw.rect(screen, (255, 255, 255), offer_card, border_radius=20)
        pygame.draw.rect(screen, GOLD, offer_card, 3, border_radius=20)

        summary = question_font.render(f"You scored {score}/{total_questions} so far!", True, BLACK)
        prompt = question_font.render("Would you like a chance to earn one bonus point?", True, BLACK)
        screen.blit(summary, (offer_card.x + 38, offer_card.y + 45))
        screen.blit(prompt, (offer_card.x + 38, offer_card.y + 95))

        stats_box = pygame.Rect(offer_card.x + 38, offer_card.y + 145, 190, 70)
        pygame.draw.rect(screen, LIGHT_BLUE, stats_box, border_radius=14)
        pygame.draw.rect(screen, (100, 150, 210), stats_box, 2, border_radius=14)
        stats_title = small_font.render("Questions Done", True, BLACK)
        stats_value = option_font.render(str(total_questions), True, BLACK)
        screen.blit(stats_title, (stats_box.x + 18, stats_box.y + 8))
        screen.blit(stats_value, (stats_box.x + 18, stats_box.y + 30))

        bonus_question_button.draw(screen, False, theme)
        skip_bonus_button.draw(screen, False, theme)
        facts_view_button.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)

    elif game_state == "facts_view":
        facts_category = facts_view_category or selected_category or last_completed_category or "Technology"
        facts = category_facts.get(facts_category, [])
        if theme_mode == "light":
            screen.fill((250, 247, 240))
            pygame.draw.circle(screen, (240, 190, 60), (85, 80), 65)
            pygame.draw.circle(screen, (173, 216, 230), (715, 90), 55)
            pygame.draw.circle(screen, (144, 238, 144), (720, 430), 85)
        else:
            screen.fill((10, 14, 32))
            pygame.draw.circle(screen, (240, 190, 60), (85, 80), 65)
            pygame.draw.circle(screen, (173, 216, 230), (715, 90), 55)
            pygame.draw.circle(screen, (144, 238, 144), (720, 430), 85)

        title = title_font.render("Want to know more?", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 34))

        facts_card = pygame.Rect(70, 105, 660, 280)
        pygame.draw.rect(screen, (255, 255, 255), facts_card, border_radius=22)
        pygame.draw.rect(screen, (201, 185, 255), facts_card, 3, border_radius=22)

        header = question_font.render(f"3 facts about {facts_category}:", True, theme["text"])
        screen.blit(header, (facts_card.x + 28, facts_card.y + 30))

        facts_text_max_width = facts_card.width - 90
        fact_y = facts_card.y + 78
        for index, fact in enumerate(facts[:3]):
            bullet_color = [LIGHT_BLUE, LIGHT_GREEN, GOLD][index % 3]
            bullet = pygame.Rect(facts_card.x + 28, fact_y + 6, 18, 18)
            pygame.draw.rect(screen, bullet_color, bullet, border_radius=6)

            fact_lines = wrap_text(fact, small_font, facts_text_max_width)
            for line_index, line in enumerate(fact_lines):
                fact_text = small_font.render(line, True, BLACK)
                screen.blit(fact_text, (facts_card.x + 58, fact_y + line_index * 22))

            fact_y += max(56, len(fact_lines) * 22 + 12)

        facts_back_button.draw(screen, False, theme)
        prompt = small_font.render("", True, theme["accent"])
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, facts_back_button.rect.y - 28))

        theme_toggle_btn.draw(screen, False, theme)

    pygame.display.update()


running = True

while running:
    draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()
            

        if game_state == "login":
            username_box.handle_event(event)
            password_box.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if music_toggle_btn.is_clicked(pos):
                    music_muted = not music_muted
                    continue

                if login_btn.is_clicked(pos):
                    username = username_box.text.strip()
                    password = password_box.text.strip()
                    success, auth_message = auth.authenticate(username, password)
                    if success:
                        reset_quiz_progress()
                        # theme_mode = "light"
                        # theme_toggle_btn.text = "Dark Mode"
                        current_user = username
                        game_state = "home"
                        print(f"DEBUG: login successful for {username}; set game_state=home")
                        pygame.event.clear()
                        pygame.time.wait(80)
                        continue

                elif register_btn.is_clicked(pos):
                    username = username_box.text.strip()
                    password = password_box.text.strip()
                    success, auth_message = auth.register_user(username, password)
                    if success:
                        username_box.text = ""
                        password_box.text = ""
                        username_box.active = True
                        password_box.active = False
                        username_box.trigger_hint_blink()
                        password_box.trigger_hint_blink()
                        print(f"DEBUG: registration successful for {username}; stay on login screen")

                elif guest_btn.is_clicked(pos):
                    reset_quiz_progress()
                    # theme_mode = "light"
                    # theme_toggle_btn.text = "Dark Mode"
                    current_user = "Guest"
                    game_state = "home"
                    print("DEBUG: guest selected; set game_state=home")
                    pygame.event.clear()
                    pygame.time.wait(80)
                    continue

        elif game_state == "home":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue
                if music_toggle_btn.is_clicked(pos):
                    music_muted = not music_muted
                    continue
                if home_start_btn.is_clicked(pos):
                    go_to_category_select()
                elif home_tutorial_btn.is_clicked(pos):
                    game_state = "tutorial"
                elif home_logout_btn.is_clicked(pos):
                    # simple logout: go back to login screen
                    reset_quiz_progress()
                    current_user = "Guest"
                    username_box.text = ""
                    password_box.text = ""
                    auth_message = "Signed out."
                    game_state = "login"
                    homepage_intro_played = False

        elif game_state == "category_select":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if category_tech_btn.is_clicked(pos):
                    start_category("Technology")
                elif category_celebrity_btn.is_clicked(pos):
                    start_category("Celebrities & More")
                elif category_history_btn.is_clicked(pos):
                    start_category("Historical Events")
                elif category_back_btn.is_clicked(pos):
                    game_state = "home"
            
        elif game_state == "tutorial":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if tutorial_start_btn.is_clicked(pos):
                    go_to_category_select()
                elif tutorial_back_btn.is_clicked(pos):
                    game_state = "home"

        elif game_state == "game" and not game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                for btn in buttons:
                    if btn.is_clicked(pos):
                        selected_option = btn.text

                if next_button.is_clicked(pos) and selected_option:
                    check_answer()
                    draw()
                    pygame.time.delay(1200)
                    next_question()

        elif game_state == "bonus_offer":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if facts_view_button.is_clicked(pos):
                    open_facts_view(selected_category or last_completed_category or "Technology", "bonus_offer")
                    continue

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if bonus_question_button.is_clicked(pos):
                    start_bonus_question()
                elif skip_bonus_button.is_clicked(pos):
                    bonus_offer = False
                    bonus_used = True
                    game_over = True
                    game_state = "game"
                    auth.save_high_score(current_user, score)

        elif game_state == "facts_view":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if facts_back_button.is_clicked(pos):
                    game_state = facts_return_state

        elif game_state == "game" and game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if main_menu_button.is_clicked(pos):
                    if selected_category:
                        completed_categories.add(selected_category)
                    if len(completed_categories) == len(question_categories):
                        game_state = "final_summary"
                    else:
                        go_to_category_select()
                    game_over = False
                    current_questions = []
                    total_questions = 0
                    bonus_used = False
                    bonus_taken = False
                    bonus_offer = False
                    celebration_played = False
                    yay_played = False
                    feedback = ""
                    selected_category = None
                    facts_view_category = None
                elif game_over_facts_btn.is_clicked(pos):
                    open_facts_view(selected_category or last_completed_category, return_state="game")

        elif game_state == "final_summary":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if final_summary_menu_btn.is_clicked(pos):
                    reset_quiz_progress()
                    game_state = "login"
                    game_over = False
                    current_questions = []
                    total_questions = 0
                    bonus_used = False
                    bonus_taken = False
                    bonus_offer = False
                    celebration_played = False
                    yay_played = False
                    feedback = ""
                    selected_category = None
                    facts_view_category = None
                    completed_categories = set()
                    current_user = "Guest"
                    username_box.text = ""
                    password_box.text = ""
                    auth_message = "Sign in or play as a guest player!"

pygame.quit()
sys.exit()
