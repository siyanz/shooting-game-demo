import kivy
__version__ = "1.9.0"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.uix.label import Label
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.button import Button
from functools import partial
import socket, time
from random import randint
import random

#setup graphics
from kivy.config import Config
Config.set('graphics','resizable',0)
 
#Graphics fix
from kivy.core.window import Window;
Window.clearcolor = (1,1,1,1)

UDP_IP = "128.237.220.101"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.connect((UDP_IP, UDP_PORT))

class Missile(Widget):
	def expend_size(self):
		if (self.size[0] < 300):
			self.size = Vector(5, 5) + self.size
	def cont_travel(self, velocity):
		self.pos = Vector(*velocity) + self.pos

class Enemy(Widget):
	velocity_x = NumericProperty(0)
	velocity_y = NumericProperty(0)
	spawnT = NumericProperty(0)
	def move(self):
		self.x = self.x + self.velocity_x
		self.y = self.y + self.velocity_y

class Score(Label):
	def show_score(self, s):
		self.text = str(s)

class ShootingGame(Widget):
	missile = ObjectProperty(None)
	enemy_list = []
	enemy_count = 0
	enemy_amount = 1
	update = False
	travel = True
	pos_current = Vector(0, 0)
	pos_down = Vector(0, 0)
	pos_up = Vector(0, 0)
	time_down = 0
	time_up = 0
	travelT = 0
	vel = Vector(0, 0)
	points = NumericProperty(0)

	# The following functions let users to shoot missiles by touching the screen
	def on_touch_down(self, touch):
		self.missile.size = Vector(0, 0)
		if (touch.x < self.parent.width/2):
			send_server(40002, 0.29, 400, 200)
		else:
			send_server(50002, 0.29, 400, 200)
		self.update = True
		self.pos_current = Vector(touch.x, touch.y)
		self.pos_down = self.pos_current
		self.time_down = time.time()
		self.missile.pos = (touch.x - self.missile.size[0]/2 , touch.y - self.missile.size[0]/2)

	def on_touch_move(self, touch):
		self.pos_current = Vector(touch.x,  touch.y)
		self.time_down = time.time()
		self.missile.pos = (touch.x - self.missile.size[0]/2 , touch.y - self.missile.size[0]/2)

	def on_touch_up(self, touch):
		self.time_up = time.time()
		self.pos_up = Vector(touch.x, touch.y)
		self.travelT = self.time_up - self.time_down

		if (self.travelT != 0):
			self.vel = Vector(((self.pos_up[0] - self.pos_down[0])/self.travelT)/60, 
				((self.pos_up[1] - self.pos_down[1])/self.travelT)/60)

		self.update = False

		if (self.vel[0] != 0) and (self.vel[1] != 0):
			self.travel = True
			if (self.vel[0] > 0 and self.pos_down[0] < (self.parent.width / 2)):
				(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.parent.width - self.pos_up[0])
				send_server(40001, intensity, duration, 200)
			elif (self.vel[0] < 0 and self.pos_down[0] > (self.parent.width / 2)):
				(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.pos_up[0])
				send_server(50001, intensity, duration, 200)
		else:
			send_server(40003, 0, 0, 200)
			send_server(50003, 0, 0, 200)

	# Randomly generating an enemy
	def drawEnemy(self, x_pos):
		tmpEnemy = Enemy()
		tmpEnemy.x = self.parent.width * x_pos

		randPos = randint(1, 100)
		tmpEnemy.y = float(randPos) /100 * self.parent.height

		tmpEnemy.velocity_x = 0
		tmpEnemy.velocity_y = randint(1, 5)
		tmpEnemy.spawnT = time.time()

		self.enemy_list.append(tmpEnemy)
		self.add_widget(tmpEnemy)

	def update(self, dt):
		# Size of missile increases when users press and hold
		if (self.update == True):
			self.missile.expend_size()
			self.missile.pos = (self.pos_current[0] - self.missile.size[0]/2 , self.pos_current[1] - self.missile.size[0]/2)

		# Missile travels is users flicks the missile
		if (self.travel == True):
			self.missile.cont_travel(self.vel)
			if ((self.missile.right < 0) or (self.missile.x > self.parent.width) or
				(self.missile.top < 0) or (self.missile.y > self.parent.height)):
				self.travel = False

		if (self.enemy_list == []):
			randX = random.choice([0.1, 0.2, 0.8, 0.9])
			while (len(self.enemy_list) < self.enemy_amount):
				self.drawEnemy(randX)
				self.enemy_count += 1

		for e in self.enemy_list:
			if (e.y < 0 or e.top > self.parent.height):
				e.velocity_y = -e.velocity_y
			e.move()
			if e.collide_widget(self.missile):
				round_score = int(1.0/(time.time() - e.spawnT)/self.missile.size[0] * 1000)
				if round_score > 300:
					round_score = 300
				elif round_score < 1:
					round_score = 1
				self.points  = self.points + round_score
				score = Score()
				score.pos = Vector(e.x, e.y + 5)
				score.show_score("[color=ff3333]" + str(round_score) + "[/color]")
				self.add_widget(score)
				Clock.schedule_once(lambda dt: self.remove_widget(score), 1)
				self.remove_widget(e)
				self.enemy_list.remove(e)


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


class ShootingApp(App):
	def build(self):
		parent = Widget()
		game =  ShootingGame()
		missile = Missile()

		parent.add_widget(game)
		parent.add_widget(missile)

		Clock.schedule_interval(game.update, 1.0 / 60.0)

		return parent



if __name__ == '__main__':	
    ShootingApp().run()