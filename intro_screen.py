import pygame
import os
import time
import subprocess

pygame.init()
pygame.mixer.init()

# -----------------------------
# Load assets
# -----------------------------
ASSET_DIR = "assets"
images = ["intro1.jpg", "intro2.jpg", "intro3.jpg", "intro4.jpg","intro5.jpg","intro7.jpg"]
images = [os.path.join(ASSET_DIR, img) for img in images]

loaded_images = [pygame.image.load(img) for img in images]

music_path = os.path.join(ASSET_DIR, "music.mp3")
if os.path.exists(music_path):
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(-1)
else:
    print("⚠ music.mp3 not found.")

# -----------------------------
# Screen Setup
# -----------------------------
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()

loaded_images = [
    pygame.transform.scale(img, (screen_width, screen_height))
    for img in loaded_images
]

# Fonts
# Fonts
title_font = pygame.font.Font(None, 110)
subtitle_font = pygame.font.Font(None, 52)

title = title_font.render("Bharatanatyam Mudra Recognition", True, (255, 215, 160))
subtitle = subtitle_font.render("Press SPACE to Begin", True, (255, 245, 230))


# -----------------------------
# FADE-IN EFFECT
# -----------------------------
def fade_in():
    fade = pygame.Surface((screen_width, screen_height))
    for alpha in range(0, 255, 8):
        fade.set_alpha(alpha)
        screen.blit(loaded_images[0], (0, 0))
        screen.blit(title, (80, 100))
        pygame.display.update()
        pygame.time.delay(30)

# -----------------------------
# FADE-OUT EFFECT
# -----------------------------
def fade_out():
    fade = pygame.Surface((screen_width, screen_height))
    for alpha in range(0, 255, 10):
        fade.set_alpha(alpha)
        screen.blit(loaded_images[0], (0, 0))
        pygame.display.update()
        pygame.time.delay(20)

fade_in()

# -----------------------------
# Slideshow Loop
# -----------------------------
index = 0
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                fade_out()
                pygame.quit()
                subprocess.Popen(["python", "live_demo.py"])
                quit()

    screen.blit(loaded_images[index], (0, 0))
    screen.blit(title, (80, 100))
    screen.blit(subtitle, (80, screen_height - 120))

    pygame.display.flip()
    time.sleep(2)

    index = (index + 1) % len(loaded_images)


