"""
    This is the package for the match algorithms.
"""

from random import randint

class Matcher:
    def match(self, triples):
        """ To return the matches
        :param triples: list of (letter, letter_temp, letter_system)
        :return: list of pairs of triples, some of them may be left, but no repeat
        """
        return None

class NaiveMatcher(Matcher):
    def match(self, triples):
        # simply shuffle and delete the same ones
        pairs = []
        while len(triples) > 1:
            other = randint(0, len(triples)-2)
            triples[other], triples[-2] = triples[-2], triples[other]
            pairs.append((triples[-1], triples[-2]))
            triples = triples[:-2]
        # print(pairs)
        return [p for p in pairs if p[0][0].send_id != p[1][0].send_id]     # not self

matcher = NaiveMatcher()
