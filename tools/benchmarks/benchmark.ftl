
single-string-literal = Hello I am a single string literal in Polish

single-interpolation = Hello { $username }, welcome to our website! in Polish

# Don't include the count in the output, to test just the speed of the plural
# form lookup, rather than the locale aware number formatting routines.

plural-form-select = { $count ->
    [one] There is one thing, in Polish
    [few] There are few things, in Polish
    [many] There are many things, in Polish
   *[other] There are other things, in Polish
 }
