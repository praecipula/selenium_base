from code import InteractiveConsole

def drop_into_repl(title, scope):
    InteractiveConsole(locals=scope).interact(title)
