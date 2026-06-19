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

WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2000's Trivia Challenge")
DATA_FILE = os.path.join(os.path.dirname(__file__), "user_data.json")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 180, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (220, 220, 220)
PURPLE = (201, 185, 255)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144, 238, 144)
NAVY = (15, 22, 52)
GOLD = (240, 190, 60)
LIGHT = (235, 236, 242)

title_font = pygame.font.SysFont("comic sans ms", 36, bold=True)
question_font = pygame.font.SysFont("comic sans ms", 20)
option_font = pygame.font.SysFont("comic sans ms", 24)
feedback_font = pygame.font.SysFont("comic sans ms", 30, bold=True)
small_font = pygame.font.SysFont("comic sans ms", 16)
prompt_font = pygame.font.SysFont("comic sans ms", 22, bold=True)


THEMES = {
    "dark": {
        "background": BLACK,
        "surface": (30, 30, 30),
        "text": WHITE,
        "title": WHITE,
        "button": (60, 60, 60),
        "button_selected": (200, 200, 200),
        "button_text": WHITE,
        "input_bg": (40, 40, 40),
        "input_border": (180, 180, 180),
        "input_text": WHITE,
        "feedback_shadow": (0, 0, 0),
        "feedback_correct": GREEN,
        "feedback_wrong": RED,
        "accent": (200, 200, 200),
    },
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
        "feedback_shadow": (200, 200, 200),
        "feedback_correct": GREEN,
        "feedback_wrong": RED,
        "accent": (60, 60, 60),
    }
}

theme_mode = "light"


def load_image(filename, max_size=(520, 240)):
    if not filename:
        return None
    path = os.path.join(IMAGE_DIR, filename)
    if not os.path.isfile(path):
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
        iw, ih = image.get_size()
        mw, mh = max_size
        scale = min(mw / iw, mh / ih, 1)
        image = pygame.transform.smoothscale(image, (int(iw * scale), int(ih * scale)))
        return image
    except pygame.error:
        return None


def create_tone_sound(frequency, duration=0.35, amplitude=14000):
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
    """Create an exciting startup sound for the login screen."""
    sample_rate = 44100
    duration = 1.2
    # Ascending arpeggio with harmonics
    notes = [262, 330, 392, 523, 659]  # C, E, G, C, E ascending
    note_duration = duration / len(notes)
    samples = array.array('h')

    for freq in notes:
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

            # Add harmonic richness
            value = int(15000 * envelope * (
                0.6 * math.sin(2 * math.pi * freq * phase) +
                0.3 * math.sin(2 * math.pi * freq * 2 * phase) +
                0.1 * math.sin(2 * math.pi * freq * 3 * phase)
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

        # Melody line - moving through intervals
        melody_freqs = [440, 494, 523, 587, 659, 587, 523, 494]  # A, B, C, D, E, D, C, B
        melody_pos = int((time % duration) * len(melody_freqs) / duration)
        melody_freq = melody_freqs[melody_pos % len(melody_freqs)]
        melody_volume = 7000

        # Add some swing/rhythm to melody with envelope
        beat_phase = (time * 2) % 1.0  # 2 beats per second
        if beat_phase < 0.3:
            melody_envelope = beat_phase / 0.3
        elif beat_phase < 0.6:
            melody_envelope = 1.0
        else:
            melody_envelope = max(0, (1.0 - beat_phase) / 0.4)

        # Harmony - minor third above bass
        harmony_freq = 440 * 1.2  # Creates nice harmony
        harmony_volume = 5000

        # Mix all elements
        bass_wave = math.sin(2 * math.pi * bass_freq * phase) * bass_volume
        melody_wave = math.sin(2 * math.pi * melody_freq * phase) * melody_volume * melody_envelope
        harmony_wave = math.sin(2 * math.pi * harmony_freq * phase) * harmony_volume * 0.5

        # Combine with slight compression
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
    sample_rate = 44100
    duration = 0.8
    frequencies = [660, 880, 1040]
    samples = array.array('h')
    total_samples = int(sample_rate * duration)

    for i in range(total_samples):
        phase = i / sample_rate
        freq = frequencies[min(i // (total_samples // len(frequencies)), len(frequencies) - 1)]
        amplitude = int(18000 * math.sin(2 * math.pi * freq * phase))
        samples.append(amplitude)

    try:
        return pygame.mixer.Sound(buffer=samples)
    except Exception:
        return None


def play_sound(sound):
    if sound:
        try:
            sound.play()
        except Exception:
            pass


celebration_sound = create_celebration_sound()
correct_sound = create_correct_sound()
wrong_sound = create_wrong_sound()
login_intro_sound = create_login_intro()
background_music = create_background_music()
celebration_played = False
login_intro_played = False
background_music_playing = False


class AuthManager:
    """Handles everything to do with checking, creating, and storing accounts."""
    def __init__(self, data_filepath):
        self.filepath = data_filepath
        self.user_data = self._load_all_data()

    def _load_all_data(self):
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError):
            return {}

    def _save_all_data(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(self.user_data, file, indent=2)
        except OSError:
            pass

    def register_user(self, username, password):
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
        if not username or not password:
            return False, "Please fill in both fields."
        if username in self.user_data and self.user_data[username]["password"] == password:
            return True, "Loaded your profile."
        return False, "Invalid username or password."

    def save_high_score(self, username, final_score):
        if username == "Guest":
            return
        if username in self.user_data:
            if final_score > self.user_data[username].get("high_score", 0):
                self.user_data[username]["high_score"] = final_score
                self._save_all_data()


class InputBox:
    def __init__(self, rect, placeholder=""):
        self.rect = pygame.Rect(rect)
        self.color = WHITE
        self.text = ""
        self.active = False
        self.placeholder = placeholder
        self.hint_blink_until = 0

    def trigger_hint_blink(self, duration_ms=2800):
        self.hint_blink_until = pygame.time.get_ticks() + duration_ms

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = GOLD if self.active else WHITE
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                pass
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
            txt = option_font.render(self.text, True, text_color)
            surface.blit(txt, (self.rect.x + 10, self.rect.y + 8))
        else:
            txt = option_font.render(self.placeholder, True, placeholder_color)
            surface.blit(txt, (self.rect.x + 10, self.rect.y + 8))

        # Draw a blinking cursor in the active input box.
        if self.active and ((now // 500) % 2) == 0:
            rendered = option_font.render(self.text, True, text_color)
            caret_x = min(self.rect.right - 12, self.rect.x + 10 + rendered.get_width() + 2)
            caret_top = self.rect.y + 9
            caret_bottom = self.rect.y + self.rect.height - 9
            pygame.draw.line(surface, text_color, (caret_x, caret_top), (caret_x, caret_bottom), 2)


# Initialize Auth Layer
auth = AuthManager(DATA_FILE)
current_user = "Guest"

# State Control: "login" or "game"
game_state = "login"
auth_message = "Sign in or play as a guest player!"

# Input fields and system buttons
username_box = InputBox((220, 180, 360, 45), "Username")
password_box = InputBox((220, 240, 360, 45), "Password")


question_categories = {
    "Technology": [
        {
            "question": "Which social media platform was founded by Mark Zuckerberg in 2004?",
            "options": ["Twitter", "Facebook", "MySpace", "Friendster"],
            "answer": "Facebook",
            "image": "facebook_logo.png"
        },
        {
            "question": "What popular video-sharing website was founded in 2005?",
            "options": ["Vimeo", "YouTube", "Dailymotion", "Metacafe"],
            "answer": "YouTube"
        },
        {
            "question": "Which music player device was released by Apple in 2001?",
            "options": ["iPad", "iPod", "Apple Watch", "AirPods"],
            "answer": "iPod"
        },
        {
            "question": "What streaming technology did Netflix introduce in 2007?",
            "options": ["Internet streaming", "Downloading", "Satellite", "Bluetooth"],
            "answer": "Internet streaming"
        },
        {
            "question": "What year was the first iPhone released?",
            "options": ["2001", "2002", "2004", "2007"],
            "answer": "2007"
        },
        {
            "question": "Which gaming console was released by Microsoft in 2005?",
            "options": ["Xbox", "Xbox 360", "Wii", "PlayStation 2"],
            "answer": "Xbox 360"
        }
    ],
    "Celebrities & More": [
        {
            "question": "Michael Jackson is known as the King of what?",
            "options": ["Jazz", "Rock", "Pop", "Blues"],
            "answer": "Pop",
            "image": "pop_king.png"
        },
        {
            "question": "Who did Michael Jackson start a band with?",
            "options": ["Brothers", "Parents", "Neighbors", "Cousins"],
            "answer": "Brothers"
        },
        {
            "question": "What was the name of the lost clownfish that a father searches for across the ocean?",
            "options": ["Nemo", "Dory", "Shrek", "The Lord of the Rings"],
            "answer": "Nemo"
        },
        {
            "question": "Which girl group was a huge phenomenon in the early 2000s?",
            "options": ["The Pussycat Dolls", "Destiny's Child", "Spice Girls", "TLC"],
            "answer": "Destiny's Child"
        },
        {
            "question": "Which reality singing competition featured Jennifer Lopez, Simon Cowell, and Steve Tyler?",
            "options": ["The Voice", "American Idol", "The X Factor", "Dancing with Stars"],
            "answer": "American Idol"
        },
        {
            "question": "What movie was released in 2000?",
            "options": ["Gladiator", "The Matrix", "X-Men", "The Lord of the Rings"],
            "answer": "The Matrix"
        }
    ],
    "Historical Events": [
        {
            "question": "What were the Twin Towers rebuilt as?",
            "options": ["One World Trade Center", "Empire State Building", "Burj Khalifa", "Shanghai Tower"],
            "answer": "One World Trade Center",
            "image": "one_world_trade.png"
        },
        {
            "question": "When did Hurricane Katrina hit New Orleans?",
            "options": ["Aug 22nd", "Aug 3rd", "Aug 23rd", "Aug 29th"],
            "answer": "Aug 29th"
        },
        {
            "question": "What was the financial crisis of 2008 primarily caused by?",
            "options": ["Dot-com bubble", "Housing market collapse", "Oil prices", "Tech stocks"],
            "answer": "Housing market collapse"
        },
        {
            "question": "In what year did Barack Obama become the 44th President of the United States?",
            "options": ["2006", "2007", "2008", "2009"],
            "answer": "2008"
        },
        {
            "question": "Which movie featuring avatar-like aliens was released in 2009?",
            "options": ["Transformers", "Avatar", "Inception", "District 9"],
            "answer": "Avatar"
        },
        {
            "question": "Which pirate-themed movie franchise launched in 2003?",
            "options": ["Pirates of the Caribbean", "Treasure Island", "The Black Pirate", "Captain Hook"],
            "answer": "Pirates of the Caribbean"
        }
    ]
}

current_questions = []
question_index = 0
score = 0
total_questions = 0
session_base_score = 0
current_category_base_score = 0
bonus_points = 0
current_is_bonus = False
bonus_used = False
bonus_taken = False
bonus_offer = False
selected_category = None
completed_categories = set()
selected_option = None
current_question_image = None
game_over = False

# Prevent immediate mouse-click propagation when switching screens
ignore_mouse = False

feedback = ""
feedback_color = BLACK
bottom_question_prompt = "Please choose one of the answers above"


class Button:
    def __init__(self, x, y, w, h, text, custom_color=None, enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.custom_color = custom_color
        self.enabled = enabled

    def draw(self, surface, selected=False, theme=None):
        if theme is None:
            theme = THEMES[theme_mode]

        # Use custom_color if set (for colored buttons on login/category screens)
        if self.custom_color is not None:
            # Colored button mode
            if not self.enabled:
                color = (100, 100, 100)
                text_color = (150, 150, 150)
            else:
                color = self.custom_color if not selected else (min(255, self.custom_color[0] + 40), min(255, self.custom_color[1] + 40), min(255, self.custom_color[2] + 40))
                text_color = WHITE
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, (50, 50, 50), self.rect, 2, border_radius=8)
        else:
            # Black and white theme button
            if not self.enabled:
                color = (100, 100, 100)
                text_color = (150, 150, 150)
            else:
                color = theme["button_selected"] if selected else theme["button"]
                text_color = theme["button_text"]
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, theme["text"], self.rect, 2, border_radius=8)

        txt = option_font.render(self.text, True, text_color)
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


def create_buttons():
    buttons = []
    for i in range(4):
        buttons.append(Button(200, 150 + i * 60, 400, 45, ""))
    return buttons

buttons = create_buttons()
next_button = Button(620, 420, 150, 50, "NEXT")
theme_toggle_btn = Button(WIDTH - 180, 20, 160, 40, "Dark Mode")
main_menu_button = Button(220, 320, 170, 45, "Back to Login", BLUE)
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

category_tech_btn = Button(180, 180, 260, 60, "Technology", BLUE)
category_celebrity_btn = Button(180, 260, 260, 60, "Celebrities & More", GREEN)
category_history_btn = Button(180, 340, 260, 60, "Historical Events", GOLD)
category_back_btn = Button(460, 420, 260, 60, "Back", RED)

bonus_question_button = Button(180, 320, 260, 55, "Bonus Question", BLUE)
skip_bonus_button = Button(460, 320, 260, 55, "Skip Bonus", GRAY)

# Tutorial screen buttons (different positions)
tutorial_start_btn = Button(220, 360, 170, 45, "Start Quiz", BLUE)
tutorial_back_btn = Button(410, 360, 170, 45, "Back", GREEN)


TOTAL_BASE_QUESTIONS = len(question_categories) * 5

def reset_quiz_progress():
    global completed_categories, session_base_score, current_category_base_score, bonus_points
    completed_categories = set()
    session_base_score = 0
    current_category_base_score = 0
    bonus_points = 0

def build_quiz_questions(source_questions, question_count=None):
    if question_count is None:
        question_count = len(source_questions)
    return [
        {
            "question": q["question"],
            "options": random.sample(q["options"], len(q["options"])),
            "answer": q["answer"]
        }
        for q in random.sample(source_questions, question_count)
    ]


def start_game(question_list, starting_score=0, starting_total=None, reset_bonus=True, question_count=None, is_bonus=False):
    global current_questions, question_index, score, total_questions, bonus_used, selected_option, game_over, feedback, feedback_color, bonus_taken, bonus_offer, current_is_bonus, current_category_base_score
    print("DEBUG: start_game() called")
    if reset_bonus:
        bonus_used = False
        bonus_taken = False
        bonus_offer = False
    current_is_bonus = is_bonus
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
    global selected_category, game_state
    selected_category = category_name
    start_game(question_categories[category_name], question_count=5, is_bonus=False)
    game_state = "game"


def start_bonus_question():
    global current_questions, question_index, total_questions, bonus_used, bonus_taken, selected_option, feedback, feedback_color, game_state, game_over, bonus_offer
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
        "answer": bonus_q["answer"]
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
    global game_state, background_music_playing
    game_state = "category_select"
    if background_music_playing:
        background_music.stop()
        background_music_playing = False


def load_question():
    global selected_option, current_question_image
    selected_option = None
    q = current_questions[question_index]
    current_question_image = load_image(q.get("image"))
    for i in range(4):
        buttons[i].text = q["options"][i]


def wrap_text(text, font, max_width):
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


def check_answer():
    global feedback, feedback_color, score, session_base_score, current_category_base_score, bonus_points
    correct = current_questions[question_index]["answer"]

    if selected_option == correct:
        score += 1
        if current_is_bonus:
            bonus_points += 1
        else:
            current_category_base_score += 1
        feedback = "✅ CORRECT!"
        feedback_color = GREEN
        play_sound(correct_sound)
    else:
        feedback = "❌ WRONG!"
        feedback_color = RED
        play_sound(wrong_sound)


def next_question():
    global question_index, game_over, feedback, bonus_offer, bonus_taken, game_state, session_base_score
    question_index += 1
    feedback = ""

    if question_index >= len(current_questions):
        if not bonus_taken and not bonus_offer:
            session_base_score += current_category_base_score
            completed_categories.add(selected_category)
            bonus_offer = True
            game_state = "bonus_offer"
            return
        if not current_is_bonus:
            session_base_score += current_category_base_score
            completed_categories.add(selected_category)
        game_over = True
        auth.save_high_score(current_user, score)
    else:
        load_question()


def draw():
    global login_intro_played, background_music_playing
    theme = THEMES[theme_mode]

    if game_state == "login":
        if not login_intro_played:
            play_sound(login_intro_sound)
            login_intro_played = True

        if not background_music_playing:
            background_music.play(-1)  # Loop infinitely
            background_music_playing = True

        screen.fill(theme["background"])
        title = title_font.render("2000's Trivia Challenge", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        username_box.draw(screen, theme)
        password_box.draw(screen, theme)

        login_btn.draw(screen, False, theme)
        register_btn.draw(screen, False, theme)
        guest_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)

        if auth_message:
            msg_surface = small_font.render(auth_message, True, theme["text"])
            screen.blit(msg_surface, (WIDTH // 2 - msg_surface.get_width() // 2, 440))

    elif game_state == "home":
        # Keep background music playing
        if not background_music_playing:
            background_music.play(-1)  # Loop infinitely
            background_music_playing = True

        screen.fill(theme["background"])
        title = title_font.render("2000's Trivia Challenge", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        welcome_text = question_font.render(f"Welcome, {current_user}!", True, theme["text"])
        screen.blit(welcome_text, (WIDTH // 2 - welcome_text.get_width() // 2, 120))

        if current_user != "Guest" and current_user in auth.user_data:
            high_score = auth.user_data[current_user].get("high_score", 0)
            high_score_text = question_font.render(f"High Score: {high_score} points", True, theme["accent"])
            screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, 160))

        home_start_btn.draw(screen, False, theme)
        home_tutorial_btn.draw(screen, False, theme)
        home_logout_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)

    elif game_state == "category_select":
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

        category_tech_btn.enabled = "Technology" not in completed_categories
        category_celebrity_btn.enabled = "Celebrities & More" not in completed_categories
        category_history_btn.enabled = "Historical Events" not in completed_categories

        category_tech_btn.draw(screen, False, theme)
        category_celebrity_btn.draw(screen, False, theme)
        category_history_btn.draw(screen, False, theme)
        category_back_btn.draw(screen, False, theme)
        theme_toggle_btn.draw(screen, False, theme)

    elif game_state == "tutorial":
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
            "Good luck!"
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
                img_rect = current_question_image.get_rect(center=(WIDTH // 2, question_bottom + current_question_image.get_height() // 2 + 20))
                screen.blit(current_question_image, img_rect)
                image_height = current_question_image.get_height() + 20

            answer_start_y = question_bottom + image_height + 20
            choice_theme = dict(theme)
            choice_theme["button"] = LIGHT_GREEN
            choice_theme["button_selected"] = (110, 200, 110)
            choice_theme["button_text"] = BLACK
            for i, btn in enumerate(buttons):
                btn.rect.y = answer_start_y + i * 60
                btn.draw(screen, btn.text == selected_option, choice_theme)

            next_button.draw(screen, False, theme)

            score_text = option_font.render(f"Score: {score}/{total_questions}", True, theme["text"])
            screen.blit(score_text, (650, 20))

            user_text = small_font.render(f"Player: {current_user}", True, theme["text"])
            screen.blit(user_text, (20, 20))

            if feedback:
                shadow = feedback_font.render(feedback, True, theme["feedback_shadow"])
                text = feedback_font.render(feedback, True, feedback_color)
                rect = text.get_rect(center=(WIDTH // 2, 440))
                screen.blit(shadow, (rect.x + 3, rect.y + 3))
                screen.blit(text, rect)

            prompt_text = prompt_font.render(bottom_question_prompt, True, theme["accent"])
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT - 16))
            screen.blit(prompt_text, prompt_rect)
        else:
            global celebration_played
            if not celebration_played:
                play_sound(celebration_sound)
                celebration_played = True

            percentage = round((score / total_questions) * 100) if total_questions else 0
            final = question_font.render(f"Final Score: {score}/{total_questions} = {percentage}%", True, theme["text"])
            screen.blit(final, (250, 180))

            if score == total_questions == 10:
                msg = "🎉 UNBELIEVABLE! 10/10! 🎉"
            elif score == total_questions:
                msg = "🏆 Perfect Score!"
            elif score >= max(1, total_questions - 1):
                msg = "⭐ Great Job!"
            else:
                msg = "👍 Keep Practicing!"

            result = question_font.render(msg, True, theme["text"])
            screen.blit(result, (180, 240))

            main_menu_button.draw(screen, False, theme)

            prompt = small_font.render("Choose your next move:", True, theme["text"])
            screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 290))

    elif game_state == "final_summary":
        screen.fill(theme["surface"])
        title = title_font.render("Quiz Complete!", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        base_percentage = round((session_base_score / TOTAL_BASE_QUESTIONS) * 100) if TOTAL_BASE_QUESTIONS else 0
        base_text = question_font.render(f"Base Score: {session_base_score}/{TOTAL_BASE_QUESTIONS} = {base_percentage}%", True, theme["text"])
        bonus_text = question_font.render(f"Bonus Points: {bonus_points}", True, theme["text"])
        total_text = question_font.render(f"Total Points: {session_base_score + bonus_points}", True, theme["text"])
        extra_text = small_font.render("Bonus can push your score above 100%!", True, theme["accent"])

        screen.blit(base_text, (WIDTH // 2 - base_text.get_width() // 2, 160))
        screen.blit(bonus_text, (WIDTH // 2 - bonus_text.get_width() // 2, 210))
        screen.blit(total_text, (WIDTH // 2 - total_text.get_width() // 2, 260))
        screen.blit(extra_text, (WIDTH // 2 - extra_text.get_width() // 2, 310))

        main_menu_button.draw(screen, False, theme)

        prompt = small_font.render("Return to the home screen to view your profile.", True, theme["text"])
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 360))

    elif game_state == "bonus_offer":
        screen.fill(theme["surface"])
        title = title_font.render("Bonus Question Offer", True, theme["title"])
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        summary = question_font.render(f"You scored {score}/{total_questions} so far!", True, theme["text"])
        screen.blit(summary, (WIDTH // 2 - summary.get_width() // 2, 140))

        prompt = question_font.render("Would you like a chance to earn one bonus point?", True, theme["text"])
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 200))

        bonus_question_button.draw(screen, False, theme)
        skip_bonus_button.draw(screen, False, theme)

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

                if login_btn.is_clicked(pos):
                    username = username_box.text.strip()
                    password = password_box.text.strip()
                    success, auth_message = auth.authenticate(username, password)
                    if success:
                        theme_mode = "light"
                        theme_toggle_btn.text = "Dark Mode"
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
                    theme_mode = "light"
                    theme_toggle_btn.text = "Dark Mode"
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
                if home_start_btn.is_clicked(pos):
                    go_to_category_select()
                elif home_tutorial_btn.is_clicked(pos):
                    game_state = "tutorial"
                elif home_logout_btn.is_clicked(pos):
                    # simple logout: go back to login screen
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
                    feedback = ""
                    selected_category = None

        elif game_state == "final_summary":
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if theme_toggle_btn.is_clicked(pos):
                    theme_mode = "light" if theme_mode == "dark" else "dark"
                    theme_toggle_btn.text = "Dark Mode" if theme_mode == "light" else "Light Mode"
                    continue

                if main_menu_button.is_clicked(pos):
                    game_state = "home"
                    game_over = False
                    current_questions = []
                    total_questions = 0
                    bonus_used = False
                    bonus_taken = False
                    bonus_offer = False
                    celebration_played = False
                    feedback = ""
                    selected_category = None

pygame.quit()
sys.exit()
