#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4:sw=4

from markdown import Markdown
from markdown.extensions.extra import ExtraExtension
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor
from itertools import chain
from os import path
from ansi.color import fg, bg, fx
import io
import logging

log = logging.getLogger(__name__)

try:
    from html import unescape  # py3.5
except:
    try:
        from html.parser import HTMLParser  # py3.4
    except ImportError:
        from HTMLParser import HTMLParser  # py2
    finally:
        unescape = HTMLParser().unescape


class Table(object):

    def __init__(self,  mode='ansi'):
        self.headers = []
        self.rows = []
        self.in_headers = False
        self.mode = mode

    def next_row(self):
        if self.in_headers:
            self.headers.append([])  # is that exists ?
        else:
            self.rows.append([])

    def add_col(self):
        if not self.rows:
            self.rows = [[]]
        else:
            self.rows[-1].append(('', 0))

    def add_header(self):
        if not self.headers:
            self.headers = [[]]
        else:
            self.headers[-1].append(('', 0))

    def begin_headers(self):
        self.in_headers = True

    def end_headers(self):
        self.in_headers = False

    def write(self, text):
        cells = self.headers if self.in_headers else self.rows

        text_cell, count = cells[-1][-1]
        if isinstance(text, str):
            text_cell += text
            count += len(text)
        elif self.mode == "ansi":  # skip the graphic if not ansi
            text_cell += str(text)  # Graphic
        cells[-1][-1] = text_cell, count

    def __str__(self):
        nbcols = max(len(row) for row in chain(self.headers, self.rows))
        maxes = [0, ] * nbcols

        for row in chain(self.headers, self.rows):
            for i, el in enumerate(row):
                _, length = el
                if maxes[i] < length:
                    maxes[i] = length

        # add up margins
        maxes = [m + 2 for m in maxes]

        output = io.StringIO()
        if self.headers:
            output.write('┏' + '┳'.join('━' * m for m in maxes) + '┓')
            output.write('\n')
            first = True
            for row in self.headers:
                if not first:
                    output.write('┣' + '╋'.join('━' * m for m in maxes) + '┫')
                    output.write('\n')
                first = False
                for i, header in enumerate(row):
                    text, l = header
                    output.write('┃ ' + text + ' ' * (maxes[i] - 2 - l) + ' ')
                output.write('┃')
                output.write('\n')
            output.write('┡' + '╇'.join('━' * m for m in maxes) + '┩')
            output.write('\n')
        else:
            output.write('┌' + '┬'.join('─' * m for m in maxes) + '┐')
            output.write('\n')
        first = True
        for row in self.rows:
            if not first:
                output.write('├' + '┼'.join('─' * m for m in maxes) + '┤')
                output.write('\n')
            first = False
            for i, item in enumerate(row):
                text, l = item
                output.write('│ ' + text + ' ' * (maxes[i] - 2 - l) + ' ')
            output.write('│')
            output.write('\n')
        output.write('└' + '┴'.join('─' * m for m in maxes) + '┘')
        output.write('\n')
        if self.mode == 'imtext':
            return '```\n' + output.getvalue() + '```\n'
        else:
            return output.getvalue()


def recurse_ansi(write, element, table=None, mode='ansi'):
    exit = []
    if element.text:
        text = element.text
    else:
        text = ''

    items = element.items()
    for k, v in items:
        if k == 'color':
            color_attr = getattr(fg, v)
            if color_attr is None:
                log.warn("there is no '%s' color in ansi" % v)
            write(color_attr)
            exit.append(fg.default)
        elif k == 'bgcolor':
            color_attr = getattr(bg, v)
            if color_attr is None:
                log.warn("there is no '%s' bgcolor in ansi" % v)
            write(color_attr)
            exit.append(bg.default)
    if element.tag == 'img':
        text = dict(items)['src']
    elif element.tag == 'strong':
        if mode == 'imtext' and not table:  # * * are supported in imtext
            write('*')
            exit.append('*')
        else:
            write(fx.bold)
            exit.append(fx.normal)
    elif element.tag == 'em':
        if mode == 'imtext' and not table:  # _ _ are supported in imtext
            write('_')
            exit.append('_')
        else:
            write(fx.underline)
            exit.append(fx.not_underline)
    elif element.tag == 'p':
        write(' ')
        exit.append('\n')
    elif element.tag == 'li':
        write('• ')
        exit.append('\n')
    elif element.tag == 'hr':
        write('─' * 80)
        write('\n')
    elif element.tag == 'ul':  # ignore the text part
        text = None
    elif element.tag == 'h1':
        if mode == 'imtext' and not table:  # * * are supported in imtext
            write('*')
            exit.append('*')
        else:
            write(fx.bold)
        text = text.upper()
        exit.append(fx.normal)
        exit.append('\n\n')
    elif element.tag == 'h2':
        write('\n')
        write('  ')
        if mode == 'imtext' and not table:  # * * are supported in imtext
            write('*')
            exit.append('*')
        else:
            write(fx.bold)
        exit.append(fx.normal)
        exit.append('\n\n')
    elif element.tag == 'h3':
        write('\n')
        write('    ')
        if mode == 'imtext' and not table:  # _ _ are supported in imtext
            write('_')
            exit.append('_')
        else:
            write(fx.underline)
        exit.append(fx.not_underline)
        exit.append('\n')
    elif element.tag in ('h4', 'h5', 'h6'):
        write('\n')
        write('      ')
        exit.append('\n')
    elif element.tag == 'table':
        table = Table(mode)
        orig_write = write
        write = table.write
        text = None
    elif element.tag == 'tbody':
        text = None
    elif element.tag == 'thead':
        table.begin_headers()
        text = None
    elif element.tag == 'tr':
        table.next_row()
        text = None
    elif element.tag == 'td':
        table.add_col()
    elif element.tag == 'th':
        table.add_header()

    if text:
        write(text)
    for e in element:
        recurse_ansi(write, e, table, mode)
    if element.tag == 'table':
        write = orig_write
        write(str(table))

    if element.tag == 'thead':
        table.end_headers()

    for restore in exit:
        write(restore)
    if element.tail:
        tail = element.tail.rstrip('\n')
        if tail:
            write(tail)


def to_ansi(element):
    f = io.StringIO()

    def write(ansi_obj):
        return f.write(str(ansi_obj))
    recurse_ansi(write, element)
    write(fx.reset)
    return f.getvalue()


def to_text(element):
    f = io.StringIO()

    def write(text):
        if not isinstance(text, str):  # skip graphic stuff
            return None
        return f.write(text)
    recurse_ansi(write, element, mode='text')
    return f.getvalue()


def to_imtext(element):
    """ Simplified Format for skype, gtalk, slack ... """
    f = io.StringIO()

    def write(text):
        if not isinstance(text, str):  # skip graphic stuff
            return None
        return f.write(text)
    recurse_ansi(write, element, mode='imtext')
    return f.getvalue()

# patch us in
Markdown.output_formats['ansi'] = to_ansi
Markdown.output_formats['text'] = to_text
Markdown.output_formats['imtext'] = to_imtext


class AnsiPostprocessor(Postprocessor):
    """Markdown generates html entities, this reputs them back to their unicode equivalent"""

    def run(self, text):
        return unescape(text)


class AnsiExtension(Extension):
    """(kinda hackish) This is just a private extension to postprocess the html text to ansi text"""

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.postprocessors.add(
            "unescape html", AnsiPostprocessor(), ">unescape"
        )
        log.debug("Will apply those postprocessors:\n%s" % md.postprocessors)
