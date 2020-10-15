import pygame
import random
import os

path = os.getcwd()
if 'flappy_gym' not in path:
  path = os.path.join(path, 'flappy_gym')

random.seed(1)
# comment out if you're not using jupyter notebook or Google Colab
os.environ["SDL_VIDEODRIVER"] = "dummy"

# scale and optimize graphics for rendering
def load_image(filename):
  img = pygame.image.load(f'{path}/assets/{filename}').convert()
  scale = 1.5
  scaled_size = int(img.get_width() * scale), int(img.get_height() * scale)
  return pygame.transform.scale(img, scaled_size)

# load all graphics needed for rendering
def load_assets(path):
  filenames = ['bird1', 'bird2', 'bird3', 'pipe', 'bg']
  assets = {}
  for fn in filenames:
    assets[fn] = load_image(fn + '.png')
  return assets

def handle_pygame_events():
  # pygame.event.pump()
  for e in pygame.event.get():
    if e.type == pygame.QUIT:
      pygame.quit()
      #sys.exit()

if __name__ == "__main__":
  pass
