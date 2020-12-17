from otree.api import (
    models, BaseConstants, BaseSubsession, BasePlayer, widgets,
)

from django.contrib.contenttypes.models import ContentType
from otree_redwood.models import Event, DecisionGroup
from otree_redwood.models import Group as RedwoodGroup

import csv
import random
import math
import otree.common
import time
import datetime


doc = """
This is a Lines Queueing project
"""

class Constants(BaseConstants):
    name_in_url = 'random_number_game'
    players_per_group = None
    num_rounds = 50
    base_points = 0


def parse_config(config_file):
    with open('random_number_game/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'round_number': int(row['round_number']),
            'stage': int(row['stage']),
            'duration': int(row['duration']),
            'shuffle_role': True if row['shuffle_role'] == 'TRUE' else False,
            'players_per_group': int(row['players_per_group']),
        })
    return rounds

class Subsession(BaseSubsession):

    def num_rounds(self):
        return len(parse_config(self.session.config['config_file']))

    def creating_session(self):
        config = self.config
        if not config:
            return

        num_silos = self.session.config['num_silos']
        fixed_id_in_group = not config['shuffle_role']

        players = self.get_players()
        num_players = len(players)
        silos = [[] for _ in range(num_silos)]
        for i, player in enumerate(players):
            if self.round_number == 1:
                player.silo_num = math.floor(num_silos * i/num_players)
            else:
                player.silo_num = player.in_round(1).silo_num
            silos[player.silo_num].append(player)
        group_matrix = []
        for silo in silos:
            silo_matrix = []
            ppg = num_players#self.config['players_per_group']
            for i in range(0, len(silo), ppg):
                silo_matrix.append(silo[i:i+ppg])
            group_matrix.extend(otree.common._group_randomly(silo_matrix, fixed_id_in_group))
        self.set_group_matrix(group_matrix)
    
    def set_payoffs(self):
        for g in self.get_groups():
            g.set_payoffs()


    '''
    This function divides players into groups of 4 (2 male and 2 female)
    and also sets the first random number for each player

    Input: None
    Output: None
    '''
    def set_initial_numbers(self):
        # Only in the first round
        if self.round_number == 1:
            # Each player is assigned a group, 
            # self.session.vars['gender_group_ids'] stores the id of the group for each player id
            self.session.vars['gender_groups_ids'] = {}
            # self.session.vars['gender_groups'] stores the groups
            self.session.vars['gender_groups']  = []

            # Initialize gender_groups
            num_gender_groups = len(self.get_players())/4
            for i in range(int(num_gender_groups)):
                self.session.vars['gender_groups'].append([])

            males = []
            m_pointer = 0 # Points to the first male player
            females = []
            f_pointer = 0 # Points to the first female player

            # Divide players by gender
            for player in self.get_players():
                if player._gender == 'Male':
                    males.append(player)
                if player._gender == 'Female':
                    females.append(player)

            # Create each Group,by adding 2 males and two females one by one
            # WHile also logging {player id : group id} in self.session.vars['gender_groups_ids']
            for i in range(int(num_gender_groups)):
                self.session.vars['gender_groups'][i].append(males[m_pointer])
                self.session.vars['gender_groups_ids'].update({males[m_pointer].id_in_group : i})
                m_pointer += 1
                self.session.vars['gender_groups'][i].append(males[m_pointer])
                self.session.vars['gender_groups_ids'].update({males[m_pointer].id_in_group : i})
                m_pointer += 1
                self.session.vars['gender_groups'][i].append(females[f_pointer])
                self.session.vars['gender_groups_ids'].update({females[f_pointer].id_in_group : i})
                f_pointer += 1
                self.session.vars['gender_groups'][i].append(females[f_pointer])
                self.session.vars['gender_groups_ids'].update({females[f_pointer].id_in_group : i})
                f_pointer += 1

        # Set Numbers
        for player in self.get_players():
            num_string = "123456789"
            sr = ''.join(random.sample(num_string, len(num_string)))
            player._initial_number = int(sr)

    @property
    def config(self):
        try:
            return parse_config(self.session.config['config_file'])[self.round_number-1]
        except IndexError:
            return None

class Group(RedwoodGroup):

    def period_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['duration']
    
    def stage(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['stage']
    
    '''
    This function sets the payoffs for each player

    Input: None
    Output: None
    '''
    def set_payoffs(self):
        events = list(self.events.filter(channel='number'))
        for p in self.get_players():
            p.set_correct_answers(events)
        if self.stage() == 2:
            for g in self.session.vars['gender_groups']:
                # Sort each group by most correct answers
                g.sort(key=lambda x: self.get_player_by_id(x.id_in_group).correct_answers(), reverse=True)
        for p in self.get_players():
            p.set_payoff()

    '''
    This function receives data from the player-side.
    It just returns a new random number to the player.

    Input: event, the data sent by player
    Output: None
    '''
    def _on_number_event(self, event=None, **kwargs):
        print(event.value)
        id = event.value['id']
        player = self.get_player_by_id(int(id))

        num_string = "123456789"
        sr = ''.join(random.sample(num_string, len(num_string)))
        event.value['number'] = int(num_string)
        event.value['channel'] = 'outgoing'

        # broadcast the updated data out to all subjects
        self.send('number', event.value)
        self.save()



class Player(BasePlayer):
    silo_num = models.IntegerField()
    _initial_number = models.IntegerField()
    _correct_answers = models.IntegerField(initial=0)

    _gender =  models.StringField(
        choices=[
            'Male',
            'Female',
        ],
        widget=widgets.RadioSelect,
        label='Question: What is your gender?'
    )

    # This is the player's payment choice for the last stage
    _choice =  models.IntegerField(
        choices=[
            1,
            2
        ],
        widget=widgets.RadioSelect,
        label='Question: What payment treatment?'
    )

    def num_players(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['players_per_group']
    
    def initial_number(self):
        return self._initial_number
    
    def correct_answers(self):
        return self._correct_answers

    '''
    This function counts the amount of correct answers for the player

    Input: events (a list of data sent to the server)
    Output: None
    '''
    def set_correct_answers(self, events):
        correct_answers = 0
        for event in events:
            if event.value['id'] == self.id_in_group and event.value['channel'] == 'incoming':
                correct_answers += 1
        self._correct_answers = correct_answers
    
    '''
    If stage 0 or 1: Payoff = # of correct answers * 1500
    If stage 2: If most answers in group: # of correct answers * 6000
                Else: 0
    If Stage 3: If choice 1: # of correct answers * 1500
                If choice 2: If most answers in group: # of correct answers * 6000
                              Else: 0

    Input: None
    Output: None
    '''
    def set_payoff(self):
        print("set_payoff: ", self._correct_answers)
        if self.group.stage() == 0 or self.group.stage() == 1:
            self.payoff = self._correct_answers * 1500
        elif self.group.stage() == 2:
            group = self.session.vars['gender_groups'][self.session.vars['gender_groups_ids'][self.id_in_group]]
            if group[0].id_in_group == self.id_in_group:
                self.payoff = self._correct_answers * 6000
            else:
                self.payoff = 0
        elif self.group.stage() == 3 and self._choice == 1:
            self.payoff = self._correct_answers * 1500
        elif self.group.stage() == 3 and self._choice == 2:
            group = self.session.vars['gender_groups'][self.session.vars['gender_groups_ids'][self.id_in_group]]
            
            # Replace the player's own score from stage 2 with their score from stage 3 and re-sorts the group
            newGroup = [(p.id_in_group , p.in_round(3)._correct_answers) for p in group if p.id_in_group is not self.id_in_group]
            newGroup.append((self.id_in_group , self._correct_answers))
            newGroup.sort(key=lambda x: x[1], reverse=True)

            if newGroup[0][0] == self.id_in_group:
                self.payoff = self._correct_answers * 6000
            else:
                self.payoff = 0