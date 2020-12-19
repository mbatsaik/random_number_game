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


class Constants(BaseConstants):
    name_in_url = 'random_number_game'
    players_per_group = 4
    num_rounds = 150 # 50 rounds per stage to make the respective page repeat itself 50 times 
    base_points = 0


class Subsession(BaseSubsession):

    def creating_session(self):

        players = self.get_players()
        num_players = len(players)
        
        #TODO: define group assignation function (take the following code as basis)
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
    best_score_stage_2 = models.IntegerField() # highest number of correct answers per group in S2
    
    def set_group_payoffs(self):
        if self.stage == 1:
            for player_in_group in self.get_players():
                player_in_group.payoff_stage_1 = player_in_group._correct_answers * 1500

        elif self.stage == 2:
            best_player = None # Player Object, placeholder for best player
            best_players = [] # List of ids in group, placeholder for best players (with same score)
            self.best_score_stage_2 = 0 # Int, placeholder for best score
            
            # evaluating who is the best player
            for player_in_group in self.get_players():
                if self.best_score_stage_2 <=  player_in_group._correct_answers:
                    best_player = player_in_group
                    self.best_score_stage_2 = best_player._correct_answers
            
            # evaluating if more than one player obtained the best score
            for player_in_group in self.get_players():
                if self.best_score_stage_2 ==  player_in_group._correct_answers:
                    best_players.append(player_in_group.id_in_group)
            
            # declaring who won if more than 1 obtained the best score
            if len(best_players) > 1:
                random.SystemRandom().shuffle(best_players) # randomizing the order
                for player_in_group in self.get_players():
                    if player_in_group.id_in_group == best_players[0]: # picking the winner at random
                        player_in_group.stage_2_winner = True
                    else:
                        player_in_group.stage_2_winner = False

            # declaring who won if only 1 player got best score
            else:
                best_player.stage_2_winner = True
                for player_in_group in self.get_players():
                    if player_in_group != best_player:
                        player_in_group.stage_2_winner = False
                        player_in_group.payoff_stage_2 = 0
                    else:
                        player_in_group.payoff_stage_2 = player_in_group._correct_answers * 6000
        
        elif self.stage == 3:
            for player_in_group in self.get_players():
                # paying the player according to his stage system choice
                # if stage 1 chosen
                if player_in_group.in_round(round(2*Constants.num_rounds/3) + 1)._choice == 1: 
                    player_in_group.payoff_stage_3 = player_in_group._correct_answers * 1500
                # if stage 2 chosen
                elif player_in_group.in_round(round(2*Constants.num_rounds/3) + 1)._choice == 2: 
                    if player_in_group.in_round(Constants.num_rounds)._correct_answers > self.best_score_stage_2:
                        player_in_group.payoff_stage_3 = player_in_group._correct_answers * 6000
                    else:
                        player_in_group.payoff_stage_3 = 0

        else:
            print("DEBUG: Stage undefined value = {self.stage}")

        if self.round_number == Constants.num_rounds:
            # adding all the stage payoffs to the player's final payoff
            for player_in_group in self.get_players():
                player_in_group.payoff = player_in_group.in_round(round(Constants.num_rounds/3)).payoff_stage_1 + \
                                         player_in_group.in_round(round(2*Constants.num_rounds/3)).payoff_stage_2 + \
                                         player_in_group.in_round(Constants.num_rounds).payoff_stage_3


class Player(BasePlayer):
    silo_num = models.IntegerField()
    task_number = models.StringField()
    task_number_img = models.StringField() # command for displaying task_number image file
    transcription = models.StringField()
    answer_is_correct = models.IntegerField()
    _correct_answers = models.IntegerField(initial=0)
    _gender_group_id = models.IntegerField()
    stage_2_winner = models.BooleanField() # True if player wins, False if not
    payoff_stage_1 = models.CurrencyField()
    payoff_stage_2 = models.CurrencyField()
    payoff_stage_3 = models.CurrencyField()

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
    ) # 1 is Stage 1 and 2 is Stage 2

    def set_correct_answer(self, transcription):
        """
        Verifies that the number inputted is correct and adds 
        increases the count of correct answers if that's the
        case

        Input: transcripted number (integer)
        Output: None
        """
        if transcription == self.task_number:
            self.answer_is_correct = 1
            if self.round_number <= round(Constants.num_rounds/3):
                self.participant.vars['correct_answers_s1'] += 1  
                self._correct_answers = self.participant.vars['correct_answers_s1']
            elif self.round_number > round(Constants.num_rounds/3) and \
                self.round_number <= round(2*Constants.num_rounds/3):
                self.participant.vars['correct_answers_s2'] += 1  
                self._correct_answers = self.participant.vars['correct_answers_s2']
            else:
                self.participant.vars['correct_answers_s3'] += 1  
                self._correct_answers = self.participant.vars['correct_answers_s3']

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
