import math
from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
from datetime import timedelta
from operator import concat
from functools import reduce

from PIL import Image, ImageDraw, ImageFont
from time import time


def writeText(text, fileName):
    """"
    This method generates the image version of an inputted text
    and saves it to fileName
    
    Input: text to be transcripted into the image, name of the output img file
    Output: None
    """

    image = Image.open('random_number_game/background.png')
    image = image.resize((650, 100))
    image.save('random_number_game/background.png')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('random_number_game/Roboto-Regular.ttf', size=19)
    imageChars = 100
    numLines = len(text) / imageChars
    numLines = math.ceil(numLines)
    lines = []

    for i in range(numLines):
        if(imageChars * (i + 1) < len(text)):
            lines.append(text[imageChars * i : imageChars * (i+1)])
        else:
            lines.append(text[imageChars * i : len(text)])

    for i in range(numLines):
        (x, y) = (10, 20 * i)
        message = lines[i]
        print("Message is: ", message)
        color = 'rgb(0, 0, 0)' # black color
        draw.text((x, y), message, fill=color, font=font)

    image.save(fileName) # stores the image on a specified folder


class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1


class GenderPage(Page):
    form_model = 'player'
    form_fields = ['_gender']

    def is_displayed(self):
        return self.round_number == 1


class ChoicePage(Page):   
    form_model = 'player'
    form_fields = ['_choice']

    def is_displayed(self):
        return self.round_number == round(2*Constants.num_rounds/3) + 1 # displays on beginning of third stage


class Stage2WaitPage(WaitPage):
    """
    WaitPage for assigning each player to their respective
    2 men 2 women group for Stage 2
    """
    
    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True
    after_all_players_arrive = 'group_assignment' # players will be assigned into groups of 2 men and 2 women
    #TODO: code group_assignment method 
    #TODO: the group_assignment method requires some commands to keep the grouping as this round for the rest of rounds

    def is_displayed(self):
        return self.round_number == round(Constants.num_rounds/3) + 1 # displays on beginning of second stage


class ProcessingPage(Page):
    timeout_seconds = 0.5 #TODO: test if non-integer timeouts work

    def before_next_page(self):
        # creating the number images and storing their commands to display on page
        #TODO: erase images after being displayed
        for player in self.group.get_players():
            player.task_number = self.player.task_number_method()
            self.round_number
            # name of random number image file
            task_number_file = "random_number_game/" + \
                               f"{player.task_number}_player_{player.id_in_group}_{self.round_number}"
            # creating the img file
            writeText(player.task_number, f'random_number_game/static/{task_number_file}.png')

            # storing the command to display the image per player
            player.task_number_img = '<img src="{% static "' + f'{task_number_file}.png' + '" %}"/>'

        # timeout for multiple pages that restarts at beginning of each stage
        if self.round_number == 1 or self.round_number == round(Constants.num_rounds/3) + 1 \
           or self.round_number == round(2*Constants.num_rounds/3) + 1:

            # assigning stage
            if self.round_number >= 1 and self.round_number <= round(Constants.num_rounds/3):
                self.group.stage == 1
            
            elif self.round_number > round(Constants.num_rounds/3) and \
                self.round_number <= round(2*Constants.num_rounds/3):
                self.group.stage == 2

            else:
                self.group.stage == 3

            self.participant.vars[f'correct_answers_s{self.group.stage}'] = 0 # setting up the corr answ counter
            self.participant.vars['expiry_time'] = time() + 3*60 # timeout of 3 minutes
    

class Decision(Page):
    form_model = "player"
    form_fields = ['transcription']
    
    #TODO: code frontend page for decision (Alex)
    def get_timeout_seconds(self):
        return self.participant.vars['expiry_time'] - time() # updating the time each time the page is displayed

    def is_displayed(self):
        return self.participant.vars['expiry_time'] != 0 # display only if there is time left

    def before_next_page(self):
        self.player.set_correct_answer(self.player.transcription) # checking if the answer was correct


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True
    after_all_players_arrive = 'set_group_payoffs'

    def is_displayed(self):
        return self.round_number == round(Constants.num_rounds/3) or \
               self.round_number == round(2*Constants.num_rounds/3)


class Results(Page):

    def is_displayed(self):
        return self.round_number == round(Constants.num_rounds/3) or \
               self.round_number == round(2*Constants.num_rounds/3) or \
               self.round_number == Constants.num_rounds    

    def vars_for_template(self):
        return{
            'correct_answers': self.player.correct_answers()
        }
        

class Payment(Page):

    def is_displayed(self):
        return self.round_number == self.subsession.num_rounds()
    
    def vars_for_template(self):
        payoff_1 = self.player.in_round(round(Constants.num_rounds/3)).payoff_stage_1
        payoff_2 = self.player.in_round(round(2*Constants.num_rounds/3)).payoff_stage_2
        payoff_3 = self.player.in_round(Constants.num_rounds).payoff_stage_3

        return {
            'payoff_1': payoff_1,
            'payoff_2': payoff_2,
            'payoff_3': payoff_3,
        }

page_sequence = [
    Introduction,
    GenderPage,
    ChoicePage,
    Stage2WaitPage,
    ProcessingPage,
    Decision,
    ResultsWaitPage,
    Results,
    Payment
]