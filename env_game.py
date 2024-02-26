import random
import sys
import re
import warnings
import cv2
import numpy as np
import pygame
from gymnasium.spaces import Discrete
import pygame.camera
import os

warnings.filterwarnings("ignore")

agent_png = 'images_for_render/supermario.png'
enemy_png = 'images_for_render/bowser.png'
wall_png = 'images_for_render/wall.png'
goal_png = 'images_for_render/goal.png'


class CustomEnv:

    def __init__(self, rows, cols, n_agents, n_act_agents, n_enemies, n_act_enemies, n_goals, if_maze,
                 if_same_enemies_actions, dir_saving, game_n, seed_value, predefined_env):

        np.random.seed(seed_value)
        random.seed(seed_value)

        if predefined_env is None:

            self.rows = rows
            self.cols = cols
            self.n_agents = n_agents
            self.n_act_agents = n_act_agents
            self.n_enemies = n_enemies
            self.n_act_enemies = n_act_enemies
            self.n_goals = n_goals
            self.n_walls = rows * 2

            self.dir_saving = dir_saving
            self.game_n = game_n

            # reward definition
            self.reward_alive = 0
            self.reward_winner = 1
            self.reward_loser = -1

            self.n_times_loser = 0

            #  game episode
            self.len_actions_enemies = 50
            self.n_steps_enemies_actions = 0

            # grid for visualize agents and enemies positions
            self.grid_for_game = []
            # list for saving enemies positions
            self.pos_enemies = []
            self.pos_enemies_for_reset = []
            # list for saving agents positions
            self.pos_agents = []
            self.pos_agents_for_reset = []
            # goal's position
            self.pos_goals = []

            # action space of agents
            self.action_space = Discrete(self.n_act_agents, start=0)

            # defining empty matrices for game
            for ind_row in range(self.rows):
                row = []
                for ind_col in range(self.cols):
                    row.append('-')
                self.grid_for_game.append(row)

            self.observation_space = rows * cols

            # positioning agents
            row_pos_agents = []
            for agent in range(1, self.n_agents + 1, 1):
                # check if same position than enemies
                do = True
                while do:
                    x_agent = random.randint(0, self.rows - 1)
                    y_agent = random.randint(0, self.cols - 1)
                    if [x_agent, y_agent] not in self.pos_agents_for_reset:
                        do = False
                self.grid_for_game[x_agent][y_agent] = 'Agent' + str(agent)
                row_pos_agents.append([x_agent, y_agent])
                self.pos_agents_for_reset.append([x_agent, y_agent])
            self.pos_agents.append(row_pos_agents)

            # positioning goal
            for goal in range(1, self.n_goals + 1, 1):
                # check if same position than enemies and agents
                do = True
                while do:
                    x_goal = random.randint(0, self.rows - 1)
                    y_goal = random.randint(0, self.cols - 1)
                    if [x_goal, y_goal] not in self.pos_agents[0]:
                        do = False
                self.grid_for_game[x_goal][y_goal] = 'Goal' + str(goal)
                self.pos_goals.append([x_goal, y_goal])

            self.walls = []
            if if_maze:
                self.define_maze()

            # positioning enemies
            row_pos_enemies = []
            for enemy in range(1, self.n_enemies + 1, 1):
                # check if same position
                do = True
                while do:
                    x_nem = random.randint(0, self.rows - 1)
                    y_nem = random.randint(0, self.cols - 1)
                    if [x_nem, y_nem] not in self.pos_agents_for_reset and [x_nem, y_nem] not in self.pos_goals and [x_nem, y_nem] not in self.walls:
                        do = False
                self.grid_for_game[x_nem][y_nem] = 'En' + str(enemy)
                row_pos_enemies.append([x_nem, y_nem])
                self.pos_enemies_for_reset.append([x_nem, y_nem])
                # self.pos_enemies.append([x_nem, y_nem])
            self.pos_enemies.append(row_pos_enemies)

            self.if_same_enemies_actions = if_same_enemies_actions
            if self.if_same_enemies_actions:
                self.list_enemies_actions = []
                for enemy in range(0, self.n_enemies, 1):
                    enemy_actions = []
                    for act in range(self.len_actions_enemies):
                        enemy_actions.append(random.randint(0, self.n_act_enemies - 1))
                    self.list_enemies_actions.append(enemy_actions)

            self.reset_enemies_attached = [[False] * self.n_enemies] * self.n_agents

            self.reset_enemies_nearby = []
            for agent in range(0, self.n_agents, 1):
                single_agent = []
                for enemy in range(0, self.n_enemies, 1):
                    x_ag = self.pos_agents[0][agent][0]
                    y_ag = self.pos_agents[0][agent][1]
                    x_en = self.pos_enemies[0][enemy][0]
                    y_en = self.pos_enemies[0][enemy][1]
                    single_agent.append(self.get_direction(x_ag, y_ag, x_en, y_en))
                self.reset_enemies_nearby.append(single_agent)

            for ind in range(len(self.grid_for_game)):
                print(self.grid_for_game[ind])

            # print('INIT)', self.pos_agents_for_reset, self.pos_enemies_for_reset)
        else:

            string_goal = 'Goal'
            string_agent = 'Agent'
            string_enemy = 'En'

            rows = len(predefined_env)
            cols = len(predefined_env[0])

            self.n_agents = 0
            self.n_enemies = 0
            self.n_goals = 0

            for i, row in enumerate(predefined_env):
                for j, value in enumerate(row):
                    if string_goal in value:
                        self.n_goals += 1
                    if string_enemy in value:
                        self.n_enemies += 1
                    if string_agent in value:
                        self.n_agents += 1

            self.rows = rows
            self.cols = cols
            self.n_act_agents = n_act_agents
            self.n_act_enemies = n_act_enemies
            self.n_walls = rows * 2

            self.dir_saving = dir_saving
            self.game_n = game_n

            # reward definition
            self.reward_alive = 0
            self.reward_winner = 1
            self.reward_loser = -1

            self.n_times_loser = 0

            #  game episode
            self.len_actions_enemies = 50
            self.n_steps_enemies_actions = 0

            # grid for visualize agents and enemies positions
            self.grid_for_game = []
            # list for saving enemies positions
            self.pos_enemies = []
            self.pos_enemies_for_reset = []
            # list for saving agents positions
            self.pos_agents = []
            self.pos_agents_for_reset = []
            # goal's position
            self.pos_goals = []

            # action space of agents
            self.action_space = Discrete(self.n_act_agents, start=0)

            # defining empty matrices for game
            for ind_row in range(self.rows):
                row = []
                for ind_col in range(self.cols):
                    row.append('-')
                self.grid_for_game.append(row)

            self.observation_space = rows * cols

            # positioning agents and goals
            row_pos_agents = []
            for i, row in enumerate(predefined_env):
                for j, value in enumerate(row):
                    if string_goal in value:
                        self.pos_goals.append([i, j])
                        self.grid_for_game[i][j] = value
                    if string_agent in value:
                        self.pos_agents_for_reset.append([i, j])
                        row_pos_agents.append([i, j])
                        self.grid_for_game[i][j] = value
            self.pos_agents.append(row_pos_agents)

            self.walls = []
            if if_maze:
                self.define_maze()

            # positioning enemies
            row_pos_enemies = []
            for enemy in range(1, self.n_enemies + 1, 1):
                # check if same position
                do = True
                while do:
                    x_nem = random.randint(0, self.rows - 1)
                    y_nem = random.randint(0, self.cols - 1)
                    if [x_nem, y_nem] not in self.pos_agents_for_reset and [x_nem, y_nem] not in self.pos_goals and [x_nem, y_nem] not in self.walls:
                        do = False
                self.grid_for_game[x_nem][y_nem] = 'En' + str(enemy)
                row_pos_enemies.append([x_nem, y_nem])
                self.pos_enemies_for_reset.append([x_nem, y_nem])
                # self.pos_enemies.append([x_nem, y_nem])
            self.pos_enemies.append(row_pos_enemies)

            self.if_same_enemies_actions = if_same_enemies_actions
            if self.if_same_enemies_actions:
                self.list_enemies_actions = []
                for enemy in range(0, self.n_enemies, 1):
                    enemy_actions = []
                    for act in range(self.len_actions_enemies):
                        enemy_actions.append(random.randint(0, self.n_act_enemies - 1))
                    self.list_enemies_actions.append(enemy_actions)

            self.reset_enemies_attached = [[False] * self.n_enemies] * self.n_agents

            self.reset_enemies_nearby = []
            for agent in range(0, self.n_agents, 1):
                single_agent = []
                for enemy in range(0, self.n_enemies, 1):
                    x_ag = self.pos_agents[0][agent][0]
                    y_ag = self.pos_agents[0][agent][1]
                    x_en = self.pos_enemies[0][enemy][0]
                    y_en = self.pos_enemies[0][enemy][1]
                    single_agent.append(self.get_direction(x_ag, y_ag, x_en, y_en))
                self.reset_enemies_nearby.append(single_agent)

            for ind in range(len(self.grid_for_game)):
                print(self.grid_for_game[ind])

    def define_maze(self):

        value_wall = -1

        def generate_random_path(grid_size, agent_position, goal_position):
            rows, cols = grid_size
            agent_row, agent_col = agent_position[0]  # DO IT BETTER
            goal_row, goal_col = goal_position[0]  # DO IT BETTER

            # Initialize the grid with all cells marked as unvisited
            grid = [[0] * cols for _ in range(rows)]

            # Initialize the path with the starting position
            path = [(agent_row, agent_col)]

            while path[-1] != (goal_row, goal_col):
                current_row, current_col = path[-1]
                neighbors = []

                # Check neighboring cells
                if current_row > 0 and grid[current_row - 1][current_col] == 0:
                    neighbors.append((current_row - 1, current_col))
                if current_row < rows - 1 and grid[current_row + 1][current_col] == 0:
                    neighbors.append((current_row + 1, current_col))
                if current_col > 0 and grid[current_row][current_col - 1] == 0:
                    neighbors.append((current_row, current_col - 1))
                if current_col < cols - 1 and grid[current_row][current_col + 1] == 0:
                    neighbors.append((current_row, current_col + 1))

                if neighbors:
                    # Randomly choose a neighboring cell
                    next_cell = random.choice(neighbors)
                    path.append(next_cell)

                    # Mark the chosen cell as visited
                    grid[next_cell[0]][next_cell[1]] = 1
                else:
                    # If no neighbors are available, backtrack
                    path.pop()

            return grid, path

        def generate_random_path_with_given_walls(grid_size, agents_position, goals_positions, num_walls,
                                                  max_attempts=20):

            for _ in range(max_attempts):
                grid, path = generate_random_path(grid_size, agents_position, goals_positions)
                if grid is not None:
                    wall_positions = set()

                    # Attempt to insert walls randomly, avoiding the path, agent, and goal
                    wall_attempts = 0
                    while not len(wall_positions) == num_walls and not wall_attempts >= num_walls * 100:
                        wall_row, wall_col = random.randint(0, grid_size[0] - 1), random.randint(0,
                                                                                                 grid_size[1] - 1)

                        if (wall_row, wall_col) not in path and (wall_row, wall_col) not in agents_position and (
                                wall_row, wall_col) not in goals_positions and (
                                wall_row, wall_col) not in wall_positions and \
                                grid[wall_row][
                                    wall_col] != -1:
                            grid[wall_row][wall_col] = value_wall  # Mark cell as a wall
                            wall_positions.add((wall_row, wall_col))
                            wall_attempts = 0  # Reset the counter after a successful wall placement
                        else:
                            wall_attempts += 1

                    if sum(row.count(-1) for row in grid) == num_walls:

                        for i, row in enumerate(grid):
                            for j, value in enumerate(row):
                                if value == value_wall:
                                    self.grid_for_game[i][j] = 'W'
                                    self.walls.append([i, j])

                        return 0

        generate_random_path_with_given_walls((self.rows, self.cols), self.pos_agents_for_reset, self.pos_goals,
                                              self.n_walls)

    def step_enemies(self):
        new_enemies_pos = []
        for enemy in range(1, self.n_enemies + 1, 1):
            last_stateX_en = self.pos_enemies[-1][enemy - 1][0]
            last_stateY_en = self.pos_enemies[-1][enemy - 1][1]

            if self.if_same_enemies_actions:
                n_steps = len(self.pos_enemies)
                if n_steps < self.len_actions_enemies:
                    n = int(n_steps)
                else:
                    n = int(n_steps - self.len_actions_enemies * (int(n_steps / self.len_actions_enemies)))

                action = self.list_enemies_actions[enemy - 1][n]
            else:
                action = random.randint(0, self.n_act_enemies - 1)

            new_stateX_en, new_stateY_en, _, _, _ = self.get_action(action, last_stateX_en, last_stateY_en,
                                                                    self.grid_for_game)
            # print('enemy pos: ', [new_stateX_en, new_stateY_en])

            if (abs(new_stateX_en - last_stateX_en) + abs(
                    new_stateY_en - last_stateY_en)) > 1 and self.n_act_enemies < 5:
                print('Enemy wrong movement', [last_stateX_en, last_stateY_en], '-', [new_stateX_en, new_stateY_en])

            new_enemies_pos.append([new_stateX_en, new_stateY_en])

        self.pos_enemies.append(new_enemies_pos)

    def get_nearbies_agent(self):
        enemies_nearby = []
        goals_nearby = []

        for agent in range(1, self.n_agents + 1, 1):
            x_ag = self.pos_agents[-1][agent - 1][0]
            y_ag = self.pos_agents[-1][agent - 1][1]
            single_agent_enemies = []
            for enemy in range(1, self.n_enemies + 1, 1):
                x_en = self.pos_enemies[-1][enemy - 1][0]
                y_en = self.pos_enemies[-1][enemy - 1][1]
                direction_nearby_enemy = self.get_direction(x_ag, y_ag, x_en, y_en)
                single_agent_enemies.append(direction_nearby_enemy)

            enemies_nearby.append(single_agent_enemies)

            single_agent_goals = []
            for goal in range(1, self.n_goals + 1, 1):
                x_goal = self.pos_goals[goal - 1][0]
                y_goal = self.pos_goals[goal - 1][1]
                direction_nearby_goal = self.get_direction(x_ag, y_ag, x_goal, y_goal)
                single_agent_goals.append(direction_nearby_goal)

            goals_nearby.append(single_agent_goals)

        """if np.mean(enemies_nearby[0]) != 50 or np.mean(goals_nearby[0]) != 50:
            print(f'\nAgent pos: {self.pos_agents[-1]}')
            print(f'Enemies pos: {self.pos_enemies[-1]}')
            print(f'Goal pos: {self.pos_goals[0]}')
            print(f'Nearby goals: {goals_nearby}')
            print(f'Nearby enemies: {enemies_nearby}')"""

        return enemies_nearby, goals_nearby

    def step_agent(self, agent_action):
        new_agents_pos = []
        for agent in range(1, self.n_agents + 1, 1):
            last_stateX_ag = self.pos_agents[-1][agent - 1][0]
            last_stateY_ag = self.pos_agents[-1][agent - 1][1]

            new_stateX_ag, new_stateY_ag, res_action, _, _ = self.get_action(agent_action, last_stateX_ag,
                                                                             last_stateY_ag,
                                                                             self.grid_for_game)
            # print('ag inside', [last_stateX_ag, last_stateY_ag], [new_stateX_ag, new_stateY_ag])

            if (abs(new_stateX_ag - last_stateX_ag) + abs(
                    new_stateY_ag - last_stateY_ag)) > 1 and self.n_act_agents < 5:
                print('Agent wrong movement', [last_stateX_ag, last_stateY_ag], '-', [new_stateX_ag, new_stateY_ag],
                      agent_action)

            new_agents_pos.append([new_stateX_ag, new_stateY_ag])

        self.pos_agents.append(new_agents_pos)

        return new_agents_pos

    def check_winner_gameover_agent(self, new_stateX_ag, new_stateY_ag):
        rewards = []
        dones = []
        # check if agent wins
        if_win = False
        if_lose = False
        for goal in self.pos_goals:
            goal_x = goal[0]
            goal_y = goal[1]
            if new_stateX_ag == goal_x and new_stateY_ag == goal_y:
                reward = self.reward_winner
                done = True
                if_win = True
                # print('winner', goal, [new_stateX_ag, new_stateY_ag])
        # check if agent loses
        if not if_win:
            for enemy in range(0, self.n_enemies, 1):
                X_en = self.pos_enemies[-1][enemy][0]
                Y_en = self.pos_enemies[-1][enemy][1]
                if new_stateX_ag == X_en and new_stateY_ag == Y_en:
                    reward = self.reward_loser
                    if_lose = True
                    self.n_times_loser += 1
                    done = False
                    self.n_steps_enemies_actions = 0
                    #  print(f'Loser) En: {[X_en, Y_en]}, Ag before: {self.pos_agents[-1]}, Ag after: {[new_stateX_ag, new_stateY_ag]}')
            # otherwise agent is alive
            if not if_lose:
                # print('alive')
                reward = self.reward_alive
                done = False

        rewards.append(reward)
        dones.append(done)

        return rewards, dones, if_lose

    def reset(self, reset_n_times_loser):
        x, y = self.pos_agents_for_reset, self.pos_enemies_for_reset
        if reset_n_times_loser:
            self.n_times_loser = 0

        # reset agents' states
        reset_rewards = [0] * self.n_agents
        reset_dones = [False] * self.n_agents

        self.pos_agents = []
        self.pos_agents.append(self.pos_agents_for_reset.copy())

        self.pos_enemies = []
        self.pos_enemies.append(self.pos_enemies_for_reset)

        if x != self.pos_agents_for_reset or y != self.pos_enemies_for_reset:
            print(x, y, '---', self.pos_agents_for_reset, self.pos_enemies_for_reset)

        return self.pos_agents_for_reset.copy(), reset_rewards, reset_dones, self.reset_enemies_nearby.copy(), self.reset_enemies_attached.copy()

    def get_direction(self, x_ag, y_ag, x_en, y_en):
        deltaX = x_en - x_ag
        deltaY = y_en - y_ag

        direction_ag_en = -1

        if deltaX == 0 and deltaY == 0:  # stop
            direction_ag_en = 0
        elif deltaX == 1 and deltaY == 0:  # right
            direction_ag_en = 1
        elif deltaX == -1 and deltaY == 0:  # left
            direction_ag_en = 2
        elif deltaX == 0 and deltaY == 1:  # up
            direction_ag_en = 3
        elif deltaX == 0 and deltaY == -1:  # down
            direction_ag_en = 4
        elif deltaX == 1 and deltaY == 1 and self.n_act_agents > 5:  # diag up right
            direction_ag_en = 5
        elif deltaX == 1 and deltaY == -1 and self.n_act_agents > 5:  # diag down right
            direction_ag_en = 6
        elif deltaX == -1 and deltaY == 1 and self.n_act_agents > 5:  # diag up left
            direction_ag_en = 7
        elif deltaX == -1 and deltaY == -1 and self.n_act_agents > 5:  # diag down left
            direction_ag_en = 8
        else:  # otherwise
            direction_ag_en = 50

        # print([x_ag, y_ag], [x_en, y_en], direction_ag_en)

        return direction_ag_en

    def get_action(self, action, last_stateX, last_stateY, grid):

        if action == 0:  # stop
            new_stateX = last_stateX
            new_stateY = last_stateY
            actionX = 0
            actionY = 0
        elif action == 1:  # right
            sub_action = 1
            if 0 <= sub_action + last_stateX < self.cols:
                new_stateX = sub_action + last_stateX
                actionX = sub_action
            else:
                new_stateX = last_stateX
                actionX = 0
                action = 0
            new_stateY = last_stateY
            actionY = 0
        elif action == 2:  # left
            sub_action = -1
            if 0 <= sub_action + last_stateX < self.cols:
                new_stateX = sub_action + last_stateX
                actionX = sub_action
            else:
                new_stateX = last_stateX
                actionX = 0
                action = 0
            new_stateY = last_stateY
            actionY = 0
        elif action == 3:  # up
            new_stateX = last_stateX
            actionX = 0
            sub_action = 1
            if 0 <= sub_action + last_stateY < self.rows:
                new_stateY = sub_action + last_stateY
                actionY = sub_action
            else:
                new_stateY = last_stateY
                actionY = 0
                action = 0
        elif action == 4:  # down
            new_stateX = last_stateX
            actionX = 0
            sub_action = -1
            if 0 <= sub_action + last_stateY < self.rows:
                new_stateY = sub_action + last_stateY
                actionY = sub_action
            else:
                new_stateY = last_stateY
                actionY = 0
                action = 0

        if grid[new_stateX][new_stateY] == 'W':
            # print('in) wall', [last_stateX, last_stateY], [new_stateX, new_stateY])
            new_stateX = last_stateX
            new_stateY = last_stateY
            action = 0
            actionX = 0
            actionY = 0
            # print('out) wall',[new_stateX, new_stateY])

        return new_stateX, new_stateY, action, actionX, actionY

    def init_gui(self, algorithm, ep):

        pygame.font.init()

        self.episode = ep
        self.algorithm = algorithm

        self.delay_visualization = 5

        self.n_defeats_start = self.n_times_loser

        self.font_size = 20
        self.FONT = pygame.font.SysFont('comicsans', self.font_size)

        fix_size_width = 900
        fix_size_height = 750
        WIDTH, HEIGHT = fix_size_width - self.font_size * 2, fix_size_height - self.font_size * 2
        self.WINDOW = pygame.display.set_mode((fix_size_width, fix_size_height))
        pygame.display.set_caption('Game')

        self.width_im = int(WIDTH / self.cols)
        self.height_im = int(HEIGHT / self.rows)
        self.new_sizes = (self.width_im, self.height_im)

        self.pics_agents = []
        for _ in range(self.n_agents):
            self.pics_agents.append(pygame.transform.scale(pygame.image.load(agent_png), self.new_sizes))
        self.pics_enemies = []
        for _ in range(self.n_enemies):
            self.pics_enemies.append(pygame.transform.scale(pygame.image.load(enemy_png), self.new_sizes))
        self.pics_walls = []
        for _ in range(len(self.walls)):
            self.pics_walls.append(pygame.transform.scale(pygame.image.load(wall_png), self.new_sizes))
        self.pics_goals = []
        for _ in range(len(self.pos_goals)):
            self.pics_goals.append(pygame.transform.scale(pygame.image.load(goal_png), self.new_sizes))

        components = self.dir_saving.split("/")
        numerical_part = components[0].split("_")[-1]
        components[0] = "Video_" + numerical_part
        self.dir_saving_video = "/".join(components)
        os.makedirs(self.dir_saving_video, exist_ok=True)
        self.path_output_video = f'{self.dir_saving_video}/video_{self.algorithm}_episode{self.episode}_game{self.game_n}.mp4'
        self.count_img = 0

        """
        self.WINDOW.fill('black')

        for agent in range(self.n_agents):
            self.WINDOW.blit(self.pics_agents[agent], (self.pre_ag_coord[agent][1] * self.width_im,
                                                       self.pre_ag_coord[agent][
                                                           0] * self.height_im + self.font_size * 2))
        for enemy in range(self.n_enemies):
            self.WINDOW.blit(self.pics_enemies[enemy], (self.pre_en_coord[enemy][1] * self.width_im,
                                                        self.pre_en_coord[enemy][
                                                            0] * self.height_im + self.font_size * 2))
        for wall in range(len(self.walls_coord)):
            self.WINDOW.blit(self.pics_walls[wall], (
                self.walls_coord[wall][1] * self.width_im,
                self.walls_coord[wall][0] * self.height_im + self.font_size * 2))
        for goal in range(len(self.goals_coord)):
            self.WINDOW.blit(self.pics_goals[goal], (
                self.goals_coord[goal][1] * self.width_im,
                self.goals_coord[goal][0] * self.height_im + self.font_size * 2))
        time_text = self.FONT.render(f'', True, 'white')
        self.WINDOW.blit(time_text, (10, 10))
        pygame.display.update()
        pygame.time.delay(self.delay_visualization)
        """

    def movement_gui(self, n_episodes, step_for_episode):

        new_ag_coord = self.pos_agents[-1].copy()
        new_en_coord = self.pos_enemies[-1].copy()

        self.WINDOW.fill('black')

        for agent in range(self.n_agents):
            self.WINDOW.blit(self.pics_agents[agent], (new_ag_coord[agent][1] * self.width_im,
                                                       new_ag_coord[agent][
                                                           0] * self.height_im + self.font_size * 2))

        for enemy in range(self.n_enemies):
            self.WINDOW.blit(self.pics_enemies[enemy], (new_en_coord[enemy][1] * self.width_im,
                                                        new_en_coord[enemy][
                                                            0] * self.height_im + self.font_size * 2))

        for wall in range(len(self.walls)):
            self.WINDOW.blit(self.pics_walls[wall], (
                self.walls[wall][1] * self.width_im,
                self.walls[wall][0] * self.height_im + self.font_size * 2))

        for goal in range(len(self.pos_goals)):
            self.WINDOW.blit(self.pics_goals[goal], (
                self.pos_goals[goal][1] * self.width_im,
                self.pos_goals[goal][0] * self.height_im + self.font_size * 2))

        time_text = self.FONT.render(
            f'Episode: {self.episode}/{n_episodes} - Algorithm: {self.algorithm} - #Defeats: {self.n_times_loser - self.n_defeats_start} - '
            f'#Actions: {step_for_episode}',
            True, 'white')
        self.WINDOW.blit(time_text, (10, 10))
        pygame.display.update()
        pygame.time.delay(self.delay_visualization)

        # Capture the current Pygame screen and convert it to a NumPy array
        pygame_image = cv2.cvtColor(pygame.surfarray.array3d(pygame.display.get_surface()), cv2.COLOR_RGB2BGR)
        pygame_image = cv2.rotate(pygame_image, cv2.ROTATE_90_CLOCKWISE)
        pygame_image = cv2.flip(pygame_image, 1)

        cv2.imwrite(
            f'{self.dir_saving_video}/im{self.count_img}_{self.algorithm}_{self.episode}episode_game{self.game_n}.jpeg',
            pygame_image)

        self.count_img += 1

    def save_video(self):

        def sort_key(filename):
            # Extract the numeric part from the filename using regular expression
            numeric_part = re.search(r'\d+', filename).group()
            # Convert the extracted numeric part to an integer for sorting
            return int(numeric_part)

        # Set the path to the directory containing your images
        image_folder = self.dir_saving_video

        # Set the output video file path
        output_path = self.path_output_video

        # Set the frame rate (frames per second) for the video
        fps = 2

        # Get the list of image filenames in the specified folder
        image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])

        # Check if there are any images in the folder
        if not image_files:
            print("No image files found in the specified folder.")
            exit()

        # Get the dimensions of the first image to determine the video resolution
        first_image_path = os.path.join(image_folder, image_files[0])
        img = cv2.imread(first_image_path)
        height, width, _ = img.shape

        # Create a VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # You can use other codecs like 'XVID' or 'H264'
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        image_files = sorted(image_files, key=sort_key)

        # Write each image to the video file
        for image_file in image_files:
            image_path = os.path.join(image_folder, image_file)
            img = cv2.imread(image_path)

            # Ensure the image was read successfully
            if img is not None:
                out.write(img)
                os.remove(image_path)
            else:
                print(f"Failed to read image: {image_path}")

        # Release the VideoWriter object
        out.release()

        # print(f"Video created and saved to: {os.path.abspath(output_path)}")