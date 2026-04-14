import pygame
from game_manager import GameManager


def main():
    pygame.init()
    game = GameManager()

    while game.running:
        game.run()

    pygame.quit()



if __name__ == "__main__":
    main()