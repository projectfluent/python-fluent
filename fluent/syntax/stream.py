from __future__ import unicode_literals


class ParserStream():
    def __init__(self, string):
        self.string = string
        self.index = 0
        self.peek_offset = 0

    def char_at(self, index):
        try:
            return self.string[index]
        except IndexError:
            return None

    @property
    def current_char(self):
        return self.char_at(self.index)

    @property
    def current_peek(self):
        return self.char_at(self.index + self.peek_offset)

    def next(self):
        self.index += 1
        self.peek_offset = 0
        return self.char_at(self.index)

    def peek(self):
        self.peek_offset += 1
        return self.char_at(self.index + self.peek_offset)

    def reset_peek(self, offset=0):
        self.peek_offset = offset

    def skip_to_peek(self):
        self.index += self.peek_offset
        self.peek_offset = 0
