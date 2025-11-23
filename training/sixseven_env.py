import gymnasium as gym
from gymnasium import spaces
import numpy as np

from game import ADDITION, MULTIPLICATION, SPACE, SUBTRACTION, Game

# scaled down by 1000
LOWER_BOUND = -1
UPPER_BOUND = 1

class SixSevenEnv(gym.Env):
    """
    Gymnasium environment wrapper for the 67 game.

    The agent receives the game grid as observation and selects moves (up, down, left, right).
    Rewards are given for:
    - Winning the game (reaching 67)
    - Each valid move that changes the board state
    - Penalty for invalid moves
    """

    def __init__(self, num_rows: int = 6, num_cols: int = 7):
        """
        Initialize the environment.

        Args:
            num_rows: Number of rows in the game grid
            num_cols: Number of columns in the game grid
        """
        super().__init__()

        self.num_rows = num_rows
        self.num_cols = num_cols
        self.game = Game(num_rows, num_cols)

        # Action space: 0=up, 1=down, 2=left, 3=right
        self.action_space = spaces.Discrete(4)

        # Observation space: Grid represented as a flattened array of encoded values
        # We'll encode: empty="", digits 0-9, operators +/-/* as unique integer values
        # Empty: 0, Digits 0-9: 1-10, Operators +: 11, -: 12, *: 13
        self.observation_space = spaces.Box(
            low=LOWER_BOUND, high=UPPER_BOUND, shape=(num_rows * num_cols * 5,), dtype=np.float32
        )

        self.action_map = {0: "up", 1: "down", 2: "left", 3: "right"}
        self.steps = 0
        self.max_steps = 1000  # Maximum steps per episode

        self.current_min_dist = 1000.0

    def _encode_cell(self, cell_value: int) -> list[float]:
        """Stores 5 values: cell value if number, else one-hot for +,-,* or space"""
        if cell_value == SPACE:
            return [0, 1, 0, 0, 0]
        elif cell_value == ADDITION:
            return [0, 0, 1, 0, 0]
        elif cell_value == SUBTRACTION:
            return [0, 0, 0, 1, 0]
        elif cell_value == MULTIPLICATION:
            return [0, 0, 0, 0, 1]
        else:  # digit 0-9
            return [cell_value / 1000, 0, 0, 0, 0]

    def _get_observation(self, grid: list[list[str]] = None) -> np.ndarray:
        """Convert game grid to observation array."""
        if grid is None:    # allows for conversion of arbitrary grid
            grid = self.game._grid

        # Flatten and encode in one pass using list comprehension
        encoded = [encoded_val
                   for row in grid
                   for cell in row
                   for encoded_val in self._encode_cell(cell)]

        return np.array(encoded, dtype=np.float32)

    def _get_info(self):
        """Get info dictionary."""
        return {
            "valid_moves": self.game.get_valid_moves(),
            "steps": self.steps,
        }

    def reset(self, seed=None, options=None):
        """
        Reset the environment to initial state.
        Returns:
            observation: Initial observation
            info: Info dictionary
        """
        super().reset(seed=seed)
        self.game = Game(self.num_rows, self.num_cols)
        self.game.generate_tiles()
        self.steps = 0
        
        # OPTIMIZATION: Initialize the cache
        self.current_min_dist = self._calculate_min_distance()

        observation = self._get_observation()
        info = self._get_info()
        info["win"] = 0
        return observation, info

    def _calculate_min_distance(self) -> float:
        """
        Optimized scanner:
        1. Flattens grid using list comprehension (faster than nested for-loops).
        2. Uses integer comparison (<= 1000) to filter out Operators/Spaces instantly.
        """
        # Extract only valid numbers (ignore operators 1001+ and SPACE 1004)
        numbers = [
            cell for row in self.game._grid 
            for cell in row 
            if cell <= 1000
        ]
        
        if not numbers:
            return 1000.0 # Default penalty if board is empty (rare)
            
        # Find min distance to 67
        return min(abs(n - 67) for n in numbers)

    def step(self, action):
        self.steps += 1
        
        # 1. Use Cached State (No calculation needed here!)
        prev_dist = self.current_min_dist
        
        valid_moves = self.game.get_valid_moves()
        move_name = self.action_map[action]

        reward = 0.0
        
        if move_name not in valid_moves:
            reward = -5.0 
            # Optional: Terminate on invalid move to speed up training significantly
            # return self._get_observation(), reward, True, False, self._get_info()
        else:
            # Execute move
            if move_name == "up": self.game.slide_up()
            elif move_name == "down": self.game.slide_down()
            elif move_name == "left": self.game.slide_left()
            else: self.game.slide_right()

            self.game.generate_tiles()
            
            # 2. Calculate New State ONCE
            curr_dist = self._calculate_min_distance()
            
            # Update Cache for the next step
            self.current_min_dist = curr_dist

            # Shaping Reward: Positive if we got closer, negative if further
            # Scale by 0.1 (e.g., 10 units closer = +1.0 reward)
            reward += (prev_dist - curr_dist) * 0.1

            # Living Reward (Encourage keeping empty spaces)
            # Use cached blank_spaces count instead of counting cells
            empty_spaces = len(self.game._blank_spaces)
            reward += empty_spaces * 0.01

        # 3. Check Terminal States
        terminated = False
        truncated = False
        info = self._get_info()
        info["win"] = 0

        if self.game.is_won():
            reward += 100.0
            info["win"] = 1
            terminated = True
        elif self.game.is_lost(valid_moves):
            reward -= 50.0
            terminated = True
        elif self.steps >= self.max_steps:
            truncated = True

        return self._get_observation(), reward, terminated, truncated, info

    def render(self):
        """Render the current game state."""
        print(self.game)

    def close(self):
        """Clean up resources."""
        pass


if __name__ == "__main__":
    import time
    env = SixSevenEnv()

    obs = env.reset()
    start = time.time()
    for i in range(5000):
        obs, r, done, truncated, info = env.step(env.action_space.sample())
        if done:
            obs = env.reset()

    print("5000 steps took:", time.time() - start, "seconds")

    exit()
    # Test the environment
    env = SixSevenEnv()
    obs, info = env.reset()
    print("Initial observation shape:", obs.shape)
    print("Valid moves:", info["valid_moves"])

    total_reward = 0.0

    # Run a few random steps - don't render during training loops for performance
    for step_num in range(10000):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        total_reward += reward

        # Only print every 1000 steps or on episode end to avoid slowdown
        print(f"Step {step_num}: Action: {env.action_map[action]}, Reward: {reward:.2f}")

        if terminated or truncated:
            print(f"Episode ended at step {step_num}")
            break

    print("Total reward: ", reward)