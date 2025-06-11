import pygame
import random
import time
import sys

pygame.init()

# Config
WIDTH, HEIGHT = 1000, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Monkeytype Clone - Loki Style")

# Fonts & Colors
FONT = pygame.font.Font(None, 48)
BIG_FONT = pygame.font.Font(None, 72)
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
GREEN = (0, 255, 0)
RED = (255, 70, 70)
BG = (10, 10, 10)

# Load words from file
try:
    with open("words.txt") as f:
        WORDS = f.read().splitlines()
except FileNotFoundError:
    print("words.txt not found!")
    sys.exit()

def get_words(n):
    return random.sample(WORDS, n)

def get_word_count_input():
    input_str = ""
    active = True
    while active:
        screen.fill(BG)
        prompt = FONT.render("How many words do you want to type? Press ENTER", True, WHITE)
        user_input = BIG_FONT.render(input_str, True, GREEN)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 100))
        screen.blit(user_input, (WIDTH//2 - user_input.get_width()//2, 200))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_str.isdigit():
                    return int(input_str)
                elif event.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif event.unicode.isdigit():
                    input_str += event.unicode

        pygame.display.flip()
        pygame.time.Clock().tick(30)

def draw_words(target, typed):
    x, y = 40, 160
    for i, word in enumerate(target):
        for j, char in enumerate(word):
            typed_char = typed[i][j] if i < len(typed) and j < len(typed[i]) else None
            if typed_char is None:
                color = GRAY
            elif typed_char == char:
                color = GREEN
            else:
                color = RED
            ch = FONT.render(char, True, color)
            screen.blit(ch, (x, y))
            x += ch.get_width()
        space = FONT.render(" ", True, WHITE)
        screen.blit(space, (x, y))
        x += space.get_width()
        if x > WIDTH - 100:
            x = 40
            y += 50

def calc_wpm(chars, secs):
    words = chars / 5
    return round(words / (secs / 60), 2)

def calc_accuracy(target, typed):
    total = sum(len(word) for word in typed)
    correct = 0
    for i in range(min(len(target), len(typed))):
        for j in range(min(len(target[i]), len(typed[i]))):
            if target[i][j] == typed[i][j]:
                correct += 1
    return round((correct / total) * 100) if total else 0, correct

def main():
    word_count = get_word_count_input()
    target_words = get_words(word_count)
    typed_words = [[]]
    current_word = 0
    started = False
    start_time = 0
    ended = False
    final_wpm, final_acc = 0, 0
    blur_background = None

    clock = pygame.time.Clock()
    running = True
    while running:
        if not ended:
            screen.fill(BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not ended and event.type == pygame.KEYDOWN:
                if not started:
                    start_time = time.time()
                    started = True

                if event.key == pygame.K_BACKSPACE:
                    if typed_words[current_word]:
                        typed_words[current_word].pop()
                    elif current_word > 0:
                        current_word -= 1
                        typed_words.pop()
                elif event.key == pygame.K_SPACE:
                    if len(typed_words) < len(target_words):
                        current_word += 1
                        typed_words.append([])
                elif event.unicode.isprintable():
                    typed_words[current_word].append(event.unicode)

                    # Check if it's the end of last word
                    if (current_word == len(target_words) - 1 and
                        ''.join(typed_words[current_word]) == target_words[current_word]):
                        ended = True
                        total_time = time.time() - start_time
                        final_acc, correct_chars = calc_accuracy(target_words, typed_words)
                        final_wpm = calc_wpm(correct_chars, total_time)

                        # 💥 Take screenshot for blur before clearing screen
                        blur_background = screen.copy()

        draw_words(target_words, typed_words)

        if started and not ended:
            elapsed = time.time() - start_time
            acc, correct_chars = calc_accuracy(target_words, typed_words)
            wpm = calc_wpm(correct_chars, elapsed)
            stats = FONT.render(f"WPM: {wpm}  |  ACC: {acc}%", True, WHITE)
            screen.blit(stats, (50, 40))

        if ended and blur_background:
            # 🔥 Apply blur from captured screen
            blur_surface = pygame.transform.smoothscale(blur_background, (WIDTH//10, HEIGHT//10))
            blur_surface = pygame.transform.smoothscale(blur_surface, (WIDTH, HEIGHT))
            screen.blit(blur_surface, (0, 0))

            # 💯 Show final stats
            wpm_txt = BIG_FONT.render(f"WPM: {final_wpm}", True, GREEN)
            acc_txt = BIG_FONT.render(f"Accuracy: {final_acc}%", True, WHITE)
            esc_txt = FONT.render("Press ESC to quit", True, GRAY)

            screen.blit(wpm_txt, (WIDTH//2 - wpm_txt.get_width()//2, 60))
            screen.blit(acc_txt, (WIDTH//2 - acc_txt.get_width()//2, 140))
            screen.blit(esc_txt, (WIDTH//2 - esc_txt.get_width()//2, 220))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

