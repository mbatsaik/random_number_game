import math
from ._builtin import Page, WaitPage

from datetime import timedelta
from operator import concat
from functools import reduce
from .models import parse_config

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
        return self.group.stage() == 3

class DecisionWaitPage(WaitPage):

    body_text = 'Waiting for all players to be ready'
    wait_for_all_groups = True
    after_all_players_arrive = 'set_initial_numbers'

    def is_displayed(self):
        return self.subsession.config is not None


class Decision(Page):

    def is_displayed(self):
        return self.subsession.config is not None


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    after_all_players_arrive = 'set_payoffs'

    def is_displayed(self):
        return self.subsession.config is not None


class Results(Page):

    timeout_seconds = 15

    def is_displayed(self):
        return self.subsession.config is not None

    def vars_for_template(self):
        pass
        

class Payment(Page):

    def is_displayed(self):
        return self.round_number == self.subsession.num_rounds()
    
    def vars_for_template(self):
        payoff_1 = self.player.in_round(2).payoff
        payoff_2 = self.player.in_round(3).payoff
        payoff_3 = self.player.in_round(4).payoff

        return {
            'payoff_1': payoff_1,
            'payoff_2': payoff_2,
            'payoff_3': payoff_3,
        }

page_sequence = [
    Introduction,
    GenderPage,
    DecisionWaitPage,
    ChoicePage,
    Decision,
    ResultsWaitPage,
    Results,
    Payment
]