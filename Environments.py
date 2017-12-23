import numpy as np

class Environment(object):
    def __init__(self, N_ACTIONS, N_PLAYERS, EPISODE_LENGTH,
            multiplier = 2, punishment_cost = 0.2, punishment_strength = 1):
        self.n_actions = N_ACTIONS
        self.n_players = N_PLAYERS
        self.episode_length = EPISODE_LENGTH
        self.step_ctr = 0
        self.ep_ctr = 0
        self.avg_rewards_per_round = []

    def step(self, actions):
        self.update_state(actions)
        rewards = self.calculate_payoffs(actions)
        self.stored_rewards[:,self.step_ctr] = rewards
        self.step_ctr += 1
        return self.state_to_observation(), rewards, self.is_done()

    def reset(self):
        self.s = self.initial_state()
        self.step_ctr = 0
        self.stored_rewards = np.zeros((self.n_players,self.episode_length))
        self.ep_ctr += 1
        return self.state_to_observation()

    def reset_ep_ctr(self):
        self.ep_ctr = 0

    def state_to_observation(self):
        return self.s

    def is_done(self):
        if self.step_ctr >= self.episode_length:
            self.avg_rewards_per_round.append(np.mean(self.stored_rewards,axis=1))
            return True
        else:
            return False

    def get_avg_rewards_per_round(self):
        return np.asarray(self.avg_rewards_per_round)

class Public_Goods_Game(Environment):
    def __init__(self, HISTORY_LENGTH, N_PLAYERS, 
            multiplier = 2, punishment_cost = 0.2, punishment_strength = 1):
        super().__init__(3, N_PLAYERS, 100)
        self.n_features = HISTORY_LENGTH * N_PLAYERS
        self.multiplier = multiplier
        self.punishment_cost = punishment_cost
        self.punishment_strength = punishment_strength
        self.history_length = HISTORY_LENGTH
        self.reset()

    def update_state(self, actions):
        if self.history_length > 0:
            self.s[:-1,:] = self.s[1:,:]
            self.s[-1,:] = actions

    def initial_state(self):
        return -np.ones((self.history_length,self.n_players)) #-1 means no action (at start of game)

    def state_to_observation(self):
        return np.reshape(self.s,self.n_players*self.history_length)

    def calculate_payoffs(self, actions):
        totalPool = self.multiplier * sum([min(a,1) for a in actions])
        share = totalPool / self.n_players
        payoffs = [share - min(a,1) for a in actions] # before punishment
        punishment_costs = [self.punishment_cost if a == 2 else 0 for a in actions]
        number_of_freeriders = actions.count(0)
        if number_of_freeriders > 0:
            punishment_amount_per_freerider = self.punishment_strength * actions.count(2) * 1.0 / number_of_freeriders
            punishments = [punishment_amount_per_freerider if a == 0 else 0 for a in actions]
        else:
            punishments = [0] * self.n_players
        return [r1 - r2 - r3
                for r1,r2,r3 in zip(payoffs,punishment_costs,punishments)]

class Prisoners_Dilemma(Environment):
    def __init__(self, N_PLAYERS, rep_update_factor):
        super().__init__(2, N_PLAYERS, 100)
        self.n_features = N_PLAYERS**2+1
        self.rep_update_factor = rep_update_factor
        self.reset()

    def update_state(self, actions):
        for idx, a in enumerate(actions):
            self.s[idx,int(self.fixture[idx])] = (1-self.rep_update_factor) * self.s[idx,int(self.fixture[idx])] 
            + self.rep_update_factor * a

    def initial_state(self):
        return 0.5 * np.ones((self.n_players,self.n_players))

    def state_to_observation(self):
        self.set_fixture()
        return [np.insert(np.reshape(self.s,self.n_players*self.n_players),0,i) for i in range(self.n_players)]

    def set_fixture(self):
        assert(self.n_players%2==0)
        fixture = np.zeros(self.n_players)
        remaining_indices = list(range(self.n_players))
        while remaining_indices:
            pair = np.random.choice(remaining_indices, 2, replace = False)
            fixture[pair[0]] = pair[1]
            fixture[pair[1]] = pair[0]
            remaining_indices.remove(pair[0])
            remaining_indices.remove(pair[1])
        self.fixture = fixture

    def calculate_payoffs(self, actions):
        return [1-a + 2*actions[int(self.fixture[idx])] for idx, a in enumerate(actions)]