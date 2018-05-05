import pygame
import os
import random

os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()

game_exit = False

button_pressed = {'w': False,
                  'a': False,
                  's': False,
                  'd': False,
                  'up': False,
                  'left': False,
                  'down': False,
                  'right': False,
                  'shift': False,
                  'ctrl': False,
                  'space': False,
                  'enter': False,
                  'p': False,
                  'o': False,
                  'mouse_1': False,
                  'mouse_2': False}

is_mouse_visible = True
tracker_pos = 0

starting_screen_shift = [0, 0]  # How much the screen is shifted by originally
jump_velocity = -65  # Initial jumping velocity

# Colours

off_white = (230, 230, 230)
white = (255, 255, 255)
black = (0, 0, 0)
grey = (60, 60, 60)
light_grey = (135, 135, 135)
red = (245, 0, 0)
green = (0, 215, 0)
blue = (0, 0, 245)
light_blue = (0, 191, 255)
purple = (150, 0, 175)
pink = (245, 105, 180)
turquoise = (0, 206, 209)
yellow = (255, 255, 0)
ochre = (204, 119, 34)
gold = (255, 215, 0)
brown = (155, 83, 19)
light_brown = (255, 218, 185)

# Official Resolution is display_width = 800 display_height = 600

display_width = 1000
display_height = 600
resolution = (display_width, display_height)

Display = pygame.display.set_mode(resolution)

pygame.display.set_caption('Drag Drop Adventure')

clock = pygame.time.Clock()

# Fonts
small_font_size = display_height // 25
med_font_size = display_height // 12
large_font_size = display_height // 5

small_font = pygame.font.SysFont('Roboto', small_font_size)
med_font = pygame.font.SysFont('Roboto', med_font_size)
large_font = pygame.font.SysFont('Roboto', large_font_size)

# Images
images = {'ground': pygame.image.load('Ground.jpg'),
          'sensor': pygame.image.load('Sensor.png'),
          'stationary goal': pygame.image.load('Stationary Goal.png'),
          'portable goal': pygame.image.load('Portable Goal.png'),
          'final goal': pygame.image.load('Final Goal.png'),
          'sign': pygame.image.load('Sign.png'),
          'star': pygame.image.load('Star.png'),
          'grey star': pygame.image.load('Grey Star.png'),
          'lock': pygame.image.load('Lock.png'),
          'enemy': pygame.image.load('Enemy.png'),
          'moveable enemy': pygame.image.load('Moveable Enemy.png'),
          'guard': pygame.image.load('Guard.png'),
          'spikes': pygame.image.load('Spikes.png'),
          'boulder': pygame.image.load('Boulder.png'),
          'player': pygame.image.load('Player.png')}

# Sounds
sounds = {'boulder crush': pygame.mixer.Sound('Boulder Crush.wav'),
          'thump': pygame.mixer.Sound('Thump.wav'),
          'click': pygame.mixer.Sound('Click.wav'),
          'jump': pygame.mixer.Sound('Jump.wav')}

for sound in sounds:
	if sound == 'thump':
		pygame.mixer.Sound.set_volume(sounds[sound], 0.05)
	else:
		pygame.mixer.Sound.set_volume(sounds[sound], 0.2)

# Music
music = {'game over': 'Game Over.wav',
         'level complete': 'Success.wav'}


class InputButtonStates:
	def __init__(self):
		self.w = [False]
		self.a = [False]
		self.s = [False]
		self.d = [False]
		self.up = [False]
		self.left = [False]
		self.down = [False]
		self.right = [False]

		self.mouse_1 = [False]

		self.enter = [False]
		self.space = [False]

	def update(self):

		for attr, value in self.__dict__.items():
			if button_pressed[attr]:
				value.insert(0, True)
			else:
				value.insert(0, False)
			value = value[:3]
			setattr(self, attr, value)


class Ability:
	def __init__(self):
		self.recharge_from_empty = 0.75  # 1 less than the maximum time it takes for ability to recharge, in seconds
		self.being_used = False
		self.recharge_time_left = 0  # Time left to recharge

		self.time_to_be_added = 0


class CoolDownBar:
	def __init__(self):
		self.width = 100
		self.height = 30
		self.x = (display_width / 2) - (self.width / 2)
		self.y = display_height - 3 * self.height / 2
		self.outline = 1  # Thickness of the outline
		self.outline_colour = black
		self.colour = light_blue

		self.incomplete_colour = grey

		self.total_time_to_recharge = None
		self._current_recharge_time = None
		self.completion = 1  # How complete the bar is as a fraction from 0 to 1

	@property
	def current_recharge_time(self):
		return self._current_recharge_time

	@current_recharge_time.setter
	def current_recharge_time(self, value):
		self._current_recharge_time = value
		if self.total_time_to_recharge is not None:
			self.completion = (self.total_time_to_recharge - value) / self.total_time_to_recharge
			if self.completion > 1:
				self.completion = 1

	def draw(self):
		pygame.draw.rect(Display, self.outline_colour, [self.x - self.outline,
		                                                self.y - self.outline,
		                                                self.width + 2 * self.outline,
		                                                self.height + 2 * self.outline])

		pygame.draw.rect(Display, self.incomplete_colour, [self.x,
		                                                   self.y,
		                                                   self.width,
		                                                   self.height])

		pygame.draw.rect(Display, self.colour, [self.x,
		                                        self.y,
		                                        self.width * self.completion,
		                                        self.height])


class Character:
	def __init__(self, x=display_width / 2,
	             y=display_height / 2,
	             width=30, height=48, img=images['player']):
		self.x_range = (100, display_width - 100 - width)
		self.original_x = x - width
		self.original_y = y
		self._x = self.original_x
		self._y = self.original_y

		self.width = width
		self.height = height
		self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

		self.velocity = 0
		self.original_facing = 'right'
		self.facing = self.original_facing

		self.colour = green
		self.img = img
		self.mask = pygame.mask.from_surface(self.img)
		self.tint = None

		self.last_eligible_pos = None
		self.visible = True

		if type(self).__name__ not in {'GhostCharacter', 'CollisionDetector', 'JumpDetector'}:
			self.ghost = GhostCharacter(self.x, self.y,
			                            self.width, self.height,
			                            self.img, self)
		if type(self).__name__ not in {'GhostCharacter', 'CollisionDetector', 'JumpDetector'}:
			self.collision_detector = CollisionDetector(self.x, self.y,
			                                            self.width, self.height,
			                                            self.img)
		if type(self).__name__ not in {'GhostCharacter', 'CollisionDetector', 'JumpDetector'}:
			self.jump_detector = JumpDetector(self.x, self.y + 1,
			                                  self.width, self.height,
			                                  self.img, self)

		self.update_rect()

		self.can_drag = True
		self.can_move = True
		self.can_fall = True

	@property
	def x_with_shift(self):
		return self.x

	@x_with_shift.setter
	def x_with_shift(self, value):
		self._x = value
		self.update_rect()

	@property
	def y_with_shift(self):
		return self.y

	@y_with_shift.setter
	def y_with_shift(self, value):
		self._y = value
		self.update_rect()

	@property
	def x(self):
		return self._x

	@x.setter
	def x(self, value):
		self._x = value
		self.x_with_shift = value
		self.update_rect()

	@property
	def y(self):
		return self._y

	@y.setter
	def y(self, value):
		self._y = value
		self.y_with_shift = value
		self.update_rect()

	def draw(self):
		self.update_rect()
		if self.img is not None:
			if self.facing != self.original_facing:
				img = pygame.transform.flip(self.img, True, False)
			else:
				img = self.img

		if self.visible:
			if self.img is None:
				pygame.draw.rect(Display, self.colour, self.rect)
			else:
				Display.blit(img, (self.x_with_shift, self.y_with_shift))
				if self.tint is not None:
					Display.blit(self.colourize(self.tint, self.facing), (self.x_with_shift, self.y_with_shift))

	def colourize(self, colour, direction):
		if direction != self.original_facing:
			image = pygame.transform.flip(self.img, True, False)
		else:
			image = self.img.copy()

		# zero out RGB values
		image.fill((0, 0, 0, 100), None, pygame.BLEND_RGBA_MULT)
		# add in new RGB values
		image.fill(colour[0:3] + (0,), None, pygame.BLEND_RGBA_ADD)

		return image

	def follow(self, original_mouse_pos, mouse_pos):
		loc_rel_chr = original_mouse_pos[0] - self.original_x, original_mouse_pos[1] - self.original_y
		self.x = mouse_pos[0] - loc_rel_chr[0]
		self.y = mouse_pos[1] - loc_rel_chr[1]

	def update_rect(self):
		self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


class GhostCharacter(Character):
	def __init__(self, x=display_width / 2,
	             y=display_height / 2,
	             width=30,
	             height=48, img=images['player'], character=None):
		super().__init__(x=x, y=y, width=width, height=height, img=img)

		self.visible = False

		self.character = character

		if self.img is not None:
			self.surface = self.img.convert_alpha()
		else:
			self.surface = pygame.Surface((self.width, self.height))
		self.surface.set_alpha(150)

		if self.img is None:
			self.surface.fill(self.colour)
		else:
			self.surface.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)

	def draw(self):
		if self.character.facing != self.character.original_facing:
			surface = pygame.transform.flip(self.surface, True, False)
		else:
			surface = self.surface
		if self.visible:
			Display.blit(surface, (self.x, self.y))


class CollisionDetector(Character):
	def __init__(self,
	             x=display_width / 2, y=display_height / 2,
	             width=30, height=48, img=images['player']):
		super().__init__(x=x, y=y, width=width, height=height, img=img)
		self.did_collide = False  # True if it collided with something in the previous check
		self.colour = blue


class JumpDetector(CollisionDetector):
	def __init__(self, x=display_width / 2,
	             y=display_height / 2,
	             width=30, height=48,
	             img=images['player'], character=None):
		super().__init__(x, y,
		                 width, height,
		                 img)

		self.character = character

		if self.img is not None:
			self.surface = self.img.convert_alpha()
		else:
			self.surface = pygame.Surface((self.width, self.height))
		self.surface.set_alpha(150)

		if self.img is None:
			self.surface.fill(grey)
		else:
			self.surface.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)

	def draw(self):
		Display.blit(self.surface, (self.x, self.y))

	def can_jump(self, blocks):
		if self.character is not None:
			self.x = self.character.x_with_shift
			self.y = self.character.y_with_shift + 1
			if self.rect.collidelist(blocks) != -1:
				return True
			else:
				return False
		else:
			return None

	def might_fall(self, blocks):
		if hasattr(self.character, 'to_move'):
			if self.character.to_move < 0:
				direction = -1
			elif self.character.to_move > 0:
				direction = 1
			else:
				direction = 0

			self.x, self.y = self.character.x_with_shift, self.character.y_with_shift

			self.x += self.character.width * direction
			self.y += 1

			if self.rect.collidelist(blocks) != -1:
				return False
			else:
				return True
		else:
			return None


class Mob(Character):
	def __init__(self, x=display_width / 2,
	             y=display_height / 2,
	             width=30, height=48,
	             img=images['enemy'],
	             name=None,
	             can_drag=True, can_move=True, can_fall=True):
		super().__init__(x + width, y, img.get_rect().width, img.get_rect().height, img)
		self.mask = pygame.mask.from_surface(self.img)
		# self.width = img.get_rect().width
		# self.height = img.get_rect().height

		self.can_drag = can_drag
		self.can_move = can_move
		self.can_fall = can_fall
		self.name = name

		self.to_move = 1

	@property
	def x_with_shift(self):
		return self.x + screen_shift.x

	@x_with_shift.setter
	def x_with_shift(self, value):
		self._x = value - screen_shift.x
		self.update_rect()

	@property
	def y_with_shift(self):
		return self.y + screen_shift.y

	@y_with_shift.setter
	def y_with_shift(self, value):
		self._y = value - screen_shift.y
		self.update_rect()

	@property
	def x(self):
		return self._x

	@x.setter
	def x(self, value):
		self._x = value
		self.update_rect()

	@property
	def y(self):
		return self._y

	@y.setter
	def y(self, value):
		self._y = value
		self.update_rect()

	def update_rect(self):
		self.rect = pygame.Rect(self.x_with_shift,
		                        self.y_with_shift,
		                        self.width, self.height)


class Boulder(Mob):
	def __init__(self, x=display_width / 2,
	             y=display_height / 2,
	             width=30, height=48,
	             img=images['enemy'],
	             name=None,
	             can_drag=True, can_move=True, can_fall=True):
		super().__init__(x, y, width, height, img, name, can_drag, can_move, can_fall)


class Block:
	def __init__(self, x=0, y=0, width=50, height=50, texture=images['ground']):
		self._x = x
		self._y = y
		self.width = int(width)
		self.height = int(height)
		self.rect = pygame.Rect(screen_shift.x + self.x, screen_shift.y + self.y, self.width, self.height)
		if not isinstance(texture, tuple):
			self.texture = pygame.transform.scale(texture, (self.width, self.height))
		else:
			self.texture = texture

		self.tint = None

		self.final = False

	@property
	def x(self):
		return self._x

	@x.setter
	def x(self, value):
		self._x = value
		self.rect = pygame.Rect(screen_shift.x + self._x, screen_shift.y + self.y, self.width, self.height)

	@property
	def y(self):
		return self._y

	@y.setter
	def y(self, value):
		self._y = value
		self.rect = pygame.Rect(screen_shift.x + self.x, screen_shift.y + self._y, self.width, self.height)

	def update_rect(self):
		self.rect = pygame.Rect(screen_shift.x + self.x, screen_shift.y + self.y, self.width, self.height)

	def draw(self):
		self.update_rect()

		if isinstance(self.texture, tuple):
			pygame.draw.rect(Display, self.texture, self.rect)
		elif self.texture.__class__.__name__ == 'Surface':
			Display.blit(self.texture, self.rect)
			if self.tint is not None:
				Display.blit(self.colourize(self.tint), self.rect)

	def colourize(self, colour):
		image = self.texture.copy()

		# zero out RGB values
		image.fill((0, 0, 0, 100), None, pygame.BLEND_RGBA_MULT)
		# add in new RGB values
		image.fill(colour[0:3] + (0,), None, pygame.BLEND_RGBA_ADD)

		return image


class Sign(Mob):
	def __init__(self, msg='',
	             x=display_width / 2,
	             y=display_height / 2,
	             width=50, height=50,
	             img=images['sign'],
	             name=None,
	             can_drag=False, can_move=False, can_fall=False):
		super().__init__(x, y, width, height, img, name, can_drag, can_move, can_fall)

		self.msg = msg
		self.text_box_x = 2
		self.text_box_y = 2
		self.text_box_width = 300
		self.text_box_height = 0

		_, self.text_rect = text_object(msg, black, 'small')
		self.msg = self._keep_splitting(msg)

		self.activated = False

	def _split_message(self, msg):
		_, text_rect = text_object(msg, black, 'small')
		if text_rect.width >= self.text_box_width:
			msg = msg[:-1]
			msg = self._split_message(msg)

		return msg

	def _keep_splitting(self, msg):
		list_of_msgs = list()
		part_of_msg = self._split_message(msg)
		next_part_of_msg = msg[len(part_of_msg):]

		part_of_msg, next_part_of_msg = self._space_in_message(part_of_msg, next_part_of_msg, msg)

		_, next_part_of_msg_rect = text_object(next_part_of_msg, black, 'small')

		list_of_msgs.append(part_of_msg)
		if next_part_of_msg_rect.width >= self.text_box_width:
			list_of_msgs += self._keep_splitting(next_part_of_msg)

		else:
			list_of_msgs.append(next_part_of_msg)

		return list_of_msgs

	def _space_in_message(self, part_of_msg, next_part_of_msg, msg):
		if part_of_msg[-1] != ' ':
			if next_part_of_msg != '':
				if next_part_of_msg[0] != ' ':
					part_of_msg = part_of_msg[:-1]
					next_part_of_msg = msg[len(part_of_msg):]
					if part_of_msg != '':
						part_of_msg, next_part_of_msg = self._space_in_message(part_of_msg, next_part_of_msg, msg)
				else:
					next_part_of_msg = next_part_of_msg[1:]
		return part_of_msg, next_part_of_msg

	def sign_output(self):
		pygame.draw.rect(Display, black, [self.text_box_x - 1, self.text_box_y - 1,
		                                  self.text_box_width + 2, self.text_box_height + 2])
		pygame.draw.rect(Display, grey, [self.text_box_x, self.text_box_y,
		                                 self.text_box_width, self.text_box_height])
		self._display_message()

	def _display_message(self):

		y_value_of_msg = 0

		for msg in self.msg:
			message_to_screen(msg, white,
			                  x_displace=self.text_box_x + 1,
			                  y_displace=self.text_box_y + 1 + y_value_of_msg,
			                  side='custom_top_left')

			y_value_of_msg += self.text_rect.height

		if y_value_of_msg > self.text_box_height:
			self.text_box_height = y_value_of_msg
			self.sign_output()


class ScreenShift:
	def __init__(self):
		self._amount = [0, 0]

		self.collisions = False
		self.error = False

	@property
	def add_amount(self):
		return self._amount

	@add_amount.setter
	def add_amount(self, value):
		self._amount = [self.x + value[0], self.y + value[1]]

	@property
	def hard_reset(self):
		return self._amount

	@hard_reset.setter
	def hard_reset(self, value):
		self._amount = value

	@property
	def x(self):
		return self.amount[0]

	@x.setter
	def x(self, value):
		old_value = self.amount[0]
		self.amount[0] = value
		self.after_shift_change(old_value, 'x')

	@property
	def y(self):
		return self.amount[1]

	@y.setter
	def y(self, value):
		old_value = self.amount[1]
		self.amount[1] = value
		self.after_shift_change(old_value, 'y')

	@property
	def amount(self):
		return self._amount

	@amount.setter
	def amount(self, value):
		old_value = self.amount
		self._amount = value
		self.after_shift_change(old_value, 'both')

	@staticmethod
	def check_collide(character):
		for tile in walls + doors[0] + no_move_zone + enemies:
			if type(tile).__name__ != 'Mob':
				tile.update_rect()

			if tile.rect.colliderect(character.rect):
				return True
		return False

	@staticmethod
	def update_tiles():
		for tile in walls + doors[0] + no_move_zone + enemies:
			tile.update_rect()

	def after_shift_change(self, old_value, axis):
		if self.check_collide(player):
			try:
				if axis == 'x':
					self.amount[0] = old_value
				elif axis == 'y':
					self.amount[1] = old_value
				elif axis == 'both':
					self.amount = old_value
				else:
					print('Error in method after_shift_change in class ScreenShift')
					print('Invalid Axis')
			except RuntimeError:
				print('Error in method after_shift_change in class ScreenShift')
				print('Runtime Error')
				game_over(True)
				self.amount = starting_screen_shift
				self.error = True

			self.update_tiles()

		if self.check_collide(player.jump_detector):
			if player.velocity > 1 or player.velocity < 0:
				pygame.mixer.Sound.play(sounds['thump'])
			player.velocity = 0


class Button:
	def __init__(self, msg, msg_colour, colour,
	             x=0, y=0, width=50, height=50,
	             outline=3, highlight_outline=5, outline_colour=black, click_colour=None,
	             font_size='medium', shifting=False):
		self.msg = msg
		self.msg_colour = msg_colour
		self.font_size = font_size

		self.colour = colour
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.shifting = shifting

		self.outline = outline
		self.outline_colour = outline_colour
		self.high_line = highlight_outline
		if click_colour is None:
			click_colour = []
			for num in self.colour:
				num += 30
				if num > 255:
					num = 255
				click_colour.append(num)
			click_colour = tuple(click_colour)

		self.click_colour = click_colour

		self.highlight = False
		self.greyed_out = False
		self.output = None
		self.was_highlighted = False  # If it was highlighted in the previous frame, this is True

	def draw(self):
		if self.shifting:
			to_shift_x, to_shift_y = screen_shift.x, screen_shift.y
		else:
			to_shift_x = to_shift_y = 0

		outline, colour = self.set_button_settings()

		pygame.draw.rect(Display, self.outline_colour, [self.x - self.width / 2 + to_shift_x - outline,
		                                                self.y - self.height / 2 + to_shift_y - outline,
		                                                self.width + 2 * outline,
		                                                self.height + 2 * outline])

		pygame.draw.rect(Display, colour, [self.x - self.width / 2 + to_shift_x,
		                                   self.y - self.height / 2 + to_shift_y,
		                                   self.width,
		                                   self.height])

		message_to_screen(self.msg,
		                  self.msg_colour,
		                  x_displace=self.x + to_shift_x,
		                  y_displace=self.y + to_shift_y,
		                  size=self.font_size,
		                  side='custom_center')

	def set_button_settings(self):
		colour = self.colour

		if self.greyed_out:
			greyed_out_colour = []
			for num in self.colour:
				num -= 30
				if num < 0:
					num = 0
				greyed_out_colour.append(num)
			greyed_out_colour = tuple(greyed_out_colour)
			return self.outline, greyed_out_colour

		if (self.x - self.width / 2 <= pygame.mouse.get_pos()[0] <= self.x + self.width / 2
		    and self.y - self.height / 2 <= pygame.mouse.get_pos()[1] <= self.y + self.height / 2):
			self.highlight = True
			if button_pressed['mouse_1']:
				colour = self.click_colour
			elif True in button_states.mouse_1:
				self.output = self.msg

		else:
			self.highlight = False

		if self.highlight:
			outline = self.high_line
			if not self.was_highlighted:
				pygame.mixer.Sound.play(sounds['click'])
			self.was_highlighted = True

		else:
			outline = self.outline
			self.was_highlighted = False

		return outline, colour

	def __repr__(self):
		return self.msg


class MenuButton(Button):
	def __init__(self, msg, msg_colour, colour,
	             x=0, y=0, width=50, height=50,
	             outline=3, highlight_outline=5,
	             outline_colour=black, click_colour=None,
	             font_size='medium', shifting=False,
	             intended_tracker_pos=0):
		super().__init__(msg, msg_colour, colour,
		                 x=x, y=y, width=width, height=height,
		                 outline=outline, highlight_outline=highlight_outline,
		                 outline_colour=outline_colour, click_colour=click_colour,
		                 font_size=font_size, shifting=shifting)

		self.intended_tracker_pos = intended_tracker_pos

	def set_button_settings(self):
		global tracker_pos

		colour = self.colour

		if self.greyed_out:
			greyed_out_colour = []
			for num in self.colour:
				num -= 30
				if num < 0:
					num = 0
				greyed_out_colour.append(num)
			greyed_out_colour = tuple(greyed_out_colour)
			return self.outline, greyed_out_colour

		if is_mouse_visible:
			if (self.x - self.width / 2 <= pygame.mouse.get_pos()[0] <= self.x + self.width / 2
			    and self.y - self.height / 2 <= pygame.mouse.get_pos()[1] <= self.y + self.height / 2):
				self.highlight = True
				tracker_pos = self.intended_tracker_pos
				if button_pressed['mouse_1']:
					colour = self.click_colour
				elif True in button_states.mouse_1:
					self.output = self.msg

			else:
				self.highlight = False
		if self.intended_tracker_pos == tracker_pos:
			self.highlight = True
			if button_pressed['enter'] or button_pressed['space']:
				colour = self.click_colour
			elif button_states.enter[-1] or button_states.space[-1]:
				self.output = self.msg
		else:
			self.highlight = False
			colour = self.colour

		if self.highlight:
			outline = self.high_line
			if not self.was_highlighted:
				pygame.mixer.Sound.play(sounds['click'])
			self.was_highlighted = True

		else:
			outline = self.outline
			self.was_highlighted = False

		return outline, colour


class LevelSelectButton(Button):
	pass

	def draw(self):
		if self.shifting:
			to_shift_x, to_shift_y = screen_shift.x, screen_shift.y
		else:
			to_shift_x = to_shift_y = 0

		outline, colour, msg_colour = self.set_button_settings()

		pygame.draw.rect(Display, self.outline_colour, [self.x + to_shift_x - outline,
		                                                self.y + to_shift_y - outline,
		                                                self.width + 2 * outline,
		                                                self.height + 2 * outline])

		pygame.draw.rect(Display, colour, [self.x + to_shift_x,
		                                   self.y + to_shift_y,
		                                   self.width,
		                                   self.height])

		area, level = self.msg.split()
		level_num = level[1:]

		message_to_screen(level_num,
		                  msg_colour,
		                  x_displace=self.x + self.width / 2 + to_shift_x,
		                  y_displace=self.y + self.height / 2 + to_shift_y,
		                  size=self.font_size,
		                  side='custom_center')

	def set_button_settings(self):
		colour = self.colour

		if self.greyed_out:
			greyed_out_colour = []
			greyed_out_msg_colour = []
			for num in self.colour:
				num -= 30
				if num < 0:
					num = 0
				greyed_out_colour.append(num)
			greyed_out_colour = tuple(greyed_out_colour)
			for num in self.msg_colour:
				num -= 30
				if num < 0:
					num = 0
				greyed_out_msg_colour.append(num)
			greyed_out_msg_colour = tuple(greyed_out_msg_colour)

			return self.outline, greyed_out_colour, greyed_out_msg_colour

		if (self.x <= pygame.mouse.get_pos()[0] <= self.x + self.width
		    and self.y <= pygame.mouse.get_pos()[1] <= self.y + self.height):
			self.highlight = True
			if button_pressed['mouse_1']:
				colour = self.click_colour
			elif True in button_states.mouse_1:
				self.output = self.msg

		else:
			self.highlight = False

		if self.highlight:
			outline = self.high_line
			if not self.was_highlighted:
				pygame.mixer.Sound.play(sounds['click'])
			self.was_highlighted = True

		else:
			outline = self.outline
			self.was_highlighted = False

		return outline, colour, self.msg_colour


def text_object(text, colour, size):
	if size == 'small':
		text_surface = small_font.render(text, True, colour)
	elif size == 'medium':
		text_surface = med_font.render(text, True, colour)
	elif size == 'large':
		text_surface = large_font.render(text, True, colour)
	else:
		raise Exception('Incorrect size in def of text_object()')
	return text_surface, text_surface.get_rect()


def message_to_screen(msg,
                      colour,
                      y_displace=0,
                      x_displace=0,
                      size='small',
                      side='center'
                      ):
	"""
	Each 'side' differs in their starting positions,
	point of the text box being controlled and
	in the direction of the displacements

	The name od the 'side' indicates the starting position as well as
	the point of the text box being controlled

	Center: Pygame directions
	Top: Pygame directions
	Bottom Left: Negative y
	Bottom Right: Negative y and Negative x
	:param msg:
	:param colour:
	:param y_displace:
	:param x_displace:
	:param size:
	:param side:
	:return:
	"""
	text_surf, text_rect = text_object(msg, colour, size)
	if side == 'center':
		text_rect.center = (display_width / 2) + x_displace, \
		                   (display_height / 2) + y_displace
	elif side == 'top':
		text_rect.midtop = (display_width / 2) + x_displace, y_displace
	elif side == 'bottom_left':
		text_rect.bottomleft = (x_displace,
		                        display_height - y_displace)
	elif side == 'bottom_right':
		text_rect.bottomright = (display_width - x_displace,
		                         display_height - y_displace)
	elif side == 'custom_center':
		text_rect.center = x_displace, y_displace
	elif side == 'custom_top':
		text_rect.midtop = x_displace, y_displace
	elif side == 'custom_top_left':
		text_rect.topleft = x_displace, y_displace
	elif side == 'custom_bottom':
		text_rect.midbottom = x_displace, y_displace
	elif side == 'custom_bot_left':
		text_rect.bottomleft = x_displace, y_displace
	elif side == 'custom_bot_right':
		text_rect.bottomright = x_displace, y_displace
	elif side == 'custom_mid_right':
		text_rect.midright = x_displace, y_displace
	elif side == 'custom_mid_left':
		text_rect.midleft = x_displace, y_displace
	else:
		text_rect.center = (display_width / 2) + x_displace, \
		                   (display_height / 2) + y_displace
	Display.blit(text_surf, text_rect)

	return text_rect


def shifting_animation(dragged=False):
	"""
	The screen shifts slowly to the destination point.
	:param dragged:
	:return:
	"""
	done = False
	difference = player.x - player.original_x, player.y - player.original_y

	subdivision = 600  # The number of steps for the screen to move
	max_diff = max(abs(difference[0]), abs(difference[1]))

	# The distance between the increments for the screen to move
	to_move_x_original = difference[0] / subdivision
	to_move_y_original = difference[1] / subdivision

	# The distance actually moved by the screen at each step
	to_move_x = to_move_x_original
	to_move_y = to_move_y_original
	old_screen_shift = screen_shift.amount[:]

	old_player_difference = None

	while (not done) and (max_diff > 0.1):

		# Screen shifts the amount equal to to_move
		screen_shift.amount = [screen_shift.x - to_move_x, screen_shift.y - to_move_y]
		player.x -= to_move_x
		player.y -= to_move_y

		# This is added to the distance between the increments so that the screen speeds up
		# during its shift
		to_move_x += to_move_x_original
		to_move_y += to_move_y_original

		player_difference = abs(player.original_x - player.x) + abs(player.original_y - player.y)

		if old_player_difference is not None:
			if old_player_difference < player_difference:
				done = True

		old_player_difference = player_difference
		if not dragged:
			x, y = player.x, player.y
			player.x, player.y = player.original_x, player.original_y
			draw_scene()
			player.x, player.y = x, y
		else:
			draw_scene()

		pygame.display.update()
		clock.tick(120)
	player.x = player.original_x
	player.y = player.original_y
	screen_shift.amount = [old_screen_shift[0] - difference[0], old_screen_shift[1] - difference[1]]

	player.last_eligible_pos = [player.x, player.y]
	if screen_shift.error:
		screen_shift.amount = starting_screen_shift
		screen_shift.error = False


def is_block_in_between(blocks, detector, first_point, last_point):
	"""
	Checks to see if a line of detectors from one of the points to the other collides
	with a wall
	:param blocks: the blocks that are checked to see if they are in between
	:param detector: detector used to check collision with block
	:param first_point: first point detector starts from
	:param last_point: last point detector ends at
	:return:
	"""

	# first_point_2 = first_point_1[0] + detector.width, first_point_1[1] + detector.height
	# last_point_2 = last_point_1[0] + detector.width, last_point_1[1] + detector.height

	close_to_0 = 0.00001  # A value close to 0 to make sure that divisors
	#  are not close to 0 to prevent dividing by zero

	if abs(last_point[0] - first_point[0]) > close_to_0:

		# Calculates the gradient
		gradient = (last_point[1] - first_point[1]) / (last_point[0] - first_point[0])
	else:
		gradient = 9999  # An arbitrary large value for the gradient

	c = last_point[1] - gradient * last_point[0]

	# Makes sure that the axis with the largest difference is used to
	# reduce the number of gaps between the detectors
	if abs(last_point[0] - first_point[0]) > abs(last_point[1] - first_point[1]):
		z1 = first_point[0]
		z2 = last_point[0]

		used_axis = 'x'
	else:
		z1 = first_point[1]
		z2 = last_point[1]

		used_axis = 'y'

	# stride is how many pixels being skipped when generating collision detectors
	stride = 20
	if z1 > z2:
		stride = -stride

	for z in range(int(z1), int(z2) + 1, stride):
		if used_axis == 'x':
			x = z
			y = gradient * x + c
		else:
			y = z
			if abs(gradient) > close_to_0:
				x = (y - c) / gradient
			else:
				x = last_point[0]

		detector.x = x
		detector.y = y

		# Uncomment this to see the collision detectors
		# detector.draw()
		# pygame.display.update()

		if detector.rect.collidelist(blocks) != -1:
			return True

	return False


def character_dragging(character, original_mouse_pos):
	"""
	Activates when the character is clicked on

	Manages the dragging around of the character.

	Most of the commented out code was used to visualize the collision detectors.
	Uncomment the code to visualize them again
	:param character: The Character object being dragged
	:param original_mouse_pos: The mouse position when clicked on initially
	:return: If the character dragging occurred, it returns True
	"""

	if (character.x_with_shift <= original_mouse_pos[0] < character.x_with_shift + character.width
	    and character.y_with_shift <= original_mouse_pos[1] < character.y_with_shift + character.height
	    and button_pressed['mouse_1'] and (not drag_ability.being_used)
	    and drag_ability.recharge_time_left <= 0):

		if character.mask.get_at((int(original_mouse_pos[0] - character.x_with_shift),
		                          int(original_mouse_pos[1] - character.y_with_shift))):

			character.tint = None

			# This allows the enemy to be displayed over any other enemies it goes over
			if character in enemies:
				enemies.remove(character)
				enemies.append(character)

			enemies_except_current_character = enemies[:]
			if character in enemies_except_current_character:
				enemies_except_current_character.remove(character)

			# first_collision is the location where the character following the mouse enters a wall
			first_collision = None

			# last_collision is the location where the character following the mouse leaves the wall
			last_collision = None

			character.original_x = character.x
			character.original_y = character.y

			original_x_with_shift = character.x_with_shift
			original_y_with_shift = character.y_with_shift

			furthest_distance = max((((display_width - character.x_with_shift) ** 2) +
			                         ((display_height - character.y_with_shift) ** 2)) ** 0.5,
			                        ((character.x_with_shift ** 2) +
			                         (character.y_with_shift ** 2)) ** 0.5)

			distance_from_start = 0

			while button_pressed['mouse_1']:
				character.ghost.visible = False
				receive_input()

				mouse_pos = pygame.mouse.get_pos()

				# Keeps track of the last position of the character
				last_x, last_y = character.x_with_shift, character.y_with_shift

				# Moves the character to the mouse
				character.follow(original_mouse_pos, mouse_pos)

				destination_x, destination_y = character.x_with_shift, character.y_with_shift

				if character.rect.collidelist(
												walls + doors[0] + no_drag_zone + no_move_zone + enemies_except_current_character) != -1:  # True if collided
					if not character.collision_detector.did_collide:
						# See initialization of first_collision above
						first_collision = character.x_with_shift, character.y_with_shift

					# did_collide keeps track of if the character collided with a wall yet
					character.collision_detector.did_collide = True
					# character.collision_detector.x = character.x
					# character.collision_detector.y = character.y
					# character.collision_detector.draw()

					if is_block_in_between(no_move_zone + enemies_except_current_character,
					                       character.collision_detector,
					                       (character.x_with_shift, character.y_with_shift), (last_x, last_y)):
						character.ghost.x, character.ghost.y = character.x_with_shift, character.y_with_shift
						character.ghost.visible = True

					character.x_with_shift = last_x
					character.y_with_shift = last_y
				elif character.collision_detector.did_collide:
					# This elif statement occurs when the character stops colliding with a
					# wall and after it has already touched one

					character.collision_detector.did_collide = False

					# See initialization of last_collision above
					last_collision = character.x_with_shift, character.y_with_shift
				# character.collision_detector.x, character.collision_detector.y = last_collision
				# character.collision_detector.draw()
				# if first_collision is not None:
				# 	character.collision_detector.x, character.collision_detector.y = first_collision
				# 	# character.collision_detector.draw()
				# character.draw()
				if (first_collision and last_collision) is not None:
					if is_block_in_between(walls + doors[0] + no_drag_zone, character.collision_detector, first_collision,
					                       last_collision):
						character.x_with_shift, character.y_with_shift = last_x, last_y
						character.last_eligible_pos = [last_x, last_y]

					first_collision = last_collision = None
				if character.last_eligible_pos is not None:
					if is_block_in_between(walls + doors[0] + no_drag_zone, character.collision_detector,
					                       (character.x_with_shift, character.y_with_shift),
					                       character.last_eligible_pos):
						character.x_with_shift = character.last_eligible_pos[0]
						character.y_with_shift = character.last_eligible_pos[1]
					else:
						character.last_eligible_pos[0] = character.x_with_shift
						character.last_eligible_pos[1] = character.y_with_shift

				if (character.x_with_shift, character.y_with_shift) != (destination_x, destination_y):

					make_change_x = False
					make_change_y = False

					if destination_x - character.x_with_shift < 0:
						to_move_x = -1
					elif destination_x - character.x_with_shift > 0:
						to_move_x = 1
					else:
						to_move_x = 0

					character.collision_detector.x, character.collision_detector.y = character.x_with_shift, character.y_with_shift

					character.collision_detector.x += to_move_x

					if character.collision_detector.rect.collidelist(
													walls + doors[0] + no_drag_zone + no_move_zone + enemies_except_current_character) == -1:
						make_change_x = True
					# character.x = character.collision_detector.x

					# character.collision_detector.draw()

					if destination_y - character.y_with_shift < 0:
						to_move_y = -1
					elif destination_y - character.y_with_shift > 0:
						to_move_y = 1
					else:
						to_move_y = 0

					character.collision_detector.x, character.collision_detector.y = character.x_with_shift, character.y_with_shift

					character.collision_detector.y += to_move_y

					if character.collision_detector.rect.collidelist(
													walls + doors[0] + no_drag_zone + no_move_zone + enemies_except_current_character) == -1:
						make_change_y = True
					# character.y_with_shift = character.collision_detector.y
					if make_change_x:
						character.x_with_shift += to_move_x
					if make_change_y:
						character.y_with_shift += to_move_y

					if character.last_eligible_pos is not None:
						character.last_eligible_pos = [character.x_with_shift, character.y_with_shift]

					# character.collision_detector.x, character.collision_detector.y = character.x, character.y
					# print(to_move_x, to_move_y)
					# character.collision_detector.draw()
					# pygame.display.update()

				draw_scene()

				distance_from_start = (((original_x_with_shift - character.x_with_shift) ** 2) +
				                       ((original_y_with_shift - character.y_with_shift) ** 2)) ** 0.5

				pygame.display.update()
				clock.tick(120)

			character.ghost.visible = False

			drag_ability.time_to_be_added = (distance_from_start / furthest_distance) * (
				2 - drag_ability.recharge_from_empty)

			if character == player:
				shifting_animation(dragged=True)

			drag_ability.recharge_time_left = drag_ability.recharge_from_empty + drag_ability.time_to_be_added

			if drag_bar.total_time_to_recharge is None:
				drag_bar.total_time_to_recharge = drag_ability.recharge_time_left

	elif (character.x_with_shift <= original_mouse_pos[0] < character.x_with_shift + character.width
	      and character.y_with_shift <= original_mouse_pos[1] < character.y_with_shift + character.height
	      and (not drag_ability.being_used)):

		if character.mask.get_at((int(original_mouse_pos[0] - character.x_with_shift),
		                          int(original_mouse_pos[1] - character.y_with_shift))):
			if drag_ability.recharge_time_left <= 0:
				character.tint = green
			else:
				character.tint = red
	else:
		character.tint = None


def falling(to_fall=None):
	"""
	Manages gravity and the jumping mechanic
	:param to_fall: the screen is shifted by amount to_fall which is defined in the function if
	if it is None. If the screen is shifted too much so that it collides with a block,
	the screen_shift value will not change so then to_fall is adjusted slightly and then the
	function is run again but with a different to_fall value
	:return:
	"""
	t = 0.1  # t is time
	a = 9.81  # a is acceleration

	terminal_velocity = jump_velocity * -2

	if button_pressed['space']:
		# player.jump_detector.update_rect(player)
		if player.jump_detector.can_jump(walls + doors[0] + no_move_zone + enemies):
			pygame.mixer.Sound.play(sounds['jump'])
			player.velocity = jump_velocity
			if button_pressed['shift']:
				player.velocity = jump_velocity / 2 - 2

	# Falling
	if player.velocity is not None:
		if to_fall is None:
			to_fall = player.velocity * t + 0.5 * a * (t ** 2)  # Kinematic equations of motion
		player.velocity += a * t
		if player.velocity > terminal_velocity:
			player.velocity = terminal_velocity
		old_screen_shift_y = screen_shift.y  # Keeps track of the value to compare later
		screen_shift.y -= to_fall

		if (screen_shift.y == old_screen_shift_y) and abs(to_fall) > 0.05:  # Base case: to_fall is around 0
			if to_fall < 0:
				adjust = -1
			elif to_fall > 0:
				adjust = 1
			else:
				adjust = 0

			try:
				falling(to_fall=to_fall - adjust)
			except RecursionError:
				pass


def walking(to_move=None):
	"""
	Left and Right movement
	:param to_move: the screen is shifted by amount to_move which is defined in the function if
	if it is None. If the screen is shifted too much so that it collides with a block,
	the screen_shift value will not change so then to_move is adjusted slightly and then the
	function is run again but with a different to_move value
	:return:
	"""
	# Left and Right movement
	# to_move keeps track of exactly how much to shift the screen before it is actually shifted

	old_screen_shift_x = screen_shift.x

	if to_move is None:
		to_move = 0
		if button_pressed['d']:
			to_move = -3
			if button_pressed['shift']:
				to_move += 2
		if button_pressed['a']:
			to_move = 3
			if button_pressed['shift']:
				to_move -= 2

	screen_shift.x += to_move

	if (screen_shift.x == old_screen_shift_x) and abs(to_move) > 0.05:  # Base case: to_move is around 0
		if to_move < 0:
			adjust = -1
		elif to_move > 0:
			adjust = 1
		else:
			adjust = 0
		walking(to_move=to_move - adjust)

	enemy_index = player.rect.collidelist(enemies)
	if enemy_index != -1:
		if enemies[enemy_index].mask.overlap(player.mask,
		                                     (int(player.x_with_shift - enemies[enemy_index].x_with_shift),
		                                      int(player.y_with_shift - enemies[
			                                      enemy_index].y_with_shift))) is not None:
			if type(enemies[enemy_index]).__name__ != 'Boulder':
				game_over()
			elif enemies[enemy_index].velocity != 0:
				pygame.mixer.Sound.play(sounds['boulder crush'])
				game_over()


def player_movement():
	"""
	Manages the movement of the player
	:return:
	"""
	global button_pressed
	global screen_shift
	global player

	mouse_pos = pygame.mouse.get_pos()

	walking()

	falling()

	character_dragging(player, mouse_pos)

	drag_bar.current_recharge_time = drag_ability.recharge_time_left
	# if drag_ability.recharge_time_left:
	# print(drag_ability.recharge_time_left)
	# print(clock.get_time())
	if drag_ability.recharge_time_left > 0:
		drag_ability.recharge_time_left -= clock.get_time() * 0.001
	else:
		drag_ability.recharge_time_left = 0
		drag_bar.total_time_to_recharge = None

	for sign in signs:
		sign.update_rect()
		if player.rect.colliderect(sign.rect):
			if button_pressed['w'] or button_pressed['up']:
				sign.activated = True
		else:
			sign.activated = False


def draw_scene():
	"""
	This is where everything is drawn to the screen
	:return:
	"""
	Display.fill(off_white)
	for tile in sensors + walls + doors[0] + no_drag_zone + no_move_zone + goals + doors[1]:
		if hasattr(tile, 'ghost'):
			tile.ghost.draw()

		tile.draw()

	for sign in signs:
		sign.draw()

	for enemy in enemies:
		enemy.ghost.draw()
		enemy.draw()

	player.ghost.draw()
	player.draw()

	drag_bar.draw()

	for sign in signs:
		if sign.activated:
			sign.sign_output()


def level_select():
	"""
	Manages the logic and draws the Level Select Screen
	:return:
	"""
	global level_select_buttons
	global list_of_levels_left
	done = False

	completed_levels = list()  # List of levels that have been completed

	with open('Saved Data.txt', 'r') as save_file:
		for line in save_file:
			line = line.rstrip('\n')
			completed_levels.append(line)

	with open('Levels.txt', 'r') as levels_file:
		line = levels_file.readline()
		if completed_levels:
			while line.rstrip('\n') != completed_levels[-1]:
				line = levels_file.readline()
			while line != '':
				line = levels_file.readline()
				line = line.rstrip('\n')
			line = levels_file.readline().rstrip('\n')
			unlocked_levels = completed_levels[:]
			if line != '':
				unlocked_levels.append(line)  # List of levels that can be played
		else:
			unlocked_levels = list()
			unlocked_levels.append('A1 L1')

	# Without this variable, when holding mouse_1 before pressing pause and releasing it after,
	# if one of the buttons is highlighted, and then mouse_1 is released, it will select it
	mouse_1_clicked_before_level_select = button_states.mouse_1[-1]

	button_width = 100
	button_horizontal_separation = button_width + 50
	button_height = 100
	button_vertical_separation = button_height - 50

	star_height = 30

	a, l = current_level.split()

	area_num = int(a[1:])

	msg_rect = message_to_screen('Area ' + str(area_num), black,
	                             y_displace=0, x_displace=0,
	                             size='large', side='top')

	lvl_select_top = pygame.draw.rect(Display, black,
	                                  [0, msg_rect.bottom,
	                                   display_width, 5]).bottom

	lvl_select_side_width = 50

	level_select_buttons = new_level_select_buttons(area_num,
	                                                lvl_select_top,
	                                                lvl_select_side_width,
	                                                button_horizontal_separation,
	                                                button_vertical_separation,
	                                                button_width,
	                                                button_height)

	select_diff_area_buttons = (
		Button('<', black, [i - 10 for i in off_white], x=20, y=(display_height + lvl_select_top) / 2,
		       width=40, height=display_height - lvl_select_top,
		       outline=0, highlight_outline=1),
		Button('>', black, [i - 10 for i in off_white], x=display_width - 20,
		       y=(display_height + lvl_select_top) / 2,
		       width=40, height=display_height - lvl_select_top,
		       outline=0, highlight_outline=1)
	)

	while not done:
		done = receive_input('level_select')

		Display.fill(off_white)
		msg_rect = message_to_screen('Area ' + str(area_num), black,
		                             y_displace=0, x_displace=0,
		                             size='large', side='top')

		pygame.draw.rect(Display, black,
		                 [0, msg_rect.bottom,
		                  display_width, 5])

		for button in level_select_buttons:
			if button.msg not in unlocked_levels:
				button.greyed_out = True
			else:
				button.greyed_out = False

			button.draw()

			star_box = (button.x, button.y)

			if button.msg in completed_levels:
				star = images['star']
			elif button.msg not in unlocked_levels:
				star = images['lock']
			else:
				star = images['grey star']

			star = pygame.transform.scale(star,
			                              (star_height, star_height))
			Display.blit(star, star_box)

			if (not mouse_1_clicked_before_level_select) and (not button.greyed_out):
				if button.output is not None:
					for lvl_index in range(len(list_of_levels)):
						if list_of_levels[lvl_index] == button.output:
							list_of_levels_left = list_of_levels[lvl_index:]
							generate_map_from_file(list_of_levels_left)
							done = True
							break

			button.output = None

		if not button_states.mouse_1[-1]:
			mouse_1_clicked_before_level_select = False

		for arrow_button in select_diff_area_buttons:

			if arrow_button.msg == '<':
				area_pointing_to = area_num - 1
				if area_pointing_to in all_area_numbers:
					arrow_button.draw()
			elif arrow_button.msg == '>':
				area_pointing_to = area_num + 1
				if area_pointing_to in all_area_numbers:
					arrow_button.draw()

			if (not button_states.mouse_1[0]) and button_states.mouse_1[1]:
				if arrow_button.output == '<':
					area_num -= 1
				elif arrow_button.output == '>':
					area_num += 1

				# Make an animation. Later
				level_select_buttons = new_level_select_buttons(area_num,
				                                                lvl_select_top,
				                                                lvl_select_side_width,
				                                                button_horizontal_separation,
				                                                button_vertical_separation,
				                                                button_width,
				                                                button_height)
			arrow_button.output = None

		pygame.display.update()
		clock.tick(60)


def new_level_select_buttons(area_num,
                             lvl_select_top,
                             lvl_select_side_width,
                             button_horizontal_separation,
                             button_vertical_separation,
                             button_width,
                             button_height):
	buttons_list = list()

	for level_name in list_of_levels:
		area, level = level_name.split()

		if area[1:] == str(area_num):
			x = (int(level[1:]) - 1) * button_horizontal_separation + lvl_select_side_width
			if x + button_width > display_width - lvl_select_side_width:
				y = lvl_select_top + 2 * button_vertical_separation + button_height
				x -= display_width - 2 * lvl_select_side_width
			else:
				y = lvl_select_top + button_vertical_separation

			buttons_list.append(
				LevelSelectButton(level_name, white, grey,
				                  x=x,
				                  y=y,
				                  width=button_width, height=button_height))

	return buttons_list


def level_complete(goal):
	global current_level
	global completion_buttons

	done = False

	drag_bar.completion = 1

	player.x, player.y = [(goal.x + screen_shift.x) - player.width / 2 + goal.width / 2,
	                      (goal.y + screen_shift.y) + (- player.height + goal.height)]

	shifting_animation(dragged=False)
	button_width = 250
	button_separation = 300

	to_save = current_level + '\n'

	with open('Saved Data.txt', 'r') as read_save:
		for line in read_save:
			if to_save == line:
				to_save = ''

	with open('Saved Data.txt', 'a') as save_file:
		save_file.write(to_save)

	n = Display.convert_alpha()
	n.fill((*grey, 100))

	pygame.mixer.music.load(music['level complete'])
	pygame.mixer.music.play()

	while not done:
		done = receive_input('level_complete')

		draw_scene()

		Display.blit(n, (0, 0))

		if not completion_buttons:
			completion_buttons = [Button('Replay Level', black, green,
			                             x=display_width / 2 - button_separation, y=display_height / 2,
			                             width=button_width, height=50),
			                      Button('Level Select', black, green,
			                             x=display_width / 2, y=display_height / 2,
			                             width=button_width, height=50),
			                      Button('Next Level', black, green,
			                             x=display_width / 2 + button_separation, y=display_height / 2,
			                             width=button_width, height=50),
			                      ]

		for button in completion_buttons:

			if (not list_of_levels_left) and button.msg == 'Next Level':
				button.greyed_out = True
			elif list_of_levels_left and button.msg == 'Next Level':
				button.greyed_out = False
			button.draw()
			if button.output == 'Next Level':
				pygame.mixer.music.stop()
				done = True
				if list_of_levels_left:
					generate_map_from_file(list_of_levels_left)
					drag_ability.recharge_time_left = 0
			elif button.output == 'Replay Level':
				pygame.mixer.music.stop()
				done = True
				generate_map_from_file(current_level)
			elif button.output == 'Level Select':
				pygame.mixer.music.stop()
				print('Test')
				done = True

				current_index = list_of_levels.index(current_level) + 1

				if current_index < len(list_of_levels):
					current_level = list_of_levels[current_index]

				button.output = None

				level_select()
				break

			button.output = None

		pygame.display.update()
		clock.tick(120)


def mob_killing(character):
	if type(character).__name__ == 'Boulder':
		if character.jump_detector.velocity != 0:
			character.jump_detector.can_jump(walls + doors[0] + no_move_zone)
			enemies_except_current_character = enemies[:]
			if character in enemies_except_current_character:
				enemies_except_current_character.remove(character)

			death_index = character.jump_detector.rect.collidelist(enemies_except_current_character)
			if death_index != -1:
				pygame.mixer.Sound.play(sounds['boulder crush'])
				enemies.remove(enemies_except_current_character[death_index])


def mob_falling(character, to_fall=None):
	"""
	Manages gravity and the jumping mechanic
	:param character: The character that the gravity is being applied to
	:param to_fall: the screen is shifted by amount to_fall which is defined in the function if
	if it is None. If the screen is shifted too much so that it collides with a block,
	the screen_shift value will not change so then to_fall is adjusted slightly and then the
	function is run again but with a different to_fall value
	:return:
	"""
	t = 0.1  # t is time
	a = 9.81  # a is acceleration

	terminal_velocity = jump_velocity * -2

	enemies_except_current_character = enemies[:]
	if character in enemies_except_current_character:
		enemies_except_current_character.remove(character)

	# Falling
	if character.velocity is not None:
		if to_fall is None:
			to_fall = character.velocity * t + 0.5 * a * (t ** 2)  # Kinematic equations of motion
		character.velocity += a * t
		if character.velocity > terminal_velocity:
			character.velocity = terminal_velocity
		character.y_with_shift += to_fall
		if character.jump_detector.can_jump(walls + doors[0] + no_move_zone + enemies_except_current_character):
			character.y = (walls
			               + doors[0]
			               + no_move_zone
			               + enemies_except_current_character
			               )[
				              character.jump_detector.rect.collidelist(walls
				                                                       + doors[0]
				                                                       + no_move_zone
				                                                       + enemies_except_current_character
				                                                       )
			              ].y - character.height

			character.velocity = 0


def mob_walking(character):
	if character.name == 'Guard':
		character.x += character.to_move
		enemies_except_current_character = enemies[:]
		if character in enemies_except_current_character:
			enemies_except_current_character.remove(character)
		if ((character.rect.collidelist(walls + doors[0] + no_move_zone + enemies_except_current_character) != -1)
		    or character.jump_detector.might_fall(walls + doors[0] + no_move_zone + enemies_except_current_character)):
			character.x -= character.to_move
			character.to_move = -character.to_move

		if character.to_move < 0:
			character.facing = 'left'
		else:
			character.facing = 'right'


def mob_movement():
	for entity in enemies + goals:
		if type(entity).__name__ != 'Block':
			entity.jump_detector.velocity = entity.velocity  # This is to test the boulder's velocity for enemy deaths
			if entity.can_fall:
				mob_falling(entity)
			if entity.can_drag:
				character_dragging(entity, pygame.mouse.get_pos())
			if entity.can_move:
				mob_walking(entity)
			mob_killing(entity)


def game_loop():
	"""
	The main loop of the game
	:return:
	"""
	global game_exit
	global button_pressed

	game_exit = False

	while not game_exit:
		receive_input()

		player_movement()

		mob_movement()

		door_status()

		draw_scene()

		goal_number = player.rect.collidelist(goals)

		for goal in goals:
			if goal.tint is not None:
				goal.tint = None

		if goal_number != -1:
			if button_pressed['w'] and player.jump_detector.can_jump(walls + doors[0]):
				if goals[goal_number].rect.collidelist(enemies) == -1:
					if type(goals[goal_number]).__name__ not in {'Block', 'Mob'}:
						continue
					elif type(goals[goal_number]).__name__ == 'Mob':
						if goals[goal_number].velocity != 0:
							continue
					if type(goals[goal_number]).__name__ == 'Mob':
						level_complete(goals[goal_number])
					else:
						if not goals[goal_number].final:
							level_complete(goals[goal_number])
						else:
							game_complete()
				else:
					goals[goal_number].tint = red

		pygame.display.update()
		clock.tick(120)

	pygame.quit()
	quit()


def door_status():
	global doors
	sensed = False
	for sensor in sensors:
		for character in enemies + goals + [player]:
			if type(character).__name__ != 'Block':
				sensor.update_rect()
				character.update_rect()
				if sensor.rect.colliderect(character.rect):
					if doors[0]:
						doors[1] = doors[0][:]
						for door in doors[1]:
							door.texture = light_grey
					doors[0] = []
					sensed = True
					break
	if not sensed:
		if doors[1]:
			doors[0] = doors[1][:]
			for entity in enemies + goals:
				entity.update_rect()
			player.update_rect()
			for door in doors[0]:
				door.texture = grey
				door.update_rect()
				if door.rect.colliderect(player.rect):
					game_over()
				# for entity in enemies:
				# 	if door.rect.colliderect(entity.rect):
				# 			enemies.remove(entity)
				# for entity in goals:
				# 	if type(entity).__name__ != 'Block':
				# 		if door.rect.colliderect(entity.rect):
				# 			goals.remove(entity)


def paused():
	global paused_buttons
	global is_mouse_visible
	global tracker_pos
	global game_exit

	done = False
	tracker_pos = None

	pygame.mixer.music.pause()

	# Without this variable, when holding space before pressing pause and releasing it after,
	# if one of the buttons is highlighted, and then space is released, it will select it
	space_pressed_before_pause = button_pressed['space']

	n = Display.convert_alpha()
	n.fill((*grey, 230))

	while (not done) and (not game_exit):
		done = receive_input('paused')

		if pygame.mouse.get_rel() != (0, 0):
			pygame.mouse.set_visible(True)
			is_mouse_visible = True

		elif ((button_pressed['up'] or button_pressed['down'])
		      or (button_pressed['w'] or button_pressed['s'])):
			pygame.mouse.set_visible(False)
			is_mouse_visible = False

		if ((button_states.up[0] and not button_states.up[1])
		    or (button_states.w[0] and not button_states.w[1])):
			if tracker_pos is not None:
				tracker_pos -= 1
			else:
				tracker_pos = 0
		if ((button_states.down[0] and not button_states.down[1])
		    or (button_states.s[0] and not button_states.s[1])):
			if tracker_pos is not None:
				tracker_pos += 1
			else:
				tracker_pos = 0

		if tracker_pos is not None:
			if len(paused_buttons) <= tracker_pos:
				tracker_pos = 0
			if tracker_pos < 0:
				tracker_pos = len(paused_buttons) - 1

		draw_scene()
		Display.blit(n, (0, 0))

		message_to_screen('PAUSED', black, y_displace=20, size='large', side='top')

		button_vertical_separation = 100

		if not paused_buttons:
			paused_buttons = [MenuButton('Resume Game', black, red,
			                             x=display_width / 2, y=0 * button_vertical_separation + 175,
			                             width=350, height=50,
			                             intended_tracker_pos=0),
			                  MenuButton('Restart Level', black, red,
			                             x=display_width / 2, y=1 * button_vertical_separation + 175,
			                             width=350, height=50,
			                             intended_tracker_pos=1),
			                  MenuButton('Level Select', black, red,
			                             x=display_width / 2, y=2 * button_vertical_separation + 175,
			                             width=350, height=50,
			                             intended_tracker_pos=2),
			                  MenuButton('Quit Game', black, red,
			                             x=display_width / 2, y=3 * button_vertical_separation + 175,
			                             width=350, height=50,
			                             intended_tracker_pos=3)
			                  ]

		for button in paused_buttons:
			button.draw()

			if not space_pressed_before_pause:
				pygame.mixer.music.unpause()
				if button.output == 'Resume Game':
					done = True
				elif button.output == 'Restart Level':
					generate_map_from_file(current_level)
					done = True
				# elif button.output == 'Toggle Fullscreen':
				# 	if Display.get_flags() & pygame.FULLSCREEN:
				# 		pygame.display.set_mode(resolution)
				# 	else:
				# 		pygame.display.set_mode(resolution, pygame.FULLSCREEN)
				elif button.output == 'Level Select':
					level_select()
					done = True
				elif button.output == 'Quit Game':
					pygame.quit()
					quit()
				pygame.mixer.music.pause()

			button.output = None

		if not button_states.space[-1]:
			space_pressed_before_pause = False

		pygame.display.update()
		clock.tick(60)

	pygame.mixer.music.unpause()


def receive_input(menu=None):
	"""
	Keeps track of the buttons pressed by modifying the button_pressed dictionary
	:param menu:
	:return:
	"""
	global game_exit
	global Display
	global is_mouse_visible

	done = False

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			game_exit = True
			done = True
			pygame.quit()
			quit()

		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_w:
				button_pressed['w'] = True
			if event.key == pygame.K_a:
				button_pressed['a'] = True
			if event.key == pygame.K_s:
				button_pressed['s'] = True
			if event.key == pygame.K_d:
				button_pressed['d'] = True
			if event.key == pygame.K_UP:
				button_pressed['up'] = True
			if event.key == pygame.K_LEFT:
				button_pressed['left'] = True
			if event.key == pygame.K_DOWN:
				button_pressed['down'] = True
			if event.key == pygame.K_RIGHT:
				button_pressed['right'] = True
			if event.key == pygame.K_LSHIFT:
				button_pressed['shift'] = True
			if event.key == pygame.K_LCTRL:
				button_pressed['ctrl'] = True
			if event.key == pygame.K_SPACE:
				button_pressed['space'] = True
			if event.key == pygame.K_RETURN:
				button_pressed['enter'] = True
			if event.key == pygame.K_p:
				button_pressed['p'] = True
			if event.key == pygame.K_o:
				button_pressed['o'] = True
			if event.key == pygame.K_ESCAPE:
				if menu != ('paused' or 'level_select'):
					paused()
				else:
					done = True

		if event.type == pygame.KEYUP:
			if event.key == pygame.K_w:
				button_pressed['w'] = False
			if event.key == pygame.K_a:
				button_pressed['a'] = False
			if event.key == pygame.K_s:
				button_pressed['s'] = False
			if event.key == pygame.K_d:
				button_pressed['d'] = False
			if event.key == pygame.K_UP:
				button_pressed['up'] = False
			if event.key == pygame.K_LEFT:
				button_pressed['left'] = False
			if event.key == pygame.K_DOWN:
				button_pressed['down'] = False
			if event.key == pygame.K_RIGHT:
				button_pressed['right'] = False
			if event.key == pygame.K_LSHIFT:
				button_pressed['shift'] = False
			if event.key == pygame.K_LCTRL:
				button_pressed['ctrl'] = False
			if event.key == pygame.K_SPACE:
				button_pressed['space'] = False
			if event.key == pygame.K_RETURN:
				button_pressed['enter'] = False
			if event.key == pygame.K_p:
				button_pressed['p'] = False
			if event.key == pygame.K_o:
				button_pressed['o'] = False

		if event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:
				button_pressed['mouse_1'] = True
			if event.button == 3:
				button_pressed['mouse_2'] = True

		if event.type == pygame.MOUSEBUTTONUP:
			if event.button == 1:
				button_pressed['mouse_1'] = False
			if event.button == 3:
				button_pressed['mouse_2'] = False

	if menu is None:
		pygame.mouse.set_visible(True)
		is_mouse_visible = True

	button_states.update()

	return done


def game_over(error=False):
	global game_over_buttons
	global is_mouse_visible
	global tracker_pos
	global game_exit

	done = False
	tracker_pos = None

	# Without this variable, when holding space before dying and releasing it after,
	# if one of the buttons is highlighted, and then space is released, it will select it
	space_pressed_before_game_over = button_pressed['space']

	n = Display.convert_alpha()
	n.fill((*red, 130))

	pygame.mixer.music.load(music['game over'])
	pygame.mixer.music.play()

	while (not done) and (not game_exit):
		done = receive_input('game_over')

		if pygame.mouse.get_rel() != (0, 0):
			pygame.mouse.set_visible(True)
			is_mouse_visible = True

		elif ((button_pressed['up'] or button_pressed['down'])
		      or (button_pressed['w'] or button_pressed['s'])):
			pygame.mouse.set_visible(False)
			is_mouse_visible = False

		if ((button_states.up[0] and not button_states.up[1])
		    or (button_states.w[0] and not button_states.w[1])):
			if tracker_pos is not None:
				tracker_pos -= 1
			else:
				tracker_pos = 0
		if ((button_states.down[0] and not button_states.down[1])
		    or (button_states.s[0] and not button_states.s[1])):
			if tracker_pos is not None:
				tracker_pos += 1
			else:
				tracker_pos = 0

		if tracker_pos is not None:
			if len(game_over_buttons) <= tracker_pos:
				tracker_pos = 0
			if tracker_pos < 0:
				tracker_pos = len(game_over_buttons) - 1

		draw_scene()
		Display.blit(n, (0, 0))

		if not error:
			message_to_screen('GAME OVER', black, y_displace=20, size='large', side='top')
		else:
			message_to_screen('An Error Occurred', black, y_displace=20, size='medium', side='top')
			message_to_screen('Please Contact Your Local Developer Who isn\'t Local', black, y_displace=50,
			                  size='medium', side='top')

		button_vertical_separation = 100

		if not game_over_buttons:
			game_over_buttons = [MenuButton('Replay Level', black, red,
			                                x=display_width / 2, y=0 * button_vertical_separation + 200,
			                                width=350, height=50,
			                                intended_tracker_pos=0),
			                     MenuButton('Level Select', black, red,
			                                x=display_width / 2, y=1 * button_vertical_separation + 200,
			                                width=350, height=50,
			                                intended_tracker_pos=1),
			                     MenuButton('Quit Game', black, red,
			                                x=display_width / 2, y=2 * button_vertical_separation + 200,
			                                width=350, height=50,
			                                intended_tracker_pos=2)
			                     ]

		for button in game_over_buttons:
			button.draw()

			if not space_pressed_before_game_over:
				if button.output == 'Replay Level':
					pygame.mixer.music.stop()
					generate_map_from_file(current_level)
					done = True
				elif button.output == 'Level Select':
					pygame.mixer.music.stop()
					level_select()
					done = True
				elif button.output == 'Quit Game':
					pygame.quit()
					quit()

			button.output = None

		if not button_states.space[-1]:
			space_pressed_before_game_over = False

		pygame.display.update()
		clock.tick(60)


	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSWSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSWSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSWSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWPWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWSWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWSWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWSWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWSWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWSSSSSSSSSSSSSSSSSSSSSSSSSSSSSWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
	# WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW


def game_complete():
	global game_over_buttons
	global is_mouse_visible
	global tracker_pos
	global game_exit

	done = False

	pygame.mixer.music.load(music['level complete'])
	pygame.mixer.music.play()

	while (not done) and (not game_exit):
		done = receive_input('game_over')

		Display.fill(off_white)

		message_to_screen('CONGRATULATIONS!!!', black, y_displace=20, size='large', side='top')
		message_to_screen('YOU FOUND THE ONE TRUE BAGEL!!!!!', black, y_displace=400, size='medium', side='top')

		pygame.display.update()
		clock.tick(60)


def generate_map_from_file(levels_list):
	global starting_screen_shift
	global current_level
	global walls
	global no_drag_zone
	global no_move_zone
	global goals
	global enemies
	global signs
	global doors
	global sensors

	if not isinstance(levels_list, list):
		levels_list = [levels_list]

	walls = list()
	no_drag_zone = list()
	no_move_zone = list()
	goals = list()
	enemies = list()
	signs = list()
	doors = [[], []]  # Index 0: locked doors, Index 1: unlocked doors
	sensors = list()

	tile_width = 50

	board_values = []

	with open('Levels.txt', 'r') as levels:
		line = levels.readline()
		while line[:-1] != levels_list[0] and line != '':
			line = levels.readline()
		while line != '':
			line = levels.readline()
			line = line.rstrip('\n')
			board_values.append(line)

	board_values = board_values[:-1]

	for data in board_values[1:]:
		try:
			block_args = [int(float(num) * tile_width) for num in data[1:].split(',')]
		except ValueError:
			split_data = data.split(',')
			for i in range(len(split_data[0])):
				if split_data[0][i].isdigit():
					block_args = [int(float(num) * tile_width) for num in data[i:].split(',')]
					break
			else:
				if data[0] == 's':
					split_data = data.split('\\')
					for i in range(len(split_data[1])):
						if split_data[1][i].isdigit():
							block_args = [int(float(num) * tile_width) for num in
							              data[len(split_data[0]) + i + 1:].split(',')]
							break
				else:
					raise Exception('Invalid Line in Levels')

		if data[0] == 'w':
			walls.append(Block(*block_args, brown))
		elif data[0] == 'm':
			no_drag_zone.append(Block(*block_args, purple))
		elif data[0] == 'd':
			no_move_zone.append(Block(*block_args, blue))
		elif data[0] == 's':
			split_data = data[1:].split('\\')
			signs.append(Sign(split_data[0], *block_args, tile_width, tile_width))
		elif data[0] == 'g':
			if data[1] == 's':
				goals.append(Block(*block_args, tile_width, tile_width, images['stationary goal']))
			elif data[1] == 'p':
				goals.append(Mob(*block_args, tile_width, tile_width, images['portable goal'],
				                 name='Portable Goal'))
			elif data[1] == 'f':
				goals.append(Block(*block_args, tile_width, tile_width, images['final goal']))
				goals[-1].final = True
		elif data[0] == 'b':
			if data[1] == 'b':
				doors[0].append(Block(*block_args, grey))
			elif data[1] == 's':
				sensors.append(Block(*block_args, tile_width, tile_width, images['sensor']))
		elif data[0] == 'e':
			if data[1] == 'b':
				enemies.append(Boulder(*block_args, can_move=False,
				                       name='Boulder', img=images['boulder']))
			elif data[1] == 's':
				enemies.append(Mob(*block_args, can_move=False, can_fall=False, can_drag=False,
				                   name='Spikes', img=images['spikes']))
			elif data[1] == 'g':
				enemies.append(Mob(*block_args,
				                   name='Guard', img=images['guard']))

	to_shift_x, to_shift_y = board_values[0].split()

	screen_shift.hard_reset = [tile_width * float(to_shift_x), tile_width * float(to_shift_y)]

	starting_screen_shift = [screen_shift.x, screen_shift.y]

	current_level = levels_list.pop(0)

	player.velocity = 0
	drag_ability.recharge_time_left = 0


def get_levels(file):
	level_names = []
	area_nums = []
	with open(file, 'r') as levels:

		for line in levels:
			if line[0] == 'A':
				level_name = line.rstrip('\n')
				level_names.append(level_name)

				area, level = line.split()
				area_num = int(area[1:])
				if area_num not in area_nums:
					area_nums.append(area_num)
	return [level_names, area_nums]


walls = list()
no_drag_zone = list()
no_move_zone = list()
goals = list()
enemies = list()
signs = list()
doors = [[], []]
sensors = list()

screen_shift = ScreenShift()

player = Character()

drag_ability = Ability()
drag_bar = CoolDownBar()

list_of_levels, all_area_numbers = get_levels('Levels.txt')

levels_in_save_file, save_area_numbers = get_levels('Saved Data.txt')

list_of_levels_left = list_of_levels[:]

for i in levels_in_save_file:
	if i in list_of_levels_left:
		list_of_levels_left.remove(i)

if not list_of_levels_left:
	list_of_levels_left = [levels_in_save_file[-1]]

current_level = None

generate_map_from_file(list_of_levels_left)

button_states = InputButtonStates()

# Buttons

paused_buttons = list()
completion_buttons = list()
level_select_buttons = list()
game_over_buttons = list()

level_select()
game_loop()
