class LogModel:

    def __init__(self, logOwner, logHeader, logText):
        self.logOwner = logOwner
        self.logHeader = logHeader
        self.logText = logText

    def toString(self):

        textList = ''.join(self.logText).split('\u26E7')
        buildString = ''
        for i in range(len(self.logHeader)):
            buildString += self.logHeader[i]
            buildString += textList[i+1]    # +1 because there is an empty element at the start strangely
        return self.logOwner + buildString
