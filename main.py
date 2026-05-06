import pygame
import json

pygame.init()

# Screen dimensions
width = 800
height = 800

game_over = 0
game_over_handled = False
score = 0
tile_size = 40
coin_collected_this_life = False  # Track if coin collected since last death

clock = pygame.time.Clock()
fps = 60

display = pygame.display.set_mode((width, height))
pygame.display.set_caption('SpaceJump Bruh')

bg_image = pygame.image.load('image/bg.png')
bg_rect = bg_image.get_rect()

sound_jump = pygame.mixer.Sound('sounds/jump.wav')
sound_game_over = pygame.mixer.Sound('sounds/game_over.wav')  # Use correct sound here
sound_coin = pygame.mixer.Sound('sounds/coin.wav')

level = 1
max_level = 10

with open(f'levels/level{level}.json', 'r') as file:
    world_data = json.load(file)

lava_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        img = pygame.image.load('map/rhomb3.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        image = pygame.image.load('map/exit.png')
        self.image = pygame.transform.scale(image, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        img = pygame.image.load('map/tile6.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        pass


class World:
    def __init__(self, data, level_num):
        dirt_img = pygame.image.load('map/tile10.png')
        grass_img = pygame.image.load('map/tile9.png')
        self.tile_list = []
        images = {1: dirt_img, 2: grass_img}

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1 or tile == 2:
                    img = pygame.transform.scale(images[tile], (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile_data = (img, img_rect)
                    self.tile_list.append(tile_data)
                elif tile == 3:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                elif tile == 5:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                elif tile == 6:
                    if level_num >= 3:
                        coin = Coin(col_count * tile_size + (tile_size // 2),
                                    row_count * tile_size + (tile_size // 2))
                        coin_group.add(coin)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            display.blit(tile[0], tile[1])


class Button:
    def __init__(self, x, y, image):
        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self):
        action = False
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True
        display.blit(self.image, self.rect)
        return action


restart_button = Button(width // 2, height // 2, 'button/restart_btn.png')
start_button = Button(width // 2 - 150, height // 2, 'button/start_btn.png')
exit_button = Button(width // 2 + 150, height // 2, 'button/exit_btn.png')


def draw_text(text, color, size, x, y):
    font = pygame.font.SysFont('Arial', size)
    img = font.render(text, True, color)
    display.blit(img, (x, y))


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        self.direction = 1

        # Load all player images (player1.png to player4.png)
        for num in range(1, 5):
            img_right = pygame.image.load(f'image/player{num}.png')
            img_right = pygame.transform.scale(img_right, (35, 70))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)

        self.flame_img = pygame.transform.scale(pygame.image.load('image/flames.png'), (40, 70))

        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 500

        self.gravity = 0
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.jumped = False

    def update(self):
        global game_over, game_over_handled, score, coin_collected_this_life
        x = 0
        y = 0
        walk_speed = 5  # Controls how fast the animation updates

        if game_over == 0:
            key = pygame.key.get_pressed()

            if key[pygame.K_SPACE] and not self.jumped:
                self.gravity = -15
                self.jumped = True
                sound_jump.play()

            if key[pygame.K_LEFT]:
                x -= 5
                self.direction = -1
                self.counter += 1

            if key[pygame.K_RIGHT]:
                x += 5
                self.direction = 1
                self.counter += 1

            if key[pygame.K_LEFT] or key[pygame.K_RIGHT]:
                if self.counter > walk_speed:
                    self.counter = 0
                    self.index += 1
                    if self.index >= len(self.images_right):
                        self.index = 0
                    self.image = self.images_right[self.index] if self.direction == 1 else self.images_left[self.index]
            else:
                # Stand still on first frame
                self.index = 0
                self.image = self.images_right[0] if self.direction == 1 else self.images_left[0]

            self.gravity += 1
            if self.gravity > 10:
                self.gravity = 10
            y += self.gravity

            for tile in world.tile_list:
                tile_rect = tile[1]

                if tile_rect.colliderect(self.rect.x + x, self.rect.y, self.width, self.height):
                    x = 0

                if tile_rect.colliderect(self.rect.x, self.rect.y + y, self.width, self.height):
                    if self.gravity < 0:
                        y = tile_rect.bottom - self.rect.top
                        self.gravity = 0
                    elif self.gravity >= 0:
                        y = tile_rect.top - self.rect.bottom
                        self.gravity = 0
                        self.jumped = False

            if self.rect.bottom + y > height:
                y = height - self.rect.bottom
                self.jumped = False
                self.gravity = 0

            self.rect.x += x
            self.rect.y += y

            if pygame.sprite.spritecollide(self, lava_group, False):
                if game_over == 0:
                    self.image = self.flame_img
                    self.rect = self.image.get_rect(center=self.rect.center)
                    if coin_collected_this_life:
                        score = max(0, score - 1)
                    game_over = -1

            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

        elif game_over == -1 and not game_over_handled:
            sound_game_over.play()
            print("Game Over")
            game_over_handled = True

        display.blit(self.image, self.rect)


def reset_level():
    global world_data, game_over_handled, coin_collected_this_life
    player.rect.x = 100
    player.rect.y = height - 130
    lava_group.empty()
    exit_group.empty()
    coin_group.empty()
    game_over_handled = False
    coin_collected_this_life = False
    with open(f'levels/level{level}.json', 'r') as file:
        world_data = json.load(file)
    return World(world_data, level)


world = World(world_data, level)
player = Player()

run = True
main_menu = True

while run:
    clock.tick(fps)
    display.blit(bg_image, bg_rect)

    if main_menu:
        if start_button.draw():
            level = 1
            score = 0
            game_over = 0
            game_over_handled = False
            with open(f'levels/level{level}.json', 'r') as file:
                world_data = json.load(file)
            world = World(world_data, level)
            player = Player()
            main_menu = False
        if exit_button.draw():
            run = False
    else:
        world.draw()
        coin_group.draw(display)
        lava_group.draw(display)
        exit_group.draw(display)
        draw_text(str(score), (255, 255, 255), 30, 10, 10)
        lava_group.update()
        player.update()

        if pygame.sprite.spritecollide(player, coin_group, True):
            sound_coin.play()
            score += 1
            coin_collected_this_life = True
            print(score)

        if game_over == -1:
            if restart_button.draw():
                player = Player()
                world = reset_level()
                game_over = 0

        if game_over == 1:
            game_over = 0
            if level < max_level:
                level += 1
                world = reset_level()
            else:
                print('win')
                main_menu = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
