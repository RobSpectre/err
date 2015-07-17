import logging
from errbot import BotPlugin, botcmd
from errbot.version import VERSION
from errbot.utils import tail
from os import path

log = logging.getLogger(__name__)


class Utils(BotPlugin):
    min_err_version = VERSION  # don't copy paste that for your plugin, it is just because it is a bundled plugin !
    max_err_version = VERSION

    # noinspection PyUnusedLocal
    @botcmd
    def echo(self, mess, args):
        """ A simple echo command. Useful for encoding tests etc ...
        """
        return args

    @botcmd
    def whoami(self, mess, args):
        """ A simple command echoing the details of your identifier. Useful to debug identity problems.
        """
        if args:
            frm = self.build_identifier(str(args).strip('"'))
        else:
            frm = mess.frm
        resp = "\n`person` is %s\n" % frm.person
        resp += "\n`nick` is %s\n" % frm.nick
        resp += "\n`fullname` is %s\n" % frm.fullname
        resp += "\n`client` is %s\n" % frm.client

        #  extra info if it is a MUC
        if hasattr(frm, 'room'):
            resp += "\n`room` is %s\n" % frm.room
        resp += "\n\nstring representation is '%s'\n" % frm
        resp += "\nclass is '%s'\n" % frm.__class__.__name__

        return resp

    # noinspection PyUnusedLocal
    @botcmd(historize=False)
    def history(self, mess, args):
        """display the command history"""
        answer = []
        user_cmd_history = self._bot.cmd_history[mess.frm.person]
        l = len(user_cmd_history)
        for i in range(0, l):
            c = user_cmd_history[i]
            answer.append('%2i:%s%s %s' % (l - i, self._bot.prefix, c[0], c[1]))
        return '\n'.join(answer)

    # noinspection PyUnusedLocal
    @botcmd
    def log_tail(self, mess, args):
        """ Display a tail of the log of n lines or 40 by default
        use : !log tail 10
        """
        # admin_only(mess)  # uncomment if paranoid.
        n = 40
        if args.isdigit():
            n = int(args)

        if self.bot_config.BOT_LOG_FILE:
            with open(self.bot_config.BOT_LOG_FILE, 'r') as f:
                return tail(f, n)
        return 'No log is configured, please define BOT_LOG_FILE in config.py'

    @botcmd
    def render_test(self, mess, args):
        """ Tests / showcases the markdown rendering on your current backend
        """
        with open(path.join(path.dirname(path.realpath(__file__)), 'test.md')) as f:
            return f.read()
