import kivy
__version__ = "1.9.0"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, ObjectProperty, StringProperty, AliasProperty
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
from kivy.storage.jsonstore import JsonStore
 
Builder.load_file('shooting.kv')

#setup graphics
from kivy.config import Config
Config.set('graphics','resizable',0)
Config.set("input", "mouse", "mouse, disable_multitouch")
#Graphics fix
from kivy.core.window import Window;
Window.clearcolor = (1,1,1,1)

UDP_IP = "128.237.221.217"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

store = JsonStore('score.json')
try:
	if (store.exists('score')):
		pass
except:
	store.put('score', highest=0)
	print("error with store")

class MyButton(Button):
#class used to get uniform button styles
    def __init__(self, **kwargs):
        super(MyButton, self).__init__(**kwargs)
        self.font_size = Window.width*0.018
        self.size_hint = (None, None)

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
	# spawnT = NumericProperty(0)
	angle = NumericProperty(0)
	source = StringProperty("")
	# tracks position of the enemy (left or right)
	enemy_on_left = True
	state = "walking"
	def decrease(self, dec):
		self.size[0] = self.size[0] - dec
		self.size[1] = self.size[1] - dec
	def move(self):
		if (self.state == "walking"):
			self.x = self.x + self.velocity_x
			self.y = self.y + self.velocity_y
		elif (self.state == "hopping"):
			if self.enemy_on_left:
				randX = random.choice([0.85, 0.9, 0.95])
				if (self.x < randX * Window.width):
					self.x = self.x + 20
				else:
					self.state = "walking"
					self.enemy_on_left = False
					print(self.enemy_on_left)
			else:
				randX = random.choice([0.05, 0.1, 0.15])
				if (self.x > randX * Window.width):
					self.x = self.x - 20
				else:
					self.state = "walking"
					self.enemy_on_left = True
					print(self.enemy_on_left)
		
	def drawWalking(self, step):
		with self.canvas:
			def changeWalk(rect, newSource, *largs):
				print(newSource[:-1])
				if (self.state == "eating"):
					Clock.unschedule
				print(self.state)
				rect.source = newSource
			if (self.state == "walking"):
				if (self.velocity_y > 0):
					self.source = 'atlas://images/images/sprite.atlas/up_1'
					Clock.create_trigger(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/up_2'),step)
					Clock.create_trigger(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/up_3'),step*2)
					# self.move()
					Clock.create_trigger(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/up_4'),step*3)
					self.move()
					Clock.create_trigger(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/up_5'),step*4)
					self.move()
					Clock.create_trigger(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/up_6'),step*5)
				if (self.velocity_y < 0):
					self.source = 'atlas://images/images/sprite.atlas/down_1'
					Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/down_2'),step)
					Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/down_3'),step*2)
					# self.move()
					Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/down_4'),step*3)
					self.move()
					Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/down_5'),step*4)
					self.move()
					Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/down_6'),step*5)
			elif (self.state == "eating"):
				self.source = 'atlas://images/images/sprite.atlas/eat_1'
				Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/eat_2'),step*1)
				# self.move()
				Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/eat_3'),step*2)
				# self.move()
				Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/eat_4'),step*3)
				Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/eat_5'),step*5)
				# self.move()
				Clock.schedule_once(partial(changeWalk, self, 'atlas://images/images/sprite.atlas/eat_6'),step*6)
				self.state = "walking"
				# self.source = './images/walk1.png'
			elif (self.state == "hopping"):
				print("hopping")

class Score(Label):
	def show_score(self, s):
		self.text = str(s)

class TestCircle(Widget):
	def move(self, dt):
		self.x = self.x + self.velocity_x

class ShootingGame(Widget):
	missile = Missile()
	missile_list = [random.choice(["fruit1", "fruit2", "trash"]),
					random.choice(["fruit1", "fruit2", "trash"])]
	next_missile = StringProperty(missile_list[1])
	hungerBar = ObjectProperty(None)
	enemy = ObjectProperty(None)
	# this indicates if the frog is traveling or not
	travel = False
	pos_down = Vector(0, 0)
	pos_up = Vector(0, 0)
	time_down = 0
	time_up = 0
	missile_onscreen = False
	vel = Vector(0, 0)
	# this is the timer that controls if the bug stops or moves
	movement_timer = 5
	# a counter that shows how many back and forth (ups and downs) the enemy has been through
	# it also sets the level
	b_f_counter = 1
	# an indicator that shows if what is generated is trash or fruit
	is_trash = False
	is_gameOver = True
	level = NumericProperty(1)
	timer = NumericProperty(0)
	point = NumericProperty(0)

	def __init__(self, **kwargs):
		super(ShootingGame, self).__init__(**kwargs)
		# randX = random.choice([0.1, 0.2, 0.8, 0.9])
		# self.enemy = self.drawEnemy(randX)

		Clock.schedule_interval(self.update, 1.0 / 60.0)
		Clock.schedule_interval(partial(self.enemyAnimation, 0.1), 0.5)
		Clock.schedule_interval(self.inc_timer, 1)

	# The following functions let users to shoot missiles by touching the screen
	def on_touch_down(self, touch):
		if (not self.is_gameOver):
			self.level = int(self.point/5 + 1)
			if (self.missile_onscreen):
				try:
					self.remove_widget(self.missile)
				except:
					print "no missile to delete in on_touch_down"
				self.vel = Vector(0, 0)
				self.missile_onscreen = False
			# only draws a new object if there is none on the screen. Also checks for side of the bug
			if ((not self.missile_onscreen) and 
				((self.enemy.enemy_on_left and touch.x > (self.parent.width/2)) or
				((not self.enemy.enemy_on_left) and touch.x < self.parent.width/2)) and
				touch.y > 80):
				# generate new line
				with self.canvas:
					Color(0, 0, 1)
					self.line = Line(points=(touch.x, touch.y, touch.x, touch.y), width = 2)
					# self.dashed_line = Line(points=(self.pos_down.x, self.pos_down.y, self.pos_down.x, self.pos_down.y), width = 1, dash_offset = 5, dash_length=3)

				# generate a new missile
				self.missile_onscreen = True
				self.missile = Missile()
				self.add_widget(self.missile)
				self.missile.pos = (touch.x - self.missile.size[0]/2 , touch.y - self.missile.size[0]/2)
				self.pos_down = Vector(touch.x, touch.y)
				self.time_down = time.time()
				try:
					next = self.missile_list.pop(0)
					self.missile_list.append(random.choice(["fruit1", "fruit2", "trash"]))
					self.next_missile = self.missile_list[0]
				except:
					print "missile list ERROR cought!"
					next = random.choice(["fruit1", "fruit2", "trash"])
				self.missile.source = './images/' + next + ".png"
				if next == "trash":
					self.is_trash = True
				else: 
					self.is_trash = False
				intensity = float(self.missile.size[0])/300 * 0.29
				# lef
				if (touch.x < self.parent.width/2):
					if (self.is_trash):
						send_server(40002, intensity, 400, 200)
					else:
						send_server(40002, intensity * 3, 400, 70)
				# right
				else:
					if (self.is_trash):
						send_server(50002, intensity, 400, 200)
					else:
						send_server(50002, intensity * 3, 400, 70)

	def on_touch_move(self, touch):
		if (not self.is_gameOver):
			if (self.missile_onscreen):
				self.time_down = time.time()
				with self.canvas:
					# if ((self.enemy.enemy_on_left) and (touch.x < self.pos_down.x) or
					# 	(not self.enemy.enemy_on_left) and (touch.x > self.pos_down.x)):
					# 	Color(1, 0, 0)
					# else: 
					# 	Color (0, 1, 0)
					# try:
					# 	if (self.line):
					# 		self.canvas.remove(self.line)
					# 		self.canvas.remove(self.dashed_line)
					# except:
					# 	print "no missile to delete in on_touch_up"
					# self.line = Line(points=(touch.x, touch.y, self.pos_down.x, self.pos_down.y), width = 2)
					self.line.points = [touch.x, touch.y, self.pos_down.x, self.pos_down.y]

				# draw dashed line
					# dashed_x = self.pos_down.x - (touch.x - self.pos_down.x)/2
					# dashed_y = self.pos_down.y + (self.pos_down.y - touch.y)/2
					# self.dashed_line.points = [self.pos_down.x, self.pos_down.y, dashed_x, dashed_y]
					
				if (touch.x - self.pos_down[0] != 0):
					a = math.degrees(math.atan((-(touch.y - self.pos_down[1]))/(-(touch.x - self.pos_down[0]))))
					# left
					if (self.pos_down[0] < self.parent.width/2) and (touch.x - self.pos_down[0] < 0):
						self.missile.angle = a/2 - 45
					# right
					elif (self.pos_down[0] > self.parent.width/2) and (touch.x - self.pos_down[0] > 0): 
						self.missile.angle = a/2 + 45

	def on_touch_up(self, touch):
		if (not self.is_gameOver):
			# remove line
			try:
				if (self.line):
					self.canvas.remove(self.line)
					self.canvas.remove(self.dashed_line)
			except:
				print "no missile to delete in on_touch_up"
			# only gives speed and orientation if there is no object traveling already
			if (not self.missile_onscreen or self.vel != Vector(0, 0)):
				self.vel = Vector(0, 0)
				self.missile_onscreen = False
				self.vel = Vector(0, 0)
				send_server(40003, 0, 0, 200)
				send_server(50003, 0, 0, 200)
			else:
				self.time_up = time.time()
				self.pos_up = Vector(touch.x, touch.y)

				self.vel = Vector(-(self.pos_up[0] - self.pos_down[0])/5, -(self.pos_up[1] - self.pos_down[1])/5)
				#if the missile is going straight up or down
				# or if there is no speed to the missile
				# remove missile
				if (((self.enemy.enemy_on_left and self.vel[0] > 5 ) or (not self.enemy.enemy_on_left and self.vel[0] < -5)) or 
					(self.vel[0] == 0) or (self.vel[0] == 0 and self.vel[1] == 1)):
					try:
						self.remove_widget(self.missile)
					except:
						print "no missile to delete in on_touch_down(else)"
					self.missile_onscreen = False
					self.vel = Vector(0, 0)
					send_server(40003, 0, 0, 200)
					send_server(50003, 0, 0, 200)
				# frog traveling (with speed threshold)
				else:
					print("x vel: "+str(self.vel[0]))
					print("y vel: "+str(self.vel[1]))
					# left
					if (self.vel[0] > 0 and self.pos_down[0] < (self.parent.width / 2)):
						self.travel = True
						(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.parent.width - self.pos_up[0])
						print("send signal to right")
						# right
						if (self.is_trash):
							send_server(40001, intensity, duration, 200)
						else:
							send_server(40001, intensity * 3, duration, 70)
					elif (self.vel[0] < 0 and self.pos_down[0] > (self.parent.width / 2)):
						self.travel = True
						(intensity, duration) = get_haptic_par(self.missile.size[0], self.vel, self.pos_up[0])
						if (self.is_trash):
							send_server(50001, intensity, duration, 200)
						else:
							send_server(50001, intensity * 3, duration, 70)

	def inc_timer(self, dt):
		if (not self.is_gameOver):
			self.timer = self.timer + 1
			# print(self.timer)

	# Randomly generating an enemy
	def drawEnemy(self, x_pos):
		tmpEnemy = Enemy()
		tmpEnemy.x = self.width * x_pos

		# 1280 is the width of the screen
		if (tmpEnemy.x < Window.width/2):
			tmpEnemy.enemy_on_left = True
		else:
			tmpEnemy.enemy_on_left = False

		randPos = randint(15, 90)
		# 1200 is the width of the screen
		tmpEnemy.y = float(randPos) /100 * Window.width

		# print(tmpEnemy.y)

		tmpEnemy.velocity_x = 0
		# tmpEnemy.velocity_y = -22
		tmpEnemy.spawnT = time.time()

		# print tmpEnemy.angle
		# if (tmpEnemy.velocity_y < 0):
		# 	print("rotating")
		# 	tmpEnemy.angle = 0
		# else:
		# 	# tmpEnemy.angle = -90
		# 	pass

		self.add_widget(tmpEnemy)
		return tmpEnemy

	def enemyAnimation(self, step_t, dt):
		if (not self.is_gameOver):
			self.enemy.drawWalking(step_t)
			if (self.enemy.velocity_y > 0):
				self.enemy.velocity_y = 5.5 * self.level + 16.5
			else:
				self.enemy.velocity_y = -(5.5 * self.level + 16.5)
			# self.enemy.decrease(self.level)

	def remove_all(self):
		send_server(40003, 0, 0, 200)
		send_server(50003, 0, 0, 200)
		try:
			self.remove_widget(self.enemy)
			self.remove_widget(self.missile)
			self.parent.remove_widget(self.restartButton)
			self.parent.remove_widget(self.L1)
			self.parent.remove_widget(self.your_score)
			self.parent.remove_widget(self.L2)
			self.parent.remove_widget(self.high_score_display)
			if (self.line):
				self.canvas.remove(self.line)
		except:
			print "all things on screen removed in restart"	

	def restart(self):
		self.remove_all()
		randX = random.choice([0.1, 0.2, 0.8, 0.9])
		self.enemy = self.drawEnemy(randX)

		self.is_gameOver = False
		self.b_f_counter = 1
		self.level = 1
		self.timer = 0
		self.point = 0

	def gameOver(self):
		send_server(40003, 0, 0, 200)
		send_server(50003, 0, 0, 200)
		print("game over")

		# if there is a line drawn, remove line. Otherwise, pass
		try:
			if (self.line):
				self.canvas.remove(self.line)
		except:
			print "no missile to delete in gameOver"
		self.remove_widget(self.enemy)
		self.remove_widget(self.missile)
		#add a restart button
		self.restartButton = MyButton(text='Restart')
		self.restartButton.size = (Window.width*.3,Window.width*.05)
		self.restartButton.pos = Window.width*0.5-self.restartButton.width/2, Window.height*0.2

		# update new high score
		if (self.point > store.get('score')['highest']):
			store.put('score', highest = self.point)
			print "new high score!"

		self.L1 = Label(text = "Your Score", font_size = Window.width*0.03, color=[0,0,0,1])
		self.L1.pos = 0, Window.height/3
		self.your_score = Label(text = str(self.point), font_size = Window.width*0.03, color=[0,0,0,1])
		self.your_score.pos = 0, Window.height/4
		self.L2 = Label(text = "Highest Score", font_size = Window.width*0.03, color=[0,0,0,1])
		self.L2.pos = 0, Window.height/4 - 1.5*(Window.height/3 - Window.height/4)
		high_score = store.get('score')['highest']
		self.high_score_display = Label(text = str(high_score), font_size = Window.width*0.03, color=[0,0,0,1])
		self.high_score_display.pos = 0, Window.height/4 - 2.5*(Window.height/3 - Window.height/4)

		#restartButton.background_color = (.5,.5,1,.2)
		def restart_button(obj):
			print 'restart button pushed'
			# reset game
			self.restart()

		self.restartButton.bind(on_release=restart_button)
		self.parent.add_widget(self.restartButton)
		self.parent.add_widget(self.L1)
		self.parent.add_widget(self.your_score)
		self.parent.add_widget(self.L2)
		self.parent.add_widget(self.high_score_display)


	def update(self, dt):
		if (not self.is_gameOver):
			# self.enemy.move()
			# Missile travels is users flicks the missile
			if (self.travel):
				self.missile.cont_travel(self.vel)
				if ((self.missile.right < 0) or (self.missile.x > self.parent.width) or
					(self.missile.top < 0) or (self.missile.y > self.parent.height)):
					self.travel = False
					self.missile_onscreen = False
					self.vel = Vector(0, 0)
					send_server(40003, 0, 0, 200)
					send_server(50003, 0, 0, 200)

			# controls when the enemy moves and stops and hops)
			if (self.b_f_counter % 3 == 0):
				self.b_f_counter += 1
				self.enemy.state = "hopping"
			else:
				# controls the timing of the enemy moving
				# if ((time.time() % self.movement_timer) < 0.015):
				# 	self.b_f_counter += 1
				# 	if (self.enemy.state == "walking"):
				# 		self.b_f_counter += 1
				# 		self.enemy.state = "mouth_open"
				# 	elif (self.enemy.state == "mouth_open"):
				# 		self.enemy.state = "walking"
				self.movement_timer = random.randint(3, 5)

			# print(self.enemy.angle)
			# Animate the enemy turning around
			if (self.enemy.top > self.parent.height and self.enemy.velocity_y > 0):
				print("top:" + str(self.enemy.y))
				print("top-v:" + str(self.enemy.velocity_y))
				# angle = -90
				# Animation(center=self.enemy.center, angle=angle, duration = 0.5).start(self.enemy)
				self.enemy.velocity_y = -(self.enemy.velocity_y)
			elif (self.enemy.y < 118 and self.enemy.velocity_y < 0):
				print("botton:" + str(self.enemy.y))
				# angle = 90
				# Animation(center=self.enemy.center, angle=angle, duration = 0.5).start(self.enemy)
				print("bottom-v: " + str(self.enemy.velocity_y))
				self.enemy.velocity_y = -(self.enemy.velocity_y)
			# when frog catches the bug
			if (self.missile and self.enemy.collide_widget(self.missile) and self.missile_onscreen):
				self.enemy.state = "eating"
				print("change to eating state")
				score = Score()
				score.pos = Vector(self.enemy.x, self.enemy.y + 5)
				score.font_size = 30

				if (self.is_trash == False):
					if (self.enemy.x < self.parent.width / 2):
						send_server(60001, 0.4, 0, 70)
					if (self.enemy.x > self.parent.width / 2):
						send_server(60002, 0.4, 0, 70)
					self.point += 1
					# self.enemy.size[0] += 3
					# self.enemy.size[1] += 3
					score.show_score("[color=ff3333]" + "YUM!" + "[/color]")
				else:
					if (self.enemy.x < self.parent.width / 2):
						send_server(60001, 0.4, 0, 200)
					if (self.enemy.x > self.parent.width / 2):
						send_server(60002, 0.4, 0, 200)
					self.timer -= 5
					punish = Score()
					punish.pos = Vector(Window.width/2, Window.height - 200)
					punish.font_size = Window.width * 0.03
					punish.show_score("[color=ff3333]"+"-5 seconds" + "[/color]")
					# self.enemy.size[0] -= 5
					# self.enemy.size[1] -= 5	
					score.font_size = 30
					score.show_score("[color=ff3333]" + "EWW!" + "[/color]")

					self.add_widget(punish)		
					Clock.schedule_once(lambda dr: self.remove_widget(punish), 1)		
				self.add_widget(score)
				Clock.schedule_once(lambda dt: self.remove_widget(score), 1)
				#removing missile as well - removed bug: frog gets stuck on the edge of the screen
				try:
					self.remove_widget(self.missile)
				except:
					print "no missile to delete in update"
				self.missile_onscreen = False
				self.vel = Vector(0, 0)

			if (self.timer >= 60):
				self.is_gameOver = True
				self.gameOver()


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
	# sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

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


class ShootingApp(App):
	# Set up screen in App so that kv can access game_screen.game.is_gameOver
	sm = ScreenManager()
	sm.add_widget(WelcomeScreen(name='welcome'))
	sm.add_widget(BasicScreen1(name='basic1'))
	sm.add_widget(BasicScreen2(name='basic2'))
	basicscreen3 = BasicScreen3(name='basic3')
	sm.add_widget(basicscreen3)
	game_screen = GameScreen(name='game')
	sm.add_widget(game_screen)

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
		return self.sm

if __name__ == '__main__':	
    ShootingApp().run()