#!/usr/bin/env python3
"""Read and write LibreOffice Draw (.odg) figures without LibreOffice's GUI.

As a command:
  odgKit.py list X.odg          one line per shape: kind, x, y, w, h (cm), style, text
  odgKit.py page X.odg          the page size, the fonts declared, the arrow markers available

As a module (a figure generated from a base .odg, keeping its page, styles, fonts and settings):
  from odgKit import Figure, L
  f = Figure('X.orig_odg')
  f.frame()                                         # the red 16x9 presentation frame
  f.box(2, 3, 10, 1.4, '#9fc5f8', '#3d85c6', [L('Title', 14, bold=True), L('detail', 10)])
  f.text(2, 5, 10, 0.6, [L('a label', 10, italic=True)])
  f.line(5, 4.4, 5, 6, start=True, end=True)        # two-headed arrow
  f.write('X.odg')

Coordinates and sizes are in cm from the page's top left. The shapes are written in the order they
are added (later ones on top).
"""
import html
import re
import sys
import zipfile
from xml.sax.saxutils import escape


def L(text, size=14, bold=False, italic=False, color='#000000'):
    """One paragraph of a shape's text."""
    return (text, size, bold, italic, color)


class Figure:
    def __init__(self, base, font='Liberation Sans', dashName='bxDash'):
        self.zin = zipfile.ZipFile(base)
        content = self.zin.read('content.xml').decode()
        self.head = content[:content.find('<office:automatic-styles>')]
        if '<office:font-face-decls>' not in self.head:
            raise SystemExit(f'{base}: no font-face-decls in content.xml')
        if font not in self.head:
            raise SystemExit(f'{base}: font {font!r} is not declared; pick one of: '
                             + ', '.join(re.findall(r'style:font-face style:name="([^"]+)"', self.head)))
        self.styles = self.zin.read('styles.xml').decode()
        if 'draw:name="Arrow"' not in self.styles:
            raise SystemExit(f'{base}: no "Arrow" marker in styles.xml; draw one arrow in Draw first')
        self.font, self.dashName = font, dashName
        self.gstyles, self.pstyles, self.tstyles, self.shapes = {}, {}, {}, []

    # ---- styles, shared by shapes that look the same ----
    def _g(self, **kw):
        key = tuple(sorted(kw.items()))
        return self.gstyles.setdefault(key, f'gr{len(self.gstyles) + 1}')

    def _t(self, size, bold, italic, color):
        key = (size, bold, italic, color)
        return self.tstyles.setdefault(key, f'T{len(self.tstyles) + 1}')

    def _p(self, align):
        return self.pstyles.setdefault(align, f'P{len(self.pstyles) + 1}')

    def _paras(self, lines, align):
        ps = self._p(align)
        return ''.join(f'<text:p text:style-name="{ps}"><text:span text:style-name="{self._t(*rest)}">'
                       f'{escape(text)}</text:span></text:p>' for text, *rest in lines)

    # ---- shapes ----
    def box(self, x, y, w, h, fill, stroke, lines=(), valign='middle', align='center', dash=False,
            strokeW='0.05cm'):
        """A filled rectangle with its own text."""
        gs = self._g(kind='box', fill=fill, stroke=stroke, valign=valign, dash=dash, strokeW=strokeW)
        self.shapes.append(
            f'<draw:custom-shape draw:style-name="{gs}" draw:layer="layout" svg:width="{w}cm" '
            f'svg:height="{h}cm" svg:x="{x}cm" svg:y="{y}cm">{self._paras(lines, align)}'
            '<draw:enhanced-geometry svg:viewBox="0 0 21600 21600" draw:type="rectangle" '
            'draw:enhanced-path="M 0 0 L 21600 0 21600 21600 0 21600 0 0 Z N"/></draw:custom-shape>')

    def text(self, x, y, w, h, lines, align='center'):
        """Free text, no border, no fill."""
        gs = self._g(kind='text')
        self.shapes.append(
            f'<draw:frame draw:style-name="{gs}" draw:layer="layout" svg:width="{w}cm" svg:height="{h}cm" '
            f'svg:x="{x}cm" svg:y="{y}cm"><draw:text-box>{self._paras(lines, align)}</draw:text-box>'
            '</draw:frame>')

    def line(self, x1, y1, x2, y2, start=False, end=True, color='#333333', width='0.045cm', dash=False):
        """A straight line; start/end put an arrowhead at that end."""
        gs = self._g(kind='line', start=start, end=end, color=color, width=width, dash=dash)
        self.shapes.append(
            f'<draw:line draw:style-name="{gs}" draw:layer="layout" svg:x1="{x1}cm" svg:y1="{y1}cm" '
            f'svg:x2="{x2}cm" svg:y2="{y2}cm"><text:p/></draw:line>')

    def frame(self, inset=1.0, color='#f10d0c', width='0.12cm'):
        """The red presentation frame, inset from the page edge."""
        pw, ph = pageSize(self.styles)
        a, b, c, d = inset, inset, pw - inset, ph - inset
        for x1, y1, x2, y2 in ((a, b, c, b), (c, b, c, d), (c, d, a, d), (a, d, a, b)):
            self.line(x1, y1, x2, y2, start=False, end=False, color=color, width=width)

    # ---- writing ----
    def _gprops(self, key):
        d = dict(key)
        stroke = (f' draw:stroke="dash" draw:stroke-dash="{self.dashName}"' if d.get('dash')
                  else ' draw:stroke="solid"')
        if d['kind'] == 'box':
            return (f'<style:graphic-properties{stroke} svg:stroke-width="{d["strokeW"]}" '
                    f'svg:stroke-color="{d["stroke"]}" draw:fill="solid" draw:fill-color="{d["fill"]}" '
                    'draw:textarea-horizontal-align="justify" '
                    f'draw:textarea-vertical-align="{d["valign"]}" draw:auto-grow-height="false" '
                    'fo:padding-top="0.12cm" fo:padding-bottom="0.12cm" fo:padding-left="0.25cm" '
                    'fo:padding-right="0.25cm" fo:wrap-option="wrap"/>')
        if d['kind'] == 'text':
            return ('<style:graphic-properties draw:stroke="none" draw:fill="none" '
                    'draw:textarea-horizontal-align="justify" draw:textarea-vertical-align="middle" '
                    'draw:auto-grow-height="false" draw:auto-grow-width="false" fo:padding-top="0cm" '
                    'fo:padding-bottom="0cm" fo:padding-left="0cm" fo:padding-right="0cm"/>')
        marks = ''.join(f' draw:marker-{end}="Arrow" draw:marker-{end}-width="0.3cm"'
                        for end in ('start', 'end') if d[end])
        return (f'<style:graphic-properties{stroke} svg:stroke-width="{d["width"]}" '
                f'svg:stroke-color="{d["color"]}"{marks} draw:fill="none"/>')

    def write(self, out):
        auto = '<office:automatic-styles><style:style style:name="dp1" style:family="drawing-page"/>'
        for key, name in self.gstyles.items():
            auto += (f'<style:style style:name="{name}" style:family="graphic" '
                     f'style:parent-style-name="standard">{self._gprops(key)}</style:style>')
        for align, name in self.pstyles.items():
            a = {'left': 'start', 'right': 'end'}.get(align, 'center')
            auto += (f'<style:style style:name="{name}" style:family="paragraph">'
                     f'<style:paragraph-properties fo:text-align="{a}"/></style:style>')
        for (size, bold, italic, color), name in self.tstyles.items():
            auto += (f'<style:style style:name="{name}" style:family="text"><style:text-properties '
                     f'style:font-name="{self.font}" fo:font-size="{size}pt" fo:color="{color}" '
                     f'fo:font-weight="{"bold" if bold else "normal"}" '
                     f'fo:font-style="{"italic" if italic else "normal"}"/></style:style>')
        auto += '</office:automatic-styles>'
        body = ('<office:body><office:drawing><draw:page draw:name="page1" draw:style-name="dp1" '
                'draw:master-page-name="Default">' + ''.join(self.shapes)
                + '</draw:page></office:drawing></office:body></office:document-content>')
        styles = self.styles
        if f'draw:name="{self.dashName}"' not in styles:
            styles = styles.replace(
                '<office:styles>', f'<office:styles><draw:stroke-dash draw:name="{self.dashName}" '
                'draw:style="rect" draw:dots1="1" draw:dots1-length="0.25cm" draw:distance="0.15cm"/>', 1)
        repack(self.zin, out, {'content.xml': (self.head + auto + body).encode(),
                               'styles.xml': styles.encode()})
        print('wrote', out, len(self.shapes), 'shapes')


def repack(zin, out, replace):
    """Copy an .odg, replacing some members; mimetype first and stored; the stale thumbnail dropped."""
    with zipfile.ZipFile(out, 'w') as zout:
        zout.writestr(zipfile.ZipInfo('mimetype'), zin.read('mimetype'), compress_type=zipfile.ZIP_STORED)
        for item in zin.infolist():
            if item.filename in ('mimetype', 'Thumbnails/thumbnail.png'):
                continue
            data = replace.get(item.filename, zin.read(item.filename))
            if item.filename == 'META-INF/manifest.xml':
                data = re.sub(rb'<manifest:file-entry[^>]*Thumbnails/thumbnail.png"[^>]*/>', b'', data)
            zout.writestr(item, data, compress_type=zipfile.ZIP_DEFLATED)


def pageSize(styles):
    w = re.search(r'fo:page-width="([\d.]+)cm"', styles)
    h = re.search(r'fo:page-height="([\d.]+)cm"', styles)
    return float(w.group(1)), float(h.group(1))


def cmdList(path):
    content = zipfile.ZipFile(path).read('content.xml').decode()
    page = content[content.find('<draw:page'):]
    for m in re.finditer(r'<draw:(custom-shape|frame|line|connector|g|rect|ellipse|polyline|path)\b([^>]*)>',
                         page):
        kind, attrs = m.groups()
        a = dict(re.findall(r'([\w:-]+)="([^"]*)"', attrs))
        if kind == 'line' or kind == 'connector':
            geo = f'{a.get("svg:x1", "")},{a.get("svg:y1", "")} -> {a.get("svg:x2", "")},{a.get("svg:y2", "")}'
        else:
            geo = f'{a.get("svg:x", "")},{a.get("svg:y", "")} {a.get("svg:width", "")}x{a.get("svg:height", "")}'
        end = {'g': '>'}.get(kind) or f'</draw:{kind}>'
        inner = page[m.end():page.find(end, m.end())] if kind != 'g' else ''
        text = ' / '.join(t for t in (html.unescape(re.sub(r'<[^>]+>', '', p)) for p in re.findall(r'<text:p\b.*?</text:p>', inner))
                          if t)
        print(f'{kind:13} {geo:34} {a.get("draw:style-name", ""):6} {text[:70]}')


def cmdPage(path):
    z = zipfile.ZipFile(path)
    styles, content = z.read('styles.xml').decode(), z.read('content.xml').decode()
    print('page (cm):', '%.2f x %.2f' % pageSize(styles))
    print('fonts:', ', '.join(sorted(set(re.findall(r'style:font-face style:name="([^"]+)"', content + styles)))))
    print('markers:', ', '.join(re.findall(r'<draw:marker draw:name="([^"]+)"', styles)) or 'none')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('list', 'page'):
        raise SystemExit(__doc__)
    {'list': cmdList, 'page': cmdPage}[sys.argv[1]](sys.argv[2])
