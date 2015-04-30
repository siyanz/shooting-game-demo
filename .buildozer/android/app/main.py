import kivy
__version__ = "1.9.0"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.button import Button
from functools import partial
import socket, time


UDP_IP = "128.237.217.81"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.connect((UDP_IP, UDP_PORT))

class Missile(Widget):
	def expend_size(self):
		if (self.size[0] < 300):
			self.size = Vector(5, 5) + self.size
	def cont_travel(self, velocity):
		self.pos = Vector(*velocity) + self.pos

class ShootingGame(Widget):
	missile = ObjectProperty(None)
	update = False
	travel = True
	pos_current = Vector(0, 0)
	pos_down = Vector(0, 0)
	pos_up = Vector(0, 0)
	time_down = 0
	time_up = 0
	travelT = 0
	vel = Vector(0, 0)

	def on_touch_down(self, touch):
		#prevent having two missiles on the screen at the same time
		if self.travel == False:
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
			self.vel = Vector(((self.pos_up[0] - self.pos_down[0])/self.travelT)/60, ((self.pos_up[1] - self.pos_down[1])/self.travelT)/60)

		self.update = False
		if (self.vel[0] != 0) and (self.vel[1] != 0):
			self.travel = True
			if (self.vel[0] > 0):
				(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.parent.width - self.pos_up[0])
				send_server(40001, intensity, duration, 200)
			else:
				(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.pos_up[0])
				send_server(50001, intensity, duration, 200)
		else:
			send_server(40003, 0, 0, 200)
			send_server(50003, 0, 0, 200)

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
		button = Button(text = "Play FE")
		missile = Missile()

		parent.add_widget(game)
		parent.add_widget(missile)
		parent.add_widget(button)

		Clock.schedule_interval(game.update, 1.0 / 60.0)

		return parent



if __name__ == '__main__':	
    ShootingApp().run()