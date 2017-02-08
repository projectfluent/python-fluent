class StringIter():
    def __init__(self, source):
        self.source = source
        self.len = len(source)
        self.i = 0

    def next(self):
        if self.i < self.len:
            ret = self.source[self.i]
            self.i += 1
            return ret
        return None

class ParserStream():
    def __init__(self, string):
        self.iter = StringIter(string)
        self.buf = []
        self.peekIndex = 0
        self.index = 0

        self.ch = None

        self.iter_end = False
        self.peek_end = False

        self.ch = self.iter.next()

    def next(self):
        if self.iter_end:
            return None

        if len(self.buf) == 0:
            self.ch = self.iter.next()
        else:
            self.ch = self.buf.shift()

        self.index += 1

        if self.ch == None:
            self.iter_end = True
            self.peek_end = True

        self.peek_index = self.index

        return self.ch

    def current(self):
        return self.ch

    def get_index(self):
        return self.index

