import pygame
import sys
import time
import asyncio

# --- Initialization ---
pygame.init()
pygame.mixer.init()

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
TIMER_DURATION = 30 * 60

WHITE, BLACK, RED = (255, 255, 255), (0, 0, 0), (255, 0, 0)
LIGHT_GREEN, GOLD = (200, 255, 200), (255, 215, 0)
BLUE, COMPLETED_GREEN, UNCOMPLETED_GREY = (50, 50, 200), (0, 200, 0), (150, 150, 150)
HINT_BOX_COLOR = (255, 255, 220)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ChemEscape - Lab Escape Game")
clock = pygame.time.Clock()

# --- Fonts ---
font = pygame.font.SysFont('arial', 20)
small_font = pygame.font.SysFont('arial', 14)
large_font = pygame.font.SysFont('arial', 40, bold=True)
title_font = pygame.font.SysFont('arial', 60, bold=True)
try:
    comic_sans_font = pygame.font.SysFont('Comic Sans MS', 24, bold=True)
except:
    comic_sans_font = pygame.font.SysFont('arial', 24, bold=True)

# --- Asset Loading ---
lab_bg = pygame.image.load("assets/lab.png")
character_img = pygame.image.load("assets/character.png")
pygame.mixer.music.load("assets/music.ogg")
pygame.mixer.music.play(-1)

# --- Game Variables ---
char_x, char_y = 50, 500
char_speed = 4
game_state = "START_SCREEN"
solved_puzzles = [False] * 10
incorrect_attempts_count = [0] * 10
user_input = ''
escape_code_input = ''
current_puzzle = None
input_active = False
escape_code_active = False
start_time = 0
total_incorrect_attempts = 0

puzzles = [
    {"id": 1, "question": "Rearrange the symbols for Boron, Nitrogen, Carbon, Argon and Oxygen to form the name of which element?\nHint: It is pretty common.", "answer": "Carbon", "hint": "It is the basis of organic life."},
    {"id": 2, "question": "If a substance sublimated, then precipitated, then melted, then froze; which state of matter was it in the most times?", "answer": "Solid", "hint": "Starts and ends here."},
    {"id": 3, "question": "If we reacted Sodium Hydoxide (NaOH) with Hydrochloric Acid (HCl), we would get water and what other common substance?", "answer": "Salt", "hint": "NaCl is the chemical name."},
    {"id": 4, "question": "As you heat a substance, its particles gain what type of energy?", "answer": "Kinetic", "hint": "Energy of motion."},
    {"id": 5, "question": "Spell the word formed from these chemical element symbols: Carbon, Americium, Phosphorus.", "answer": "Camp", "hint": "C + Am + P"},
    {"id": 6, "question": "What turns red in an acid, blue in a base and green in water?", "answer": "Universal Indicator", "hint": "pH indicator."},
    {"id": 7, "question": "If a substance behaves as both a solid and a liquid depending on what is done to it, what type of substance is it?", "answer": "Non-Newtonian", "hint": "Think of Oobleck."},
    {"id": 8, "question": "An empty can collapses in ice water because the ________ outside the can is greater than it is inside.", "answer": "Pressure", "hint": "Air force pushing in."},
    {"id": 9, "question": "Combustion is the chemical reaction occurs when a substance reacts with which element?", "answer": "Oxygen", "hint": "Fire needs this."},
    {"id": 10, "question": "What four letter word is shared by both softball and soap?", "answer": "Base", "hint": "Opposite of an acid."},
]
puzzle_positions = [(150, 150), (300, 120), (450, 140), (600, 150), (160, 300), (300, 350), (450, 330), (600, 300), (250, 500), (500, 500)]

# --- Helper Functions ---
def wrap_text(text, font_obj, max_width):
    words = text.split(' ')
    lines, current_line = [], []
    for word in words:
        test_line = " ".join(current_line + [word])
        if font_obj.render(test_line, True, BLACK).get_width() < max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    lines.append(" ".join(current_line))
    return lines

def draw_timer():
    elapsed = time.time() - start_time
    remaining = max(0, TIMER_DURATION - int(elapsed))
    timer_text = font.render(f"Time Left: {remaining//60:02}:{remaining%60:02}", True, BLACK)
    screen.blit(timer_text, (10, 10))

def draw_puzzle_tracker():
    bx, by, bw, bh = WIDTH - 160, 10, 150, 200
    pygame.draw.rect(screen, WHITE, (bx, by, bw, bh), 0, 5)
    pygame.draw.rect(screen, BLACK, (bx, by, bw, bh), 2, 5)
    screen.blit(small_font.render("Puzzles Solved:", True, BLACK), (bx + 10, by + 5))
    for i in range(10):
        color = COMPLETED_GREEN if solved_puzzles[i] else UNCOMPLETED_GREY
        ix = bx + 10 + (i % 3) * 45
        iy = by + 40 + (i // 3) * 45
        pygame.draw.rect(screen, color, (ix, iy, 20, 20))
        screen.blit(small_font.render(str(i+1), True, BLACK), (ix + 5, iy - 15))

# --- Main Game Loop ---
async def main():
    global game_state, char_x, char_y, user_input, escape_code_input, current_puzzle, input_active, escape_code_active, start_time, total_incorrect_attempts

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if game_state == "START_SCREEN":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pygame.Rect(WIDTH//2-75, HEIGHT-100, 150, 50).collidepoint(event.pos):
                        game_state = "PLAYING"
                        start_time = time.time()

            elif game_state == "PLAYING":
                if input_active and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        idx = current_puzzle["id"] - 1
                        if user_input.strip().lower() == current_puzzle["answer"].lower():
                            solved_puzzles[idx] = True
                            input_active = False
                            user_input = ""
                        else:
                            user_input = ""
                            incorrect_attempts_count[idx] += 1
                            total_incorrect_attempts += 1
                    elif event.key == pygame.K_BACKSPACE: user_input = user_input[:-1]
                    else: user_input += event.unicode
                
                elif escape_code_active and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if escape_code_input.strip() == "190":
                            game_state = "END_SCREEN"
                        else:
                            escape_code_input = ""
                            total_incorrect_attempts += 1
                    elif event.key == pygame.K_BACKSPACE: escape_code_input = escape_code_input[:-1]
                    else: escape_code_input += event.unicode

        if game_state == "START_SCREEN":
            screen.fill(BLACK)
            title = title_font.render("ChemEscape", True, WHITE)
            screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//6)))
            
            instr = [
                "You are locked in the science lab!",
                "Solve all 10 puzzles to unlock the escape door.",
                "Use the ARROW KEYS to move and stand on puzzles.",
                "When you have solved all ten puzzles, go to the door and enter the final code.",
                "You have 30 minutes to escape. Good luck!"
            ]
            for i, line in enumerate(instr):
                txt = font.render(line, True, WHITE)
                screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//3 + i*40)))
            
            pygame.draw.rect(screen, BLUE, (WIDTH//2-75, HEIGHT-100, 150, 50), border_radius=10)
            screen.blit(font.render("START", True, WHITE), (WIDTH//2-30, HEIGHT-88))

        elif game_state == "PLAYING":
            screen.blit(lab_bg, (0, 0))
            screen.blit(character_img, (char_x, char_y))
            
            # Movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: char_x -= char_speed
            if keys[pygame.K_RIGHT]: char_x += char_speed
            if keys[pygame.K_UP]: char_y -= char_speed
            if keys[pygame.K_DOWN]: char_y += char_speed
            char_x, char_y = max(0, min(WIDTH-40, char_x)), max(0, min(HEIGHT-40, char_y))

            # Collision Logic
            char_rect = character_img.get_rect(topleft=(char_x, char_y))
            any_puz = False
            for i, (px, py) in enumerate(puzzle_positions):
                if not solved_puzzles[i] and char_rect.colliderect(pygame.Rect(px-25, py-25, 50, 50)):
                    any_puz = True
                    if current_puzzle is None or current_puzzle["id"]-1 != i:
                        user_input = ""
                        current_puzzle, input_active = puzzles[i], True
                    break
            if not any_puz: input_active, current_puzzle = False, None

            # Door collision detection
            if all(solved_puzzles) and char_rect.colliderect(pygame.Rect(650, 500, 100, 100)):
                escape_code_active = True
            else: escape_code_active = False

            draw_timer()
            draw_puzzle_tracker()

            if input_active:
                pygame.draw.rect(screen, LIGHT_GREEN, (100, 100, 600, 300), border_radius=10)
                lines = wrap_text(current_puzzle["question"], comic_sans_font, 560)
                for idx, l in enumerate(lines): screen.blit(comic_sans_font.render(l, True, BLACK), (120, 120 + idx*35))
                pygame.draw.rect(screen, WHITE, (120, 340, 560, 40))
                screen.blit(font.render(user_input, True, BLACK), (125, 345))
                if incorrect_attempts_count[current_puzzle["id"]-1] >= 2:
                    pygame.draw.rect(screen, HINT_BOX_COLOR, (120, 300, 560, 35))
                    screen.blit(font.render(f"Hint: {current_puzzle['hint']}", True, RED), (125, 305))

            if escape_code_active:
                # Box drawing - kept height manageable to prevent logic break
                pygame.draw.rect(screen, GOLD, (100, 100, 600, 400), border_radius=10)
                final_msg = "Final Code: Take the first letter of each of your answers. Add the atomic numbers of the corresponding element in the periodic table. Enter the sum of these numbers to exit."
                
                # Wrap text and display
                wrapped_lines = wrap_text(final_msg, comic_sans_font, 560)
                for idx, line in enumerate(wrapped_lines):
                    screen.blit(comic_sans_font.render(line, True, BLACK), (120, 120 + idx * 35))
                
                # Input box positioned safely at the bottom
                pygame.draw.rect(screen, WHITE, (120, 440, 560, 40))
                screen.blit(font.render(escape_code_input, True, BLACK), (125, 445))

        elif game_state == "END_SCREEN":
            screen.fill(BLACK)
            screen.blit(large_font.render("LAB ESCAPED!", True, GOLD), (250, 250))

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

asyncio.run(main())
