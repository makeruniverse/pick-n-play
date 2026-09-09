import pygame
from config import ROUND_OVER
from app import SceneBase


class IdleScene(SceneBase):
	def on_enter(self):
		pass

	def on_exit(self):
		pass

	def ProcessInput(self, events, pressed_keys):
		for event in events:
			if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
				# Move to the next scene when the user pressed Enter
				self.SwitchToScene(GameScene(self.ctx))

	def Update(self):
		# Should just Loop the Video of the Demo
		# Should Have Arcade Like Idle animation
		pass

	def Render(self, screen):
		# Should show Demo Video
		# and Leaderboard
		screen.fill((255, 0, 0))


class GameScene(SceneBase):
	def on_enter(self):
		# Process Input
		# Generate Random Number
		# Start Teleoperation mode in Lerobot
		# Start OpenCV AruCo detection
		self.t_start = pygame.time.get_ticks()
		pygame.time.set_timer(ROUND_OVER, 90_000, loops=1)

	def on_exit(self):
		pygame.time.set_timer(ROUND_OVER, 0)

	def ProcessInput(self, events, pressed_keys):
		# If User presses X, Game goes back to idle
		for event in events:
			if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
				# Show Warning, if pressed again switch to Idle
				self.SwitchToScene(IdleScene(self.ctx))
			if event.type == ROUND_OVER:
				self.SwitchToScene(DisplayScoreScene(self.ctx, self.score))
				# If Timer Ends
				# Save the Score/State and
				# self.SwitchToScene(DisplayScoreScene())

	def Update(self, dt):
		# Update the:
		# Video Feed
		# the current Score
		# the
		pass

	def Render(self, screen):
		# The game scene is just a blank blue screen
		screen.fill((0, 0, 255))



class DisplayScoreScene(SceneBase, ctx, score):
	def __init__(ctx, score):
		super().__init__(ctx)

	def on_enter(self):
		pass

	def on_exit(self):
		pass

	def ProcessInput(self, events, pressed_keys):
		# press L to go to Leaderboard scene
		# or press X to go back to idle without saving score
		pass

	def Update(self):
		pass

	def Render(self, screen):
		pass

class LeaderboardScene(SceneBase):

	def on_enter(self):
		pass

	def on_exit(self):
		pass

	def ProcessInput(self, events, pressed_keys):
		# Save Input in Array for Leaderboard
		# If Enter is pressed, check if array is valid, then either:
		# Play again, or go back to idle and save leaderboard
		pass

	def Update(self):
		# Update the Logic
		pass

	def Render(self, screen):
		pass
