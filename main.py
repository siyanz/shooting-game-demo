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
	cont_travel = False
	pos_current = Vector(0, 0)
	pos_down = Vector(0, 0)
	pos_up = Vector(0, 0)
	time_down = 0
	time_up = 0
	travelT = 0
	vel = Vector(0, 0)

	def on_touch_down(self, touch):
		self.missile.size = Vector(0, 0)
		send_server(40005, 0.29, 400, 200)
		self.update = True
		self.pos_current = Vector(touch.x, touch.y)
		self.pos_down = self.pos_current
		self.time_down = time.time()
		self.missile.pos = (touch.x - self.missile.size[0]/2 , touch.y - self.missile.size[0]/2)

	def on_touch_move(self, touch):
		self.pos_current = Vector(touch.x,  touch.y)
		self.missile.pos = (touch.x - self.missile.size[0]/2 , touch.y - self.missile.size[0]/2)

	def on_touch_up(self, touch):
		self.time_up = time.time()
		self.pos_up = Vector(touch.x, touch.y)
		self.travelT = self.time_up - self.time_down
		self.vel = Vector((self.pos_up[0] - self.pos_down[0])/self.travelT/50, (self.pos_up[1] - self.pos_down[1])/self.travelT/50)

		send_server(40006, 0.29, 400, 200)
		self.update = False
		self.cont_travel = True

	def update(self, dt):
		if (self.update == True):
			self.missile.expend_size()
			self.missile.pos = (self.pos_current[0] - self.missile.size[0]/2 , self.pos_current[1] - self.missile.size[0]/2)
		if (self.cont_travel == True):
			self.missile.cont_travel(self.vel)
			if (((self.missile.x + 2 * self.missile.size[0]) < 0) or (self.missile.x > self.parent.width)  or 
				(self.missile.y < 0) or ((self.missile.y - 2 * self.missile.size[0]) > self.parent.height)):
				self.cont_travel = False


class ShootingApp(App):

	def build(self):
		parent = Widget()
		game =  ShootingGame()
		button = Button(text = "Play FE")
		missile = Missile()

		parent.add_widget(game)
		parent.add_widget(missile)
		parent.add_widget(button)

		button.bind(on_press=partial(send_server, 40003, 0.29, 400, 200))

		Clock.schedule_interval(game.update, 1.0 / 60.0)

		return parent
	

def send_server(*args):
	port = args[0]
	intensity = args[1]	
	duration = args[2]
	frequency = args[3]


	MESSAGE = "%d;%f;%f;%f" % (port, intensity, duration, frequency)
	sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))


if __name__ == '__main__':	
    ShootingApp().run()