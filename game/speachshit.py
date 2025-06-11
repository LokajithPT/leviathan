import pygame
import time
import sys
import threading
import speech_recognition as sr

pygame.init()

# Config
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Speak The Sentence - Loki Style")

# Fonts & Colors
FONT = pygame.font.Font(None, 48)
BIG_FONT = pygame.font.Font(None, 72)
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
GREEN = (0, 255, 0)
RED = (255, 70, 70)
BG = (10, 10, 10)

# Speech Recognition setup
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Game state
spoken_words = []
final_wpm = 0
final_acc = 0
sentence_done = False
start_time = None

def listen_in_background(target_sentence):
    global spoken_words, sentence_done, start_time, final_wpm, final_acc

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while not sentence_done:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5)
                result = recognizer.recognize_google(audio).lower()
                print(f"🎙️ Heard: {result}")
                spoken_words += result.strip().split()

                # End check
                if len(spoken_words) >= len(target_sentence):
                    spoken_words = spoken_words[:len(target_sentence)]
                    total_time = time.time() - start_time
                    correct_chars = sum(len(w) for i, w in enumerate(spoken_words) if i < len(target_sentence) and w == target_sentence[i])
                    final_wpm = calc_wpm(correct_chars, total_time)
                    final_acc, _ = calc_accuracy(target_sentence, spoken_words)
                    sentence_done = True

        except sr.WaitTimeoutError:
            print("🎤 Timeout...")
        except sr.UnknownValueError:
            print("🤔 Didn't catch that...")
        except sr.RequestError:
            print("🚫 Could not request results. Check internet.")

def draw_sentence(target, spoken):
    x, y = 40, 160
    for i, word in enumerate(target):
        if i < len(spoken):
            color = GREEN if spoken[i] == word else RED
        else:
            color = GRAY
        rendered = FONT.render(word, True, color)
        screen.blit(rendered, (x, y))
        x += rendered.get_width() + 20
        if x > WIDTH - 200:
            x = 40
            y += 60

def calc_wpm(char_count, seconds):
    words = char_count / 5
    return round(words / (seconds / 60), 2)

def calc_accuracy(target, spoken):
    total = sum(len(w) for w in spoken)
    correct = 0
    for i in range(min(len(target), len(spoken))):
        for j in range(min(len(target[i]), len(spoken[i]))):
            if target[i][j] == spoken[i][j]:
                correct += 1
    return round((correct / total) * 100) if total else 0, correct

def get_sentence_input():
    input_str = ""
    while True:
        screen.fill(BG)
        prompt = FONT.render("Type the sentence user will say. Press ENTER", True, WHITE)
        user_input = BIG_FONT.render(input_str, True, GREEN)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 100))
        screen.blit(user_input, (WIDTH//2 - user_input.get_width()//2, 200))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_str.strip():
                    return input_str.strip().lower().split()
                elif event.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif event.unicode.isprintable():
                    input_str += event.unicode

        pygame.display.flip()
        pygame.time.Clock().tick(30)

def main():
    global start_time

    sentence = get_sentence_input()
    start_time = time.time()

    # Start background listening
    listen_thread = threading.Thread(target=listen_in_background, args=(sentence,))
    listen_thread.start()

    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill(BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_sentence(sentence, spoken_words)

        if not sentence_done:
            elapsed = time.time() - start_time
            joined = spoken_words
            acc, correct_chars = calc_accuracy(sentence, joined)
            wpm = calc_wpm(correct_chars, elapsed)
            stats = FONT.render(f"WPM: {wpm}  |  ACC: {acc}%", True, WHITE)
            screen.blit(stats, (50, 40))

        if sentence_done:
            blur = pygame.transform.smoothscale(screen, (WIDTH//10, HEIGHT//10))
            blur = pygame.transform.smoothscale(blur, (WIDTH, HEIGHT))
            screen.blit(blur, (0, 0))

            wpm_txt = BIG_FONT.render(f"WPM: {final_wpm}", True, GREEN)
            acc_txt = BIG_FONT.render(f"Accuracy: {final_acc}%", True, WHITE)
            esc_txt = FONT.render("Press ESC to quit", True, GRAY)
            screen.blit(wpm_txt, (WIDTH//2 - wpm_txt.get_width()//2, 80))
            screen.blit(acc_txt, (WIDTH//2 - acc_txt.get_width()//2, 160))
            screen.blit(esc_txt, (WIDTH//2 - esc_txt.get_width()//2, 250))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

