from __future__ import division
import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator



class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env, trials=1):
        super(LearningAgent, self).__init__(
            env)
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.alpha = 0.9
        self.q_learn = {}
        self.default_Q = 1
        self.gamma = 0.3
        self.epsilon = 0.1


        self.success = 0
        self.total = 0
        self.trials = trials


        self.penalties = 0
        self.moves = 0

        self.net_reward = 0

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required
        self.prev_state = None
        self.prev_action = None
        self.prev_reward = None

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # TODO: Update state
        inputs['waypoint'] = self.next_waypoint

        # Tried deleting some inputs to see how it affected performance.
        # Success rate did improve significantly, and counterintuitively, less penalty.
        del inputs['oncoming']
        del inputs['left']
        del inputs['right']
        self.state = tuple(sorted(inputs.items()))

        # TODO: Select action according to your policy

        _Q, action = self._select_Q_action(self.state)

        # Execute action and get reward
        reward = self.env.act(self, action)

        self.net_reward += reward
        self.moves += 1
        if reward < 0:
            self.penalties += 1

        add_total = False
        if deadline == 0:
            add_total = True
        if reward > 5:
            self.success += 1
            add_total = True
        if add_total:
            self.total += 1

        # TODO: Learn policy based on state, action, reward

        if self.prev_state != None:
            if (self.prev_state, self.prev_action) not in self.q_learn:
                self.q_learn[(self.prev_state, self.prev_action)] = self.default_Q

            self.q_learn[(self.prev_state, self.prev_action)] = (1 - self.alpha) * self.q_learn[
                (self.prev_state, self.prev_action)] + \
                                                                self.alpha * (self.prev_reward + self.gamma * self._select_Q_action(self.state)[0])


        self.prev_state = self.state
        self.prev_action = action
        self.prev_reward = reward

        print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs,
                                                                                                    action,
                                                                                                    reward)
        print "Penalty: {}".format(self.penalties)
        print "Total reward: {}".format(self.net_reward)
        print "Sucesses: {}".format(self.success)

    def _get_Q(self, state, action):
        return self.q_learn.get((state, action), self.default_Q)

    def _random_pick(self, epsilon=0.5):
        return random.random() < epsilon

    def _select_Q_action(self, state):
        best_action = random.choice(Environment.valid_actions)
        if self._random_pick(self.epsilon):
            max_Q = self._get_Q(state, best_action)
        else:
            max_Q = -999999
            for action in Environment.valid_actions:
                Q = self._get_Q(state, action)
                if Q > max_Q:
                    max_Q = Q
                    best_action = action
                elif Q == max_Q:
                    if self._random_pick(0.5):
                        best_action = action
        return (max_Q, best_action)


def run():
    """Run the agent for a finite number of trials."""

    trials = 100
    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent, trials)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # set agent to track

    # Now simulate it
    sim = Simulator(e, update_delay=0.00000001)  # reduce update_delay to speed up simulation
    sim.run(n_trials=trials)  # press Esc or close pygame window to quit


if __name__ == '__main__':
    run()