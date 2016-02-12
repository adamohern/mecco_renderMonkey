#python

# By Adam O'Hern for Mechanical Color LLC
# Attempts to render a series of frames from an arbitrary string, like "1-5, 10, 20-15"

import monkey, modo, lx, lxu, traceback, os

CMD_NAME = 'renderMonkey.range'


class CMD(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.startPath = None

        self.dyna_Add('range', lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        try:
            frames_string = self.dyna_String(0)
            frames_list = monkey.util.range_from_string(frames_string)

            if frames_list:
                monkey.util.render_range(frames_list)
            else:
                modo.dialogs.alert("Invalid Frame Range","error",'No frame range recognized in "%s".' % range_string)
                return lx.symbol.e_FAILED

        except:
            monkey.util.debug(traceback.format_exc())


lx.bless(CMD, CMD_NAME)
