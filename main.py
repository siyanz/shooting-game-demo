import kivy
__version__ = "1.9.0"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, StringProperty
from kivy.uix.relativelayout import RelativeLayout
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Line, Color, Rectangle
from functools import partial
import socket, time, math, random, math
from random import randint
from kivy.lang import Builder
 
Builder.load_file('shooting.kv')

#setup graphics
from kivy.config import Config
Config.set('graphics','resizable',0)
 
#Graphics fix
from kivy.core.window import Window;
Window.clearcolor = (1,1,1,1)

UDP_IP = "10.0.1.5"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class Missile(Widget):
	angle = NumericProperty(0)
	source = StringProperty("")
	def expend_size(self):
		if (self.size[0] < 200):
			self.size[0] = Vector(3, 3) + self.size
	def cont_travel(self, velocity):
		self.pos = Vector(*velocity) + self.pos
	def rotate(self, a):
		self.angle = a

class Enemy(Widget):
	velocity_x = NumericProperty(0)
	velocity_y = NumericProperty(0)
	spawnT = NumericProperty(0)
	angle = NumericProperty(0)
	source = StringProperty("")
	# tracks position of the enemy (left or right)
	enemy_on_left = True
	state = "walking"
	def decrease(self, dec):
		# print(self.size)
		self.size[0] = self.size[0] - dec
		self.size[1] = self.size[1] - dec
	def move(self):
		if (self.state == "walking"):
			self.x = self.x + self.velocity_x
			self.y = self.y + self.velocity_y
		elif (self.state == "mouth_open"):
			self.x = self.x
			self.y = self.y
		elif (self.state == "hopping"):
			if self.enemy_on_left:
				randX = random.choice([0.85, 0.9, 0.95])
				if (self.x < randX * 1280):
					self.x = self.x + 20
				else:
					self.state = "walking"
					self.enemy_on_left = False
			else:
				randX = random.choice([0.05, 0.1, 0.15])
				if (self.x > randX * 1280):
					self.x = self.x - 20
				else:
					self.state = "walking"
					self.enemy_on_left = True
		
	def drawWalking(self):
		with self.canvas:
			if (self.state == "walking"):
				self.source = './images/walk1.png'
				def changeWalk(rect, newSource, *largs):
					rect.source = newSource
				Clock.schedule_once(partial(changeWalk, self, './images/walk2.png'),0.5)
			elif (self.state == "mouth_open"):
				self.source = './images/walk1.png'
			elif (self.state == "hopping"):
				print("hopping")
				pass

class HungerBar(Widget):
	def hunger_dec(self, dt):
		if (self.size[0] > 0):
			print(self.size[0])
			self.size[0] = self.size[0] - 5
	def hunger_inc(self, increase):
		if (self.size[0] + increase < 100):
			self.size = Vector(increase, 0) + self.size

class Score(Label):
	def show_score(self, s):
		self.text = str(s)

class TestCircle(Widget):
	def move(self, dt):
		self.x = self.x + self.velocity_x

class ShootingGame(Widget):
	missile = Missile()
	hungerBar = ObjectProperty(None)
	enemy = Enemy()
	# this indicates if the frog is traveling or not
	travel = False
	pos_down = Vector(0, 0)
	pos_up = Vector(0, 0)
	time_down = 0
	time_up = 0
	missile_onscreen = False
	vel = Vector(0, 0)
	points = NumericProperty(0)
	# this is the timer that controls if the bug stops or moves
	movement_timer = 5
	# a counter that shows how many back and forth (ups and downs) the enemy has been through
	# it also sets the level
	b_f_counter = 1
	# an indicator that shows if what is generated is trash or fruit
	is_trash = False

	def __init__(self, **kwargs):
		super(ShootingGame, self).__init__(**kwargs)
		randX = random.choice([0.1, 0.2, 0.8, 0.9])
		self.enemy = self.drawEnemy(randX)

		Clock.schedule_interval(self.update, 1.0 / 60.0)
		Clock.schedule_interval(self.enemyAnimation, 1)

	# The following functions let users to shoot missiles by touching the screen
	def on_touch_down(self, touch):
		if (self.missile):
			self.remove_widget(self.missile)
			self.vel = Vector(0, 0)
			self.missile_onscreen = False
		# only draws a new object if there is none on the screen. Also checks for side of the bug
		if ((not self.missile_onscreen) and 
			((self.enemy.enemy_on_left and touch.x > (self.parent.width/2)) or
			((not self.enemy.enemy_on_left) and touch.x < self.parent.width/2)) and
			touch.y > 80):
			# generate new line
			with self.canvas:
				Color(1, 0, 0)
				self.line = Line(points=(touch.x, touch.y, touch.x, touch.y), width = 2)
			# generate a new missile
			self.missile_onscreen = True
			self.missile = Missile()
			self.add_widget(self.missile)
			self.missile.pos = (touch.x - self.missile.size[0]/2 , touch.y - self.missile.size[0]/2)
			self.pos_down = Vector(touch.x, touch.y)
			self.time_down = time.time()
			icon = random.choice(["fruit1", "fruit2", "trash"])
			self.missile.source = './images/' + icon + ".png"
			if icon == "trash":
				self.is_trash = True
			else: 
				self.is_trash = False
		# rotate sprite
		# left
		if (touch.x < self.parent.width/2):
				self.missile.angle = -45
				send_server(40002, 0.29, 400, 200)
		# right
		else:
				self.missile.angle = 45
				send_server(50002, 0.29, 400, 200)

	def on_touch_move(self, touch):
		if (self.missile_onscreen):
			self.time_down = time.time()
			with self.canvas:
				self.line.points = [touch.x, touch.y, self.pos_down.x, self.pos_down.y]

			if (touch.x - self.pos_down[0] != 0):
				a = math.degrees(math.atan((-(touch.y - self.pos_down[1]))/(-(touch.x - self.pos_down[0]))))
				# left
				if (self.pos_down[0] < self.parent.width/2) and (touch.x - self.pos_down[0] < 0):
					self.missile.angle = a/2 - 45
				# right
				elif (self.pos_down[0] > self.parent.width/2) and (touch.x - self.pos_down[0] > 0): 
					self.missile.angle = a/2 + 45

	def on_touch_up(self, touch):
		# remove line
		self.canvas.remove(self.line)
		if (not self.missile_onscreen or self.vel != Vector(0, 0)):
			self.remove_widget(self.missile)
			self.vel = Vector(0, 0)
			self.missile_onscreen = False
			self.vel = Vector(0, 0)
			send_server(40003, 0, 0, 200)
			send_server(50003, 0, 0, 200)
		# only gives speed and orientation if there is no object traveling already
		else:
			self.time_up = time.time()
			self.pos_up = Vector(touch.x, touch.y)
			
			self.vel = Vector(-(self.pos_up[0] - self.pos_down[0])/5, -(self.pos_up[1] - self.pos_down[1])/5)
			# frog traveling (with speed threshold)
			if ((((self.enemy.enemy_on_left and self.vel[0]) < -5 ) or (not self.enemy.enemy_on_left and self.vel[0])) and (self.vel[1] != 0)):
				print("x vel: "+str(self.vel[0]))
				print("y vel: "+str(self.vel[1]))
				# left
				if (self.vel[0] > 0 and self.pos_down[0] < (self.parent.width / 2)):
					self.travel = True
					(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.parent.width - self.pos_up[0])
				# right
					send_server(40001, intensity, duration, 200)
				elif (self.vel[0] < 0 and self.pos_down[0] > (self.parent.width / 2)):
					self.travel = True
					(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.pos_up[0])
					send_server(50001, intensity, duration, 200)
				else:
					self.remove_widget(self.missile)
					self.vel = Vector(0, 0)
					send_server(40003, 0, 0, 200)
					send_server(50003, 0, 0, 200)
				

	
	def drawBar(self):
		bar = HungerBar()
		self.add_widget(bar)
		return bar

	# Randomly generating an enemy
	def drawEnemy(self, x_pos):
		tmpEnemy = Enemy()
		tmpEnemy.x = self.width * x_pos

		# 1280 is the width of the screen
		if (tmpEnemy.x < 1280/2):
			tmpEnemy.enemy_on_left = True
		else:
			tmpEnemy.enemy_on_left = False

		randPos = randint(15, 90)
		# 1200 is the width of the screen
		tmpEnemy.y = float(randPos) /100 * 800

		tmpEnemy.velocity_x = 0
		tmpEnemy.velocity_y = -(randint(1, 3))
		tmpEnemy.spawnT = time.time()

		self.add_widget(tmpEnemy)
		return tmpEnemy

	def enemyAnimation(self, dt):
		self.enemy.drawWalking()
		self.enemy.decrease(int(self.b_f_counter/10 + 1))

	def update(self, dt):
		# Missile travels is users flicks the missile
		if (self.travel):
			self.missile.cont_travel(self.vel)
			if ((self.missile.right < 0) or (self.missile.x > self.parent.width) or
				(self.missile.top < 0) or (self.missile.y > self.parent.height)):
				self.travel = False
				self.missile_onscreen = False
				self.vel = Vector(0, 0)


		if (self.b_f_counter % 3 == 0):
			self.b_f_counter += 1
			self.enemy.state = "hopping"
		else:
			# controls the timing of the enemy moving
			if ((time.time() % self.movement_timer) < 0.015):
				if (self.enemy.state == "walking"):
					self.b_f_counter += 1
					self.enemy.state = "mouth_open"
				else:
					self.enemy.state = "walking"
				self.movement_timer = random.randint(3, 5)

		# print("State:" + self.enemy.state)
		self.enemy.move()

		# Animate the bug turning around
		if (self.enemy.top > self.parent.height and self.enemy.velocity_y > 0):
			print("top:" + str(self.enemy.y))
			angle = -90
			Animation(center=self.enemy.center, angle=angle, duration = 0.5).start(self.enemy)
			self.enemy.velocity_y = -(self.enemy.velocity_y)
		elif (self.enemy.y < 80 and self.enemy.velocity_y < 0):
			print("botton:" + str(self.enemy.y))
			angle = 90
			Animation(center=self.enemy.center, angle=angle, duration = 0.5).start(self.enemy)
			print("bottom-v: " + str(self.enemy.velocity_y))
			self.enemy.velocity_y = -(self.enemy.velocity_y)
		# when frog catches the bug
		if (self.missile and self.enemy.collide_widget(self.missile) and self.missile_onscreen):
			score = Score()
			score.pos = Vector(self.enemy.x, self.enemy.y + 5)
			if (self.is_trash == False):
				self.enemy.size[0] += 5
				self.enemy.size[1] += 5
				score.show_score("[color=ff3333]" + "YUM!" + "[/color]")
			else:
				if (self.enemy.x < self.parent.width / 2):
					send_server(60001, 0, 0, 200)
				if (self.enemy.x > self.parent.width / 2):
					send_server(60002, 0, 0, 200)
				self.enemy.size[0] -= 5
				self.enemy.size[1] -= 5	
				score.show_score("[color=ff3333]" + "EWW!" + "[/color]")					
			self.add_widget(score)
			Clock.schedule_once(lambda dt: self.remove_widget(score), 1)
			#removing missile as well - removed bug: frog gets stuck on the edge of the screen
			self.remove_widget(self.missile)
			self.missile_onscreen = False
			self.vel = Vector(0, 0)
			# self.enemy_list.remove(e)

def get_haptic_par(size, vel, canvasWidth):
	intensity = float(size)/300 * 0.29
	vis_dur_tot = canvasWidth/(abs(vel[0]) * 60) * 1000
	hap_dur_tot = 0.69 * vis_dur_tot + 137.02
	#hap_dur_tot = dur + soa = dur + 0.28 * dur + 60.7 => dur = (hap_dur_tot - 60.7)/1.28
	return (intensity, (hap_dur_tot - 60.7)	/1.28)

def send_server(*args):
	port = args[0]
	intensity = args[1]	
	duration = args[2]
	frequency = args[3]

	MESSAGE = "%d;%f;%f;%f" % (port, intensity, duration, frequency)
	sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

class WelcomeScreen(Screen):
	pass

class BasicScreen1(Screen):
	pass

class BasicScreen2(Screen):
	pass

class BasicScreen3(Screen):
	pass

class GameScreen(Screen):
	def __init__(self, **kwargs):
	    super(GameScreen, self).__init__(**kwargs)
	    self.game = ShootingGame()
	    self.add_widget(self.game)

sm = ScreenManager()
sm.add_widget(WelcomeScreen(name='welcome'))
sm.add_widget(BasicScreen1(name='basic1'))
sm.add_widget(BasicScreen2(name='basic2'))
basicscreen3 = BasicScreen3(name='basic3')
sm.add_widget(basicscreen3)
game_screen = GameScreen(name='game')
sm.add_widget(game_screen)

class ShootingApp(App):
	def printThis(self, x):
		print(x)

	def play_haptic(self, intensity, duration):
		send_server(40001, intensity, duration, 70)

	def play_ball(self, intensity, duration):
		ball = TestCircle()
		# i = 0.0106 * math.pow(10, (intensity - 38.892)/9.7721)
		# ball.size = Vector(50, 50)
		ball.pos = Vector(0,405)
		basicscreen3.add_widget(ball)
		lengthT = duration + 0.4 * duration + 0.28 * duration + 60.7
		ball.velocity_x = ball.parent.width/lengthT * 20
		Clock.schedule_interval(ball.move, 1.0/60.0)
		if (ball.x > ball.parent.width):
			basicscreen3.remove_widget(ball)


	def build(self):
		return sm

if __name__ == '__main__':	
    ShootingApp().run()