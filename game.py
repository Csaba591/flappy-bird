import pygame
import sys
import random
import os
import math
import numpy as np

if 'flappy_gym' not in os.getcwd():
  os.chdir('flappy_gym')

random.seed(1)

# comment out if you're not using jupyter notebook or Google Colab
os.environ["SDL_VIDEODRIVER"] = "dummy"
WIN_WIDTH, WIN_HEIGHT = 400, 667
pygame.init()
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

def load_image(filename):
  img = pygame.image.load(f'assets/{filename}').convert()
  scale = 1.5
  scaled_size = int(img.get_width() * scale), int(img.get_height() * scale)
  return pygame.transform.scale(img, scaled_size)

ASSETS = {
  'bird1': load_image('bird1.png'),
  'bird2': load_image('bird2.png'),
  'bird3': load_image('bird3.png'),
  'pipe': load_image('pipe.png'),
  'bg': load_image('bg.png')
  }

GRAVITY = 1

class Bird:
  def __init__(self):
    self.IMGS = [ASSETS['bird1'], ASSETS['bird2'], ASSETS['bird3']]
    self.width = self.IMGS[0].get_width()
    self.height = self.IMGS[0].get_height()
    self.ANIMATION_TIME = 5

    self.reset()

  def flap(self):
    self.vel = -8
    self.tick_count = 0

  def move(self):
    self.tick_count += 1
    self.vel += 0.5
    if self.vel > self.max_vel:
      self.vel = self.max_vel
    self.y += self.vel

  def reset(self):
    self.x = WIN_WIDTH / 3
    self.y = WIN_HEIGHT / 2
    self.tick_count = 0
    self.vel = 0
    self.max_vel = 12
    self.img_count = 0
    self.img = self.IMGS[0]

  def draw(self, screen):
    screen.blit(self.IMGS[(self.tick_count // self.ANIMATION_TIME) % len(self.IMGS)], (self.x, self.y))

  def get_mask(self):
    return pygame.mask.from_surface(self.img)

class Pipe:
  def __init__(self):
    self.vel = 2
    self.gap = 150
    self.x = WIN_WIDTH
    self.passed = False
    self.pipe_top = pygame.transform.flip(ASSETS['pipe'], False, True)
    self.pipe_bottom = ASSETS['pipe']
    self.set_dimensions()

  def set_dimensions(self):
    dist = random.randint(-180, 180)
    middle = WIN_HEIGHT / 2
    self.top = middle + dist - self.gap / 2 - self.pipe_top.get_height()
    self.bottom = middle + dist + self.gap / 2
    self.width = self.pipe_top.get_width()

  def move(self):
    self.x -= self.vel

  def draw(self, screen):
    screen.blit(self.pipe_top, (self.x, self.top))
    screen.blit(self.pipe_bottom, (self.x, self.bottom))

  def collide_simple(self, bird):
    if bird.y <= self.top or bird.y + bird.height >= self.bottom:
      if bird.x <= self.x + self.width and bird.x + bird.width >= self.x:
        return True
      elif bird.y < 0 or bird.y + bird.heigth > WIN_HEIGHT:
        return True
    return False

  def collide(self, bird):
    bird_mask = bird.get_mask()
    top_mask = pygame.mask.from_surface(self.pipe_top)
    bottom_mask = pygame.mask.from_surface(self.pipe_bottom)

    top_offset = (int(self.x - bird.x), int(self.top - round(bird.y)))
    bottom_offset = (int(self.x - bird.x), int(self.bottom - round(bird.y)))
    
    bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
    top_point = bird_mask.overlap(top_mask, top_offset)
    
    return bottom_point != None or top_point != None

class FlappyBird():
  def __init__(self):
    self.bird = Bird()
    self.pipes = [Pipe()]
    self.clock = pygame.time.Clock()
    self.score = 0
    self.screen = screen

  def step(self, action):
    if action == 1:
      self.bird.flap()
    
    self.bird.move()
    
    reward = 15

    # get next state
    y_distance_bottom = self.pipes[0].bottom - self.bird.y
    y_distance_middle = self.pipes[0].bottom - self.pipes[0].gap / 2 - self.bird.y + self.bird.height / 2
    x_distance = self.pipes[0].x - self.bird.x
    add_pipe = True
    pipe_passed = False
    for p in self.pipes:
      if p.x + p.pipe_top.get_width() > self.bird.x:
        # calculate x, y distance to next pipe
        y_distance_bottom = p.bottom - self.bird.y
        y_distance_middle = p.bottom - p.gap / 2 - self.bird.y + self.bird.height / 2
        x_distance = p.x - self.bird.x
        # there's a pipe in front of the bird -> no need for new one
        add_pipe = False
        break # once next one is found, no need to look further
      else:
        # add score if pipe was passed just now
        if not p.passed:
          reward = 100
          pipe_passed = True
          self.score += 1
          p.passed = True
    next_state = (y_distance_bottom, x_distance, self.bird.vel)
    
    '''if pipe_passed:
      reward = 500
    else:
      reward = -int(math.sqrt(x_distance ** 2 + y_distance_middle ** 2))'''

    if add_pipe:
      self.pipes.append(Pipe())
    
    # bird dies when it hits a pipe or flies out of the screen
    done = self.check_collision() \
           or self.bird.y + self.bird.img.get_height() < 0 \
           or self.bird.y > WIN_HEIGHT
    
    if not done:
      for p in self.pipes:
        p.move()
    self.clear_pipes()
    
    if done:
      reward = -1000
      
    return next_state, reward, done   

  def get_state_space_size(self):
    return 3

  def clear_pipes(self):
    if self.pipes[0].x + self.pipes[0].pipe_bottom.get_width() < 0:
      del self.pipes[0]

  def check_collision(self):
    for p in self.pipes:
      done = p.collide(self.bird)
      if done: 
        print('collision')
        return done
    return done

  def reset(self):
    self.bird.reset()
    self.pipes.clear()
    self.pipes.append(Pipe())
    self.score = 0
    x_distance = self.pipes[0].x - self.bird.x
    y_distance_bottom = self.pipes[0].bottom - self.bird.y
    return (y_distance_bottom, x_distance, self.bird.vel)

  # for model training:
  # draw everything and then 
  # return the screen as an RGB numpy array
  
  # for playing the game:
  # draw everything and show it in a window
  def render(self, mode='human'):
    if mode == 'human':
      self.clock.tick(60)
    else:
      self.clock.tick()
    #self.screen.blit(ASSETS['bg'], (0, 0))
    self.screen.fill((0, 0, 0))
    for p in self.pipes:
      p.draw(self.screen)
    self.bird.draw(self.screen)
    if mode=='human':
      pygame.display.update()
    else:
      screen_arr = pygame.surfarray.array3d(self.screen)
      screen_arr = np.swapaxes(screen_arr, 0, 1)
      return screen_arr

  def close(self):
    pygame.quit()
    #sys.exit()

def handle_pygame_events():
  # pygame.event.pump()
  for e in pygame.event.get():
    if e.type == pygame.QUIT:
      pygame.quit()
      #sys.exit()