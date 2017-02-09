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
                self.reset_peek()
                break

    def skip_line_ws(self):
        while self.ch:
            if self.ch != ' ' and self.ch != '\t':
                break
            self.next()

    def expect_char(self, ch):
        if self.ch == ch:
            self.next()
            return True

        raise Exception('ExpectedToken')

    def take_char_if(self, ch):
        if self.ch == ch:
            self.next()
            return True
        return False

    def take_char(self, f):
        ch = self.ch
        if f(ch):
            self.next()
            return ch
        return None

    def is_id_start(self):
        cc = ord(self.ch)

        return (cc >= 97 and cc <= 122) or \
               (cc >= 65 and cc <= 90) or \
                cc == 95

    def is_number_start(self):
        cc = ord(self.ch)

        return (cc >= 48 and cc <= 57) or cc == 45

    def is_peek_next_line_variant_start(self):
        if not self.current_peek_is('\n'):
            return False
        
        self.peek()

        self.peek_line_ws()
        if self.current_peek_is('*'):
            self.peek()

        if self.current_peek_is('[') and not self.peek_char_is('['):
            self.reset_peek()
            return True

        self.reset_peek()
        return False

    def is_peek_next_line_attribute_start(self):
        if not self.current_peek_is('\n'):
            return False
        
        self.peek()

        self.peek_line_ws()

        if self.current_peek_is('.'):
            self.reset_peek()
            return True

        self.reset_peek()
        return False

    def skip_to_next_entry_start(self):
        while self.next():
            if self.current_is('\n') and not self.peek_char_is('\n'):
                self.next()

                if self.ch == None or self.is_id_start() or self.current_is('#') or \
                   (self.current_is('[') and self.peek_char_is('[')):
                    break

    def take_id_start(self):
        if self.is_id_start():
            ret = self.ch
            self.next()
            return ret

        raise Exception('ExpectedCharRange')

    def take_id_char(self):
        def closure(ch):
            cc = ord(ch)
            return (cc >= 97 and cc <= 122) or \
                   (cc >= 65 and cc <= 90) or \
                   (cc >= 48 and cc <= 57) or \
                    cc == 95 or cc == 45
        return self.take_char(closure)

    def take_kw_char(self):
        def closure(ch):
            cc = ord(ch)
            return (cc >= 97 and cc <= 122) or \
                   (cc >= 65 and cc <= 90) or \
                   (cc >= 48 and cc <= 57) or \
                    cc == 95 or cc == 45 or cc == 32
        return self.take_char(closure)

    def take_digit(self):
        def closure(ch):
            cc = ord(ch)
            return (cc >= 48 and cc <= 57) 
        return self.take_char(closure)
