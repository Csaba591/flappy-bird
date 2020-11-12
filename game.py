import pygame
import sys
import random
import os
import math
import numpy as np
from . import utils

pygame.init()
WIN_WIDTH, WIN_HEIGHT = 400, 667
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

ASSETS = utils.load_assets(utils.path)

GRAVITY = 0.5

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
    self.vel += GRAVITY
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
  vel = 2
  gap = 150
  def __init__(self):
    self.x = WIN_WIDTH
    self.passed = False
    self.pipe_top = pygame.transform.flip(ASSETS['pipe'], False, True)
    self.pipe_bottom = ASSETS['pipe']
    self.set_dimensions()

  def set_dimensions(self):
    dist = random.randint(-180, 180)
    middle = WIN_HEIGHT / 2
    self.top = middle + dist - Pipe.gap / 2 - self.pipe_top.get_height()
    self.bottom = middle + dist + Pipe.gap / 2
    self.width = self.pipe_top.get_width()

  def move(self):
    self.x -= Pipe.vel

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

  # calculate x, y distance to next pipe
  def get_x_y_distance(self, pipe):
    x_dist = pipe.x - self.bird.x
    y_dist_to_bottom_pipe = pipe.bottom - self.bird.y
    y_dist_to_top_pipe = y_dist_to_bottom_pipe - Pipe.gap
    return x_dist, y_dist_to_bottom_pipe, y_dist_to_top_pipe

  def step(self, action):
    # 1 = fly up, 0 = do nothing
    if action == 1:
      self.bird.flap()
    
    # update x, y and velocity
    self.bird.move()
    # move pipes
    for p in self.pipes:
      p.move()
    
    # reward for staying alive
    reward = 0.1

    #--- get next state
    x_distance, y_distance_bottom, y_distance_top = \
      self.get_x_y_distance(self.pipes[0])
    add_pipe = True
    for p in self.pipes:
      pipe_in_front_of_bird = p.x + p.pipe_top.get_width() > self.bird.x
      if pipe_in_front_of_bird:
        # x, y distance to next pipe
        x_distance, y_distance_bottom, y_distance_top = \
          self.get_x_y_distance(p)
        # there's a pipe in front of the bird -> no need for new one
        add_pipe = False
        break # once next one is found, no need to look further
      
      else: # bird has passed pipe p
        # if pipe was passed just now
        if not p.passed:
          reward = 1      # reward for passing pipe
          self.score += 1 # game score
          p.passed = True
          # Pipe.vel *= 1.05
    
    # new state of bird
    next_state = (y_distance_bottom, y_distance_top, x_distance, self.bird.vel)
    
    # if there's no pipe in front of the bird
    # -> add one
    if add_pipe:
      self.pipes.append(Pipe())
    
    # bird dies when it hits a pipe or flies out of the screen
    done = self.check_collision() \
           or self.bird.y  < 0 \
           or self.bird.y + self.bird.img.get_height() > WIN_HEIGHT
    
    # reward for dying
    if done:
      reward = -1
    
    # remove pipes that are out of the screen
    self.clear_pipes()
    
    return np.array(next_state), reward, done   

  def get_state_space_size(self):
    return 4

  # remove pipes that are out of the screen
  def clear_pipes(self):
    if self.pipes[0].x + self.pipes[0].pipe_bottom.get_width() < 0:
      del self.pipes[0]

  # check if bird collides with any of the pipes
  def check_collision(self):
    for p in self.pipes:
      done = p.collide(self.bird)
      if done:
        return done
    return done

  # reset environment to initial state
  def reset(self):
    self.bird.reset()
    self.pipes.clear()
    self.pipes.append(Pipe())
    self.score = 0
    x_distance = self.pipes[0].x - self.bird.x
    y_distance_bottom = self.pipes[0].bottom - self.bird.y
    y_distance_top = y_distance_bottom - Pipe.gap
    return np.array((y_distance_bottom, y_distance_top, x_distance, self.bird.vel))

  # for model training:
  # draw everything and then 
  # return the screen as an RGB numpy array
  
  # for playing the game:
  # draw everything and show it in a window
  def render(self, mode='human'):
    if mode == 'human':
      self.clock.tick(60) # FPS lock
    else:
      self.clock.tick()   # no FPS lock
    #self.screen.blit(ASSETS['bg'], (0, 0))
    self.screen.fill((0, 0, 0)) # black background
    # draw all pipes
    for p in self.pipes:
      p.draw(self.screen)
    # draw bird
    self.bird.draw(self.screen)

    if mode == 'human':
      # show in game window
      pygame.display.update()
      
    # return screen as an array
    screen_arr = pygame.surfarray.array3d(self.screen)
    screen_arr = np.swapaxes(screen_arr, 0, 1)
    if mode == '8color':
      screen_arr = screen_arr / 8.
      screen_arr = np.floor(screen_arr, dtype='float32')
    return screen_arr

  def close(self):
    pygame.quit()
    #sys.exit()