from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

import csv
import random
import math
import otree.common
import time
import datetime


doc = """
This is a Lines Queueing project
"""

# def parse_config(config_file):
#     """
#     Parses the information of a configuration file for otree usage

#     Input: configuration file name (config_file)
#     Output: None 
#     """

#     with open('random_number_game/configs/' + config_file) as file:
#         rows = list(csv.DictReader(file))

#     rounds = []
#     for row in rows:
#         rounds.append({
#             'round_number': int(row['round_number']),
#             'stage': int(row['stage']),
#             'duration': int(row['duration']),
#             'shuffle_role': True if row['shuffle_role'] == 'TRUE' else False,
#             'players_per_group': int(row['players_per_group']),
#         })
#     return rounds


class Constants(BaseConstants):
    name_in_url = 'random_number_game'
    players_per_group = 4
    num_rounds = 150 # 50 rounds per stage to make the respective page repeat itself 50 times 
    base_points = 0


class Subsession(BaseSubsession):

    def creating_session(self):
        config = self.config

        num_silos = self.session.config['num_silos'] #TODO: ask Alex what is num_silos: possible subgroup
        fixed_id_in_group = not config['shuffle_role'] # if role not shuffled, the ids'll be fixed

        players = self.get_players()
        num_players = len(players)
        silos = [[] for _ in range(num_silos)]

        # silo assignation per player in first round
        for i, player in enumerate(players):
            if self.round_number == 1: 
                player.silo_num = math.floor(num_silos * i/num_players)
            else: # same silo for the next rounds
                player.silo_num = player.in_round(1).silo_num
            silos[player.silo_num].append(player)
        
        # defining a matrix with players per group
        group_matrix = []
        for silo in silos:
            silo_matrix = []
            for i in range(0, len(silo), num_players):
                silo_matrix.append(silo[i:i+num_players])
            group_matrix.extend(otree.common._group_randomly(silo_matrix, fixed_id_in_group))
        self.set_group_matrix(group_matrix) # setting up the matrix in otree
    
    def set_payoffs_per_group(self):
        """
        Sets the payoff for the participants in each group

        Input: None
        Output: None
        """
        for group in self.get_groups():
            group.set_payoffs()


class Group(BaseGroup):
   
    stage = models.IntegerField()
    
    def set_group_payoffs(self):
        for p in self.get_players():
            p.set_payoff()


class Player(BasePlayer):
    silo_num = models.IntegerField()
    task_number = models.StringField()
    task_number_img = models.StringField() # command for displaying task_number image file
    transcription = models.StringField()
    _initial_number = models.IntegerField()
    _correct_answers = models.IntegerField(initial=0)
    _gender_group_id = models.IntegerField()

    _gender =  models.StringField(
        choices=[
            'Male',
            'Female',
        ],
        widget=widgets.RadioSelect,
        label='Question: What is your gender?'
    )
    _choice =  models.IntegerField(
        choices=[
            1,
            2
        ],
        widget=widgets.RadioSelect,
        label='Question: What payment treatment?'
    )

    def set_correct_answer(self, transcription):
        """
        Verifies that the number inputted is correct and adds 
        increases the count of correct answers if that's the
        case

        Input: transcripted number (integer)
        Output: None
        """
        if transcription == self.task_number:
            self._correct_answers += 1

    def task_number_method(self):
        """
        Creates a random 9-digit number as a string for transcription 
        with unique digits

        Input: None
        Output: task number (string)
        """

        random_number = ""
        one_to_nine = [num for num in range(1, 10)] # list with numbers from 1 to 9

        random.SystemRandom().shuffle(one_to_nine) # shuffling the order of its items

        # turning the list into a string
        for num in one_to_nine:
            initial_number += str(num)

        return random_number

    def set_payoff(self):
        print("set_payoff: ", self._correct_answers)
        if self.group.stage == 1:
            self.payoff = self._correct_answers * 1500
        elif self.group.stage == 2:
            self.payoff = self._correct_answers * 1500
            # TODO: edit stage 3 payoff
        elif self.group.stage == 2:
            group = self.session.vars['gender_groups'][self.session.vars['gender_groups_ids'][self.id_in_group]]
            if group[0].id_in_group == self.id_in_group:
                self.payoff = self._correct_answers * 6000
            else:
                self.payoff = 0
        elif self.group.stage == 3 and self._choice == 1:
            self.payoff = self._correct_answers * 1500
        elif self.group.stage == 3 and self._choice == 2:
            group = self.session.vars['gender_groups'][self.session.vars['gender_groups_ids'][self.id_in_group]]
            
            newGroup = [(p.id_in_group , p.in_round(3)._correct_answers) for p in group if p.id_in_group is not self.id_in_group]
            newGroup.append((self.id_in_group , self._correct_answers))
            newGroup.sort(key=lambda x: x[1], reverse=True)

            if newGroup[0][0] == self.id_in_group:
                self.payoff = self._correct_answers * 6000
            else:
                self.payoff = 0

"""
    def set_initial_numbers(self):
        
        if self.round_number == 1:
            self.session.vars['gender_groups_ids'] = {}
            self.session.vars['gender_groups']  = []
            num_gender_groups = len(self.get_players())/4
            for i in range(int(num_gender_groups)):
                self.session.vars['gender_groups'].append([])

            males = []
            m_pointer = 0
            females = []
            f_pointer = 0

            for player in self.get_players():
                if player._gender == 'Male':
                    males.append(player)
                if player._gender == 'Female':
                    females.append(player)

            for i in range(int(num_gender_groups)):
                self.session.vars['gender_groups'][i].append(males[m_pointer])
                males[m_pointer]._gender_group_id = i
                self.session.vars['gender_groups_ids'].update({males[m_pointer].id_in_group : i})
                m_pointer += 1
                self.session.vars['gender_groups'][i].append(males[m_pointer])
                self.session.vars['gender_groups_ids'].update({males[m_pointer].id_in_group : i})
                males[m_pointer]._gender_group_id = i
                m_pointer += 1
                self.session.vars['gender_groups'][i].append(females[f_pointer])
                self.session.vars['gender_groups_ids'].update({females[f_pointer].id_in_group : i})
                females[f_pointer]._gender_group_id = i
                f_pointer += 1
                self.session.vars['gender_groups'][i].append(females[f_pointer])
                self.session.vars['gender_groups_ids'].update({females[f_pointer].id_in_group : i})
                females[f_pointer]._gender_group_id = i
                f_pointer += 1
            print(self.session.vars['gender_groups_ids'])


        for player in self.get_players():
            num_string = ""
            for i in range(9):
                num_string += str(random.randint(1, 9))
            player._initial_number = int(num_string)
            print(player.id_in_group, ": ", player._initial_number)

    @property
    def config(self):
        try:
            return parse_config(self.session.config['config_file'])[self.round_number-1]
        except IndexError:
            return None
"""