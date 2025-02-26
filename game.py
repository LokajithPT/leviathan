import pygame

# Initialize pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy RAT")

# Bird settings
bird = pygame.Rect(100, 250, 30, 30)
velocity = 0
gravity = 0.5

# Game loop
running = True
while running:
    pygame.time.delay(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            velocity = -8

    velocity += gravity
    bird.y += velocity

    win.fill((0, 0, 0))
    pygame.draw.rect(win, (255, 255, 0), bird)
    pygame.display.update()

pygame.quit()

