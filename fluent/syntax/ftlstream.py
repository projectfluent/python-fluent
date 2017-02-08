from .stream import ParserStream

class FTLParserStream(ParserStream):
    def peek_line_ws(self):
        ch = self.current_peek()
        while ch:
            if ch != ' ' and ch != '\t':
                break
            ch = self.peek()

    def skip_ws_lines(self):
        while True:
            self.peek_line_ws()

            if self.current_peek_is('\n'):
                self.skip_to_peek()
                self.next()
            else:
                self.reset_to_peek()
                break

    def skip_line_ws(self):
        while self.ch:
            if self.ch != ' ' and self.ch != '\t':
                break
            self.next()

    def expec_char(self, ch):
        if self.ch == ch:
            self.next()
            return True

        raise Exception('ExpectedToken')

    def is_id_start(self):
        cc = ord(self.ch)

        return (cc >= 97 and cc <= 122) or \
               (cc >= 65 and cc <= 90) or \
               (cc >= 48 and cc <= 57) or \
                cc == 95 or cc == 45

    def take_id_start(self):
        if self.is_id_start():
            ret = self.ch
            self.next()
            return ret

        raise Exception('ExpectedCharRange')

    def take_id_char(self):
        pass
