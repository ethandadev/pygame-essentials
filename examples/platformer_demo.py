"""A tiny platformer showing Camera, Spritesheet/Animation, particles, Timer/Cooldown, SaveData and DebugOverlay.

Controls:
    A / D or ← / →   move
    Space / W / ↑    jump   (dust + small screen shake on landing)
    Shift            dash   (1 second cooldown, shown as a bar)
    F3               debug overlay (FPS, hitboxes, watched values)
    Collect the yellow coins. Your best coin count is saved between runs.

Run it with:  python examples/platformer_demo.py

The player's spritesheet is drawn in code, so this demo needs no image files.
"""

import random

import pygame

import pygame_essentials as pk

pygame.init()
W, H = 960, 540
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("pygame-essentials platformer demo")
clock = pygame.time.Clock()


# ------------------------------------------------------------------ assets
def make_player_sheet() -> pygame.Surface:
    """Draw a 4x2 spritesheet of 16x16 frames: row 0 = idle (bobbing), row 1 = run (legs moving)."""
    sheet = pygame.Surface((16 * 4, 16 * 2), pygame.SRCALPHA)
    body, eye, leg = (80, 170, 255), (20, 20, 40), (40, 90, 160)
    for i in range(4):
        # idle: body bobs up and down
        bob = (0, 1, 1, 0)[i]
        ox, oy = i * 16, 0
        pygame.draw.rect(sheet, body, (ox + 3, oy + 3 + bob, 10, 10), border_radius=3)
        pygame.draw.rect(sheet, eye, (ox + 9, oy + 6 + bob, 2, 3))
        pygame.draw.rect(sheet, leg, (ox + 4, oy + 13, 3, 3))
        pygame.draw.rect(sheet, leg, (ox + 9, oy + 13, 3, 3))
        # run: legs alternate
        ox, oy = i * 16, 16
        pygame.draw.rect(sheet, body, (ox + 3, oy + 2, 10, 10), border_radius=3)
        pygame.draw.rect(sheet, eye, (ox + 9, oy + 5, 2, 3))
        a, b = [(2, 7), (4, 9), (6, 5), (4, 9)][i]
        pygame.draw.rect(sheet, leg, (ox + a, oy + 12, 3, 4))
        pygame.draw.rect(sheet, leg, (ox + b, oy + 12, 3, 4))
    return sheet


sheet = pk.Spritesheet(make_player_sheet(), 16, 16, scale=3)
run_right = pk.Animation(sheet.frames(row=1), fps=12)
anims = pk.AnimationSet({
    "idle_right": pk.Animation(sheet.frames(row=0), fps=4),
    "run_right": run_right,
    "idle_left": pk.Animation(sheet.frames(row=0), fps=4).flipped(),
    "run_left": run_right.flipped(),
})

# ------------------------------------------------------------------- level
WORLD = pygame.Rect(0, 0, 3000, 900)
platforms = [pygame.Rect(0, 840, 3000, 60)]
random.seed(4)
x = 150
while x < 2800:
    platforms.append(pygame.Rect(x, random.randint(480, 780), random.randint(120, 260), 24))
    x += random.randint(180, 320)
coins = [pygame.Rect(p.centerx - 8, p.y - 40, 16, 16) for p in platforms[1:]]

# ------------------------------------------------------------------ player
player = pygame.Rect(80, 700, 36, 42)
vel = pygame.Vector2(0, 0)
on_ground = False
facing = "right"
GRAVITY, SPEED, JUMP, DASH = 1800, 320, 720, 900

dash_cooldown = pk.Cooldown(1.0)
dash_timer = pk.Timer(0.15, autostart=False)
coyote = pk.Timer(0.1, autostart=False)  # lets you jump a split second after walking off a ledge

# ---------------------------------------------------------------- effects
camera = pk.Camera((W, H), world_rect=WORLD, follow_speed=8, offset=(0, -60), deadzone=(120, 80))
camera.follow(player)
camera.snap_to()

dust = pk.ParticleEmitter(colors=[(210, 200, 180), (180, 170, 150)], angle=-90, spread=170,
                          speed=(40, 140), size=(3, 6), end_size=0, lifetime=(0.25, 0.5),
                          gravity=(0, 300), drag=3)
sparkle = pk.ParticleEmitter(colors=[(255, 230, 90), (255, 255, 200)], speed=(60, 220),
                             size=(2, 4), lifetime=(0.3, 0.6), gravity=(0, 250))
dash_trail = pk.ParticleEmitter(rate=90, emitting=False, colors=[(255, 255, 255)], speed=(0, 20),
                                size=(5, 9), end_size=0, lifetime=0.25, fade=True)

# ------------------------------------------------------------- UI + extras
save = pk.SaveData("pygame-essentials-platformer-demo", defaults={"best_coins": 0})
score = 0
score_label = pk.Label((W - 20, 16), "", font_size=34, color="white", anchor="topright",
                       background=(0, 0, 0), padding=8, border_radius=8)
dash_bar = pk.ProgressBar((20, H - 36), size=(160, 14), fill_color=(80, 170, 255),
                          background=(30, 40, 60), border_color=(255, 255, 255), border_width=1)
help_label = pk.Label((20, H - 62), "Shift: dash    F3: debug", font_size=22, color=(230, 235, 255))

debug = pk.DebugOverlay(position=(10, 10))
debug.watch("player", lambda: player.topleft)
debug.watch("velocity", lambda: f"{vel.x:.0f}, {vel.y:.0f}")
debug.watch("on ground", lambda: on_ground)
debug.watch("dash ready", lambda: dash_cooldown.ready())
debug.watch("particles", lambda: len(dust) + len(sparkle) + len(dash_trail))
debug.watch("save file", lambda: save.path.name)

running = True
while running:
    dt = min(clock.tick(60) / 1000, 1 / 20)  # cap dt so a lag spike can't push you through floors

    jump_pressed = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        debug.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
            jump_pressed = True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            if dash_cooldown.use():
                dash_timer.start()
                camera.shake(3, 0.1)

    keys = pygame.key.get_pressed()
    move = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    if move:
        facing = "right" if move > 0 else "left"

    # timers
    dash_cooldown.update(dt)
    dash_timer.update(dt)
    coyote.update(dt)
    dashing = dash_timer.running

    # movement
    if dashing:
        vel.x = DASH if facing == "right" else -DASH
        vel.y = 0
    else:
        vel.x = move * SPEED
        vel.y += GRAVITY * dt
    if jump_pressed and (on_ground or coyote.running):
        vel.y = -JUMP
        coyote.stop()
        dust.burst(8, pos=player.midbottom)

    player.x += round(vel.x * dt)
    player.clamp_ip(WORLD)
    for p in platforms:
        if player.colliderect(p):
            if vel.x > 0:
                player.right = p.left
            elif vel.x < 0:
                player.left = p.right

    was_on_ground = on_ground
    player.y += round(vel.y * dt)
    for p in platforms:
        if player.colliderect(p):
            if vel.y > 0:
                player.bottom = p.top
            elif vel.y < 0:
                player.top = p.bottom
            vel.y = 0
    # check 1px below the feet, so standing still doesn't flicker between "on ground" and "falling"
    on_ground = vel.y >= 0 and any(player.move(0, 1).colliderect(p) for p in platforms)
    if on_ground:
        vel.y = 0
    if on_ground and not was_on_ground:
        dust.burst(14, pos=player.midbottom)
        camera.shake(4, 0.15)
    if was_on_ground and not on_ground and vel.y >= 0:
        coyote.start()

    for coin in coins[:]:
        if player.colliderect(coin):
            coins.remove(coin)
            score += 1
            sparkle.burst(30, pos=coin.center)
            if save.set_max("best_coins", score):
                score_label.color = (255, 230, 90)

    # effects
    dash_trail.pos = player.center
    dash_trail.emitting = dashing
    for emitter in (dust, sparkle, dash_trail):
        emitter.update(dt)
    anims.play(("run_" if move else "idle_") + facing)
    anims.update(dt)
    camera.update(dt)
    debug.update(dt)
    score_label.text = f"Coins: {score}   Best: {save['best_coins']}"
    dash_bar.value = dash_cooldown.progress

    # ---------------------------------------------------------------- draw
    screen.fill((110, 170, 230))
    for i in range(6):  # simple parallax hills
        hx = (i * 600 - camera.position.x * 0.3) % 3600 - 600
        pygame.draw.circle(screen, (90, 150, 120), (hx, H + 200 - camera.position.y * 0.1), 420)
    for p in platforms:
        if camera.is_visible(p):
            r = camera.apply(p)
            pygame.draw.rect(screen, (95, 70, 50), r)
            pygame.draw.rect(screen, (90, 190, 90), (r.x, r.y, r.width, 6))
            debug.draw_rect(p, (0, 255, 0))
    for coin in coins:
        if camera.is_visible(coin):
            pygame.draw.circle(screen, (255, 210, 60), camera.apply(coin).center, 8)
            debug.draw_rect(coin, (255, 255, 0))
    dash_trail.draw(screen, camera)
    image = anims.image
    screen.blit(image, image.get_rect(midbottom=camera.apply(player).midbottom))
    debug.draw_rect(player, (255, 0, 255), 2)
    dust.draw(screen, camera)
    sparkle.draw(screen, camera)

    score_label.draw(screen)
    help_label.draw(screen)
    dash_bar.draw(screen)
    debug.draw(screen, camera)
    pygame.display.flip()

pygame.quit()
