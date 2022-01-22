from enum import Enum


class Action(Enum):
    CLOUD = 0
    SKIP = 1

    def __repr__(self):
        return self.name


class Solution:
    decisions = None
    score = None
    scores_by_decision = None

    def __init__(self, decisions, score, scores_by_decision):
        self.decisions = decisions
        self.score = score
        self.scores_by_decision = scores_by_decision
