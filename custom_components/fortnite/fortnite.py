from fortnite_python import Fortnite
from fortnite_python.domain import Platform
from fortnite_python.domain import Mode

class FortniteData():

    def __init__(self, name, api_key, player, platform, mode):
        self.name = name
        self.api_key = api_key
        self.player = player
        self.platform= Platform[platform]
        self.mode = Mode[mode]
        self.stats = None
        self.attr = {}

        try:
            # create the fortinite object
            self.game = Fortnite(self.api_key)
            self.fplayer = self.game.player(self.player, self.platform)
            self.update_stats()
        except:
            pass

    def update_stats(self):

       self.stats = self.fplayer.get_stats(self.mode)
       # transform stats into a dict
       self.attr['top1'] = self.stats.top1
       self.attr['top3'] = self.stats.top3
       self.attr['top10'] = self.stats.top10
       self.attr['kills'] = self.stats.kills

    def print_stats(self):
        print(self.stats)

if __name__ == '__main__':

    f = FortniteData('teste', 'b4384fbd-60da-4b8e-9d8a-a402dd18794e', 'Captain_Crunch88', 'GAMEPAD', 'SQUAD')
    f.update_stats()
    f.print_stats() 
