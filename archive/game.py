import pygame as pg
import sys

class Game:
	"""The Main Game Loop with Cooldown, Video Passthrough etc."""

	def __init__(self):
		pg.init()
		pg.display.set_caption("Pick N Play")
		self.screen = pg.display.set_mode((0,0), pg.FULLSCREEN)
		
	def idle(self):
		# 
		# Show Video Playback of How Game Works
		# Have Explanation for how to Start the game and how it works, so user knows what to do immediately
		# if button is presed go to run game and start the teleoperation (so it's not running 24/7)
		while True:
			self._check_events()
			self._update_screen()

		

	def run_game(self):
		# RNG for Target Number
		# start the timer
		# call opencv camera setup function and 
		# while true loop:
		# start displaying the webcam feed
		# show the target Number
		# if q pressed quit game
		while True:
			# self check events (quitting game)
			self._check_events()
			self._update_screen()

	def _check_events(self):
		for event in pg.event.get():
			if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
				sys.exit()
			elif event.type == pg.KEYDOWN:
				if event.key == pg.K_s
					self.run_game()

	def _update_screen(self):
		self.screen.fill((255,255,0))
		pg.display.flip()
	
	def cvimage_to_pg(self, image):
		"""Convert cvimage into a pg image"""
		pg.image.frombuffer(image.tostring(), image.shape[1::-1], "BGR")

	


if __name__ == '__main__':
	game = Game()
	game.idle()