# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

# Code by Aljon Viray (86285526) and Daniel Mishkanian (44251598)

from AI import AI
from Action import Action
import random
from queue import Queue


class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		
		self.rowDimension = rowDimension
		self.colDimension = colDimension
		self.totalMines = totalMines
		self.moveCountMax = rowDimension*colDimension*2
		self.moveCount = 0
		self.prevX = startX
		self.prevY = startY
		self.startX = startX
		self.startY = startY

		#Setup:
		#Make a 2D array to store the AI's current view of the board
		#'?' = Unknown tile, everything else = number on that tile after uncovered
		#Later, the board will use "effective labels" -> Actual Label - neighboring flagged tiles
		#Example: A tile has '1', but most it neighbors are uncovered except for 1 that is flagged
			#The flagged one id definitely a bomb, so now we know that any remaining neighbors are safe
		self.board = [[['?', '?'] for i in range(rowDimension)] for j in range(colDimension)]

		#Make a "frontier" queue for this 2D array, order the next actions we plan to take
		#This makes next moves more systematic, since you can add next moves to the queue simply
		#Also, automatically add neighbors of starting tile to frontier, FIRST MOVE ONLY
		self.frontier = list()
		self.flaggingQueue = list()

		#Keep track of remaining tiles/coords, list of 1's, count of flags
		self.numberedTiles = list()
		self.uncovered = list()
		self.remaining = list()
		for i in range(rowDimension):
			for j in range(colDimension):
				self.remaining.append( (i,j) )
		self.remaining.remove( (startX,startY) )
		self.flags = dict()

		#Since starting tile is always '0', immediately add neighbors to frontier
			#Perform all UNCOVERS on neighbors, add those neighbors to frontier as well
		self.addTilesNearZero(startX, startY)

		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

		

	def getAction(self, number: int) -> "Action Object":

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################

		#Record the previous turn, update flag neighbors' effective labels
		self.moveCount += 1
		self.recordTileLabel(number)
		#If out of moves OR we believe we won the game, LEAVE
		if self.moveCount >= self.moveCountMax:
			#print("---Leaving... because out of moves - 'AI lost?'---")
			return Action(AI.Action(0))
		elif self.isBoardComplete():
			#print("---Leaving... because the game board was completed - 'AI won?'---")
			return Action(AI.Action(0))

		#print('\nResulting Board:')
		#self.printAIBoard()	

		#Check every numbered tile for rule-of-thumb: "EffectiveLabel == NumOfUnmarkedNeighbors -> neighbors are bombs"
		#print('Numbered Tiles =', self.numberedTiles)
		for tile in self.numberedTiles:
			unmarkedNeighbors = set()
			x = tile[0]
			y = tile[1]
			neighbors = [ (x, y+1), (x-1, y+1), (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1), (x+1, y), (x+1, y+1)]
			for n in neighbors:
				if self.isInBounds(n[0], n[1]):
					if self.board[n[0]][n[1]][0] == '?':
						unmarkedNeighbors.add(n)
			if self.board[x][y][1] == len(unmarkedNeighbors):
				for n2 in list(unmarkedNeighbors):
					if n2 not in self.flaggingQueue and n2 not in list(self.flags.keys()):
						self.flaggingQueue.append(n2)
	
		#Pop through frontier until coords are a valid tile to UNCOVER
		#print()
		while True:
			#print('iterating frontier... =', self.frontier)

			#Flagging Queue Case: Flag any guaranteed flags found by rule-of-thumb
			#print('\nFlagging Queue =', self.flaggingQueue)
			if len(self.flaggingQueue) != 0:
				#Update every non-zero and non-flag tile for "EffectiveLabel == NumOfCoveredNeighbors"
				#If true, all covered neighbors of tile are bombs.
				if len(self.flaggingQueue) > 0:
					while True:
						flag = self.flaggingQueue.pop(0)
						if flag not in list(self.flags.keys()):
							break
					#print('Flagging now:', flag)
					self.effectiveLabeling(flag[0], flag[1])
					self.finishFunction(number, 2, flag[0], flag[1])
					return Action(AI.Action(2), flag[0], flag[1])

			if len(self.frontier) != 0:
				coords = self.frontier.pop(0)
				#Normal case: Found tile to uncover that is valid and not a bomb
				if coords not in self.uncovered and self.isInBounds(coords[0], coords[1]):
					#print('Breaking out of loop, found valid tile in frontier...')
					break

			#Flagging Case: Flag possible bomb using right-angle method
			elif len(self.frontier) == 0:
				if len(self.flags) != self.totalMines and len(self.numberedTiles) >= 3:
					#print('\nFlagging Corner bomb...')
					flag = None
					for i in self.numberedTiles:
						flag = self.flagBombs()
						if flag == None: continue
						else: break
					#If did not find valid flag, do random UNCOVER instead
					#print('Flag =', flag)
					if flag != None:
						if type(flag) == list:
							#Sometimes returns 2 flags, separate them here
							self.flaggingQueue.append(flag[0])
							flag = flag[1]

						self.effectiveLabeling(flag[0], flag[1])
						self.finishFunction(number, 2, flag[0], flag[1])
						return Action(AI.Action(2), flag[0], flag[1])
					else:
						#print('\nCorner and Effective Label Flags not found, trying random coords...')
						coords = self.chooseRandomTile()
						break

				#Cleanup Case: Bombs have been flagged, UNCOVER all remaining tiles that are not flagged
				elif len(self.flags) == self.totalMines:
					#print('\nAll bombs flagged, moving remaining tiles to frontier...')
					self.frontier = self.remaining
					self.remaining = []
					coords = self.frontier.pop(0)
					break

				#Last Resort Case: Try random coords if no other options
				else:
					#print('\nEverything else failed, trying random coords...')
					coords = self.chooseRandomTile()
					break
		#print()

		self.finishFunction(number, 1, coords[0], coords[1])
		return Action(AI.Action(1), coords[0], coords[1])



	### Helper Functions ###
	
	#Condenses all end-of-function actions into one place (returning action and coordinates, assigning values, etc.)
	#Actions from AI.py are as follows: [LEAVE = 0, UNCOVER = 1, FLAG = 2, UNFLAG = 3]
	def finishFunction(self, number, action, x, y):
		#print("Next ACTION = {0}: ({1}, {2})".format(action, x, y))
		tiles = [ (x, y+1), (x-1, y+1), (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1), (x+1, y), (x+1, y+1)]
		if action == 2:
			self.flags[ (x,y) ] = tiles
		self.prevX = x
		self.prevY = y
		if len(self.remaining) != 0:
			self.remaining.remove( (x,y) )


	#Adds all adjacent tiles into frontier, in a radius to a '0' tile
	#Initial tile is ALWAYS guaranteed to be '0'
	def addTilesNearZero(self, x, y):
		tiles = [ (x, y+1), (x-1, y+1), (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1), (x+1, y), (x+1, y+1)]
		#print('\nPossible tiles =', tiles)
		for tile in tiles:
			#We want the tile to be NOT UNCOVERED and IN BOUNDS
			if tile not in self.frontier and tile not in self.uncovered and self.isInBounds( tile[0], tile[1] ):
				#print("Adding tile:", tile)
				self.frontier.append( tile )


	#Record the label of the tile we just uncovered/flagged
	def recordTileLabel(self, number):
		self.uncovered.append( (self.prevX,self.prevY) )

		if number == -1:
			self.board[self.prevX][self.prevY][0] = 'F'
			self.board[self.prevX][self.prevY][1] = 'F'
		elif number == 0:
			self.board[self.prevX][self.prevY][0] = 0
			self.board[self.prevX][self.prevY][1] = 0
			self.addTilesNearZero(self.prevX, self.prevY)
		else:
			self.board[self.prevX][self.prevY][0] = number
			self.board[self.prevX][self.prevY][1] = number
			
			if ((self.prevX, self.prevY) not in self.numberedTiles):
				self.numberedTiles.append( (self.prevX, self.prevY) )						
				#Update effective label of neighbors of flags that have just been uncovered
				for key in self.flags:
					if (self.prevX, self.prevY) in self.flags[key]:
						if self.board[self.prevX][self.prevY][1] == '?':
							self.board[self.prevX][self.prevY][1] = number
						else:
							self.board[self.prevX][self.prevY][1] -= 1
					#If updated to '0', immediately add those to the frontier (it is effectively safe!)
					if self.board[self.prevX][self.prevY][1] == 0:
						self.addTilesNearZero(self.prevX, self.prevY)


	def effectiveLabeling(self, x, y):
		neighbors = [ (x, y+1), (x-1, y+1), (x-1, y), (x-1, y-1), (x, y-1), (x+1, y-1), (x+1, y), (x+1, y+1)]
		for tile in neighbors:
			if self.isInBounds(tile[0], tile[1]) and self.board[tile[0]][tile[1]][1] != 0 and self.board[tile[0]][tile[1]][1] != 'F':
				if self.board[tile[0]][tile[1]][0] == '?' and self.board[tile[0]][tile[1]][1] == '?':
					continue
				elif self.board[tile[0]][tile[1]][1] == '?':
					self.board[tile[0]][tile[1]][1] = self.board[tile[0]][tile[1]][0]-1
				else:
					self.board[tile[0]][tile[1]][1] -= 1
					
				if self.board[tile[0]][tile[1]][1] == 0:
						self.addTilesNearZero(tile[0], tile[1])


	#Check if neighbors of 1's are also 1's, and find out where bombs should be
	def flagBombs(self):
		########################################################################
		#   Corner Pattern [numbers don't matter as long as they are all >1]   #
		########################################################################
		#print("Checking 'Corner Patterns'", end = "")
		for (x, y) in self.numberedTiles:
			if (x-1, y) in self.numberedTiles and (x, y+1) in self.numberedTiles and (x-1,y+1) in self.remaining:
				return ( (x-1,y+1) )
			elif (x+1, y) in self.numberedTiles and (x, y+1) in self.numberedTiles and (x+1,y+1) in self.remaining:
				return ( (x+1,y+1) )
			elif (x+1, y) in self.numberedTiles and (x, y-1) in self.numberedTiles and (x+1,y-1) in self.remaining:
				return ( (x+1,y-1) )
			elif (x-1, y) in self.numberedTiles and (x, y-1) in self.numberedTiles and (x-1,y-1) in self.remaining:
				return ( (x-1,y-1) )

		###########################################################################
		#   1-2-1 Straight Line Pattern [only works for 1-2-1 effective labels]   #
		###########################################################################
		#print("Checking '1-2-1 Patterns'", end = "")
		for (x, y) in self.numberedTiles:
			centerValue = self.board[x][y][1]
			if centerValue != 2:
				continue
			#horizontal line of 3, bombs below the 1's
			if ( (x-1,y) in self.numberedTiles and (x+1,y) in self.numberedTiles
					and self.board[x+1][y][1] == 1 and self.board[x-1][y][1] == 1
					and (x-1,y-1) in self.remaining and (x,y-1) in self.remaining and (x+1,y-1) in self.remaining ):
				#print('bombs below')
				return ( [(x-1,y-1), (x+1,y-1)] )
			#horizontal line of 3, bombs above the 1's
			elif ( (x-1,y) in self.numberedTiles and (x+1,y) in self.numberedTiles
					and self.board[x+1][y][1] == 1 and self.board[x-1][y][1] == 1
					and (x-1,y+1) in self.remaining and (x,y+1) in self.remaining and (x+1, y+1) in self.remaining ):
				#print('bombs above')
				return ( [(x-1,y+1), (x+1,y+1)] )
			#vertical line of 3, neighbors to up and down, bombs to the left of the 1's
			elif ( (x,y+1) in self.numberedTiles and (x,y-1) in self.numberedTiles
					and self.board[x][y+1][1] == 1 and self.board[x][y-1][1] == 1
					and (x-1,y+1) in self.remaining and (x-1,y) in self.remaining and (x-1,y-1) in self.remaining ):
				#print('bombs to left')
				return ( [(x-1,y+1), (x-1,y-1)] )
			#vertical line of 3, neighbors to up and down, bombs to the right of the 1's
			elif ( (x,y+1) in self.numberedTiles and (x,y-1) in self.numberedTiles
					and self.board[x+1][y][1] == 1 and self.board[x-1][y][1] == 1
					and (x+1,y+1) in self.remaining and (x+1,y) in self.remaining and (x+1,y-1) in self.remaining ):
				#print('bombs to left')
				return ( [(x+1,y+1), (x+1,y-1)] )

		###############################################################################
		#	1-2-2-1 Straight Line Pattern [only works for 1-2-2-1 effective labels]	  #
		###############################################################################
		'''#print("Checking '1-2-2-1 Patterns'", end = "")
		for (x, y) in self.numberedTiles:
			centerBiases = list()
			#If the starting value is not 2, skip these coords
			centerValue = self.board[x][y][1] 
			if centerValue != 2:
				continue
			#Check horizontally, left of original (x,y)
			if self.board[x+1][y][1] == 2: 
				centerBiases.append("left")
			#Check horizontally, right of original (x,y)
			if self.board[x-1][y][1] == 2: 
				centerBiases.append("right")
			#Check vertically, above original (x,y)
			if self.board[x][y+1][1] == 2:
				centerBiases.append("above")
			#Check vertically, below original (x,y)
			if self.board[x][y-1][1] == 2:
				centerBiases.append("below")
			#If all fail, this tile is useless
			if len(centerBiases) == 0: 
				continue
			###############################################################################
			#Center bias is left -> (1-[2]-2-1)
			for centerBias in centerBiases:
				if centerBias == "left":
					if (x-1,y) in self.numberedTiles and (x+1,y) in self.numberedTiles and (x+2,y) in self.numberedTiles:
						if self.board[x-1][y][1] == 1 and self.board[x+1][y][1] == 2 and self.board[x+2][y][1] == 1:
							#horizontal line of 4, bombs below the 2's
							if (x-1,y-1) in self.remaining and (x,y-1) in self.remaining and (x+1,y-1) in self.remaining and (x+2,y-1) in self.remaining:
								return ( [(x,y-1), (x+1,y-1)] )
							#horizontal line of 4, bombs above the 2's
							elif (x-1,y+1) in self.remaining and (x,y+1) in self.remaining and (x+1,y+1) in self.remaining and (x+2,y+1) in self.remaining:
								return ( [(x,y+1), (x+1,y+1)] )
				###############################################################################
				#Center bias is right -> (1-2-[2]-1)
				elif centerBias == "right":
					if (x-2,y) in self.numberedTiles and (x-1,y) in self.numberedTiles and (x+1,y) in self.numberedTiles:
						if self.board[x-2][y][1] == 1 and self.board[x-1][y][1] == 2 and self.board[x+1][y][1] == 1:
							#horizontal line of 4, bombs below the 2's
							if (x,y-1) in self.remaining and (x-1,y-1) in self.remaining and (x-2,y-1) in self.remaining and (x+1,y-1) in self.remaining:
								return ( [(x,y-1), (x-1,y-1)] )
							#horizontal line of 4, bombs above the 2's
							elif (x,y+1) in self.remaining and (x-1,y+1) in self.remaining and (x-2,y+1) in self.remaining and (x+1,y+1) in self.remaining:
								return ( [(x,y+1), (x-1,y+1)] )
				###############################################################################
				#Center bias is above -> {top}(1-[2]-2-1){bottom}
				elif centerBias == "above":
					if (x,y+1) in self.numberedTiles and (x,y-1) in self.numberedTiles and (x,y-2) in self.numberedTiles:
						if self.board[x][y+1][1] == 1 and self.board[x][y-1][1] == 2 and self.board[x][y-2][1] == 1:
							#vertical line of 4, bombs left of 2's
							if (x-1,y+1) in self.remaining and (x-1,y) in self.remaining and (x-1,y-1) in self.remaining and (x-1,y-2) in self.remaining:
								return ( [(x-1,y), (x-1,y-1)] )
							#vertical line of 4, bombs right of 2's
							elif (x+1,y+1) in self.remaining and (x+1,y) in self.remaining and (x+1,y-1) in self.remaining and (x+1,y-2) in self.remaining:
								return ( [(x+1,y), (x+1,y-1)] )
				###############################################################################
				#Center bias is below -> {top}(1-2-[2]-1){bottom}
				elif centerBias == "below":
					if (x,y+2) in self.numberedTiles and (x,y+1) in self.numberedTiles and (x,y-1) in self.numberedTiles:
						if self.board[x][y+2][1] == 1 and self.board[x][y+1][1] == 2 and self.board[x][y-1][1] == 1:
							#vertical line of 4, bombs left of 2's
							if (x-1,y-1) in self.remaining and (x-1,y) in self.remaining and (x-1,y+1) in self.remaining and (x-1,y+2) in self.remaining:
								return ( [(x-1,y), (x-1,y+1)] )
							#vertical line of 4, bombs right of 2's
							if (x+1,y-1) in self.remaining and (x+1,y) in self.remaining and (x+1,y+1) in self.remaining and (x+1,y+2) in self.remaining:
								return ( [(x+1,y), (x+1,y+1)] )'''


	##############################


	#For when the AI has no idea what to do next. Use as last resort.
	def chooseRandomTile(self):
		#print('remaining =', self.remaining)
		coords = random.choice(self.remaining)
		#print('randomly chose =', coords)
		return coords

	def printAIBoard(self):
		for row in reversed(range(len(self.board[0]))):
			for col in range(len(self.board)):
				print(str(self.board[col][row][0]) + "|" + str(self.board[col][row][1]), end = "  ")
			print()
		print('\n-------------------------\n')

	def isInBounds(self, x, y):
		if x < 0 or x > self.colDimension-1 or y < 0 or y > self.rowDimension-1:
			return False
		else:
			return True

	def isBoardComplete(self):
		for row in self.board:
			for col in row:
				if col[0] == '?':
					return False
		return True

	########################################################################
	#							YOUR CODE ENDS							   #
	########################################################################
