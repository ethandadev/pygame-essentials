"""Every pygame-essentials UI widget on one screen.

Run it with:  python examples/ui_demo.py
"""

import pygame

import pygame_essentials as pk

pygame.init()
pygame.key.set_repeat(400, 35)  # hold Backspace/arrows to repeat in the text box
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("pygame-essentials UI demo")
clock = pygame.time.Clock()

BG = (245, 246, 250)
DARK = (30, 30, 40)

title = pk.Label((400, 40), "pygame-essentials UI demo", font_size=48, color=DARK, anchor="center")
status = pk.Label((400, 570), "Try everything!", font_size=26, color=(90, 90, 110), anchor="center")


def say(text):
    status.text = text


# Buttons
play = pk.Button((40, 100), size=(160, 50), text="Play", border_radius=10,
                 color=(60, 130, 240), hover_color=(90, 150, 250), pressed_color=(40, 100, 200),
                 on_click=lambda: say("Play clicked!"))
disabled = pk.Button((220, 100), size=(160, 50), text="Disabled", border_radius=10, enabled=False)

# Text input
name_box = pk.TextInput((40, 190), size=(340, 44), placeholder="Type your name, press Enter",
                        max_length=24, on_submit=lambda t: say(f"Hello, {t or 'nobody'}!"))

# Slider + label showing its value
volume_label = pk.Label((40, 260), "", font_size=26, color=DARK)
volume = pk.Slider((40, 300), size=(340, 8), value=0.7)

difficulty_label = pk.Label((40, 330), "", font_size=26, color=DARK)
difficulty = pk.Slider((40, 370), size=(340, 8), min_value=1, max_value=5, step=1, value=3)

# Checkbox and toggle
show_bar = pk.Checkbox((440, 100), label="Show health bar", checked=True, label_color=DARK)
music = pk.Toggle((440, 150), label="Music", checked=True, label_color=DARK,
                  on_change=lambda on: say(f"Music {'on' if on else 'off'}"))

# Progress bars
health = pk.ProgressBar((440, 300), size=(320, 22), value=1.0, smooth=True,
                        trail_color=(255, 210, 120), border_color=DARK,
                        fill_color=lambda v: (60, 200, 90) if v > 0.3 else (230, 60, 60),
                        text_format=lambda v: f"{round(v * 100)} / 100 HP")
hurt = pk.Button((440, 340), size=(150, 40), text="Hurt", border_radius=8,
                 color=(220, 70, 70), hover_color=(240, 100, 100),
                 on_click=lambda: setattr(health, "value", health.value - 0.15))
heal = pk.Button((610, 340), size=(150, 40), text="Heal", border_radius=8,
                 color=(60, 170, 90), hover_color=(80, 200, 110),
                 on_click=lambda: setattr(health, "value", health.value + 0.25))

loading = pk.ProgressBar((440, 420), size=(320, 14), value=0, show_text=False,
                         fill_color=(60, 130, 240), background=(210, 215, 225))

# Dropdown (handled first, drawn last)
quality = pk.Dropdown((440, 200), ["Low", "Medium", "High", "Ultra", "Potato", "Insane", "Max"],
                      size=(320, 40), selected_index=1, max_visible=4,
                      on_change=lambda q: say(f"Quality set to {q}"))

widgets = [play, disabled, name_box, volume, difficulty, show_bar, music, hurt, heal]

running = True
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if quality.handle_event(event):
            continue  # the dropdown used this event; don't let it click things under the list
        for w in widgets:
            w.handle_event(event)

    for w in widgets:
        w.update(dt)
    health.update(dt)
    loading.value = (loading.value + dt * 0.25) % 1.0
    volume_label.text = f"Volume: {round(volume.value * 100)}%"
    difficulty_label.text = f"Difficulty: {int(difficulty.value)}"
    health.visible = show_bar.checked

    screen.fill(BG)
    for thing in (title, status, volume_label, difficulty_label, health, loading, *widgets):
        thing.draw(screen)
    quality.draw(screen)
    pygame.display.flip()

pygame.quit()
