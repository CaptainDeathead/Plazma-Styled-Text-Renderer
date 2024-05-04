import pygame as pg
from typing import Tuple, List

def get_styles(tag: str, bold: bool, italic: bool, underline: bool) -> Tuple[bool]:
    line_break: bool = False

    # apply styles
    if tag in ("b", "strong"):
        bold = True
    elif tag == "i":
        italic = True
    elif tag == "u":
        underline = True
    elif tag == "br/":
        line_break = True
    else:
        # check if it is a closing tag
        if tag[0] == "/":
            # remove styles
            if tag in ("/b", "/strong"):
                bold = False
            elif tag == "/i":
                italic = False
            elif tag == "/u":
                underline = False
                
    return (bold, italic, underline, line_break)

def feed_line(current_x: int, current_y: int, line_size: int, default_line_size: int, padding: Tuple[int]) -> Tuple[int]:
    if line_size == 0:
        line_size = default_line_size

    current_x = padding[3]
    current_y += line_size + padding[0]

    return (current_x, current_y)

class StyledText:
    def __init__(self, html_text: str, wrap_px: int, render_height: int, base_color: Tuple[int], background_color: Tuple[int], font_name: str, default_size: int, padding: Tuple[int]) -> None:
        # setup variables
        self.html_text: str = html_text
        self.wrap_px: int = wrap_px
        self.render_height: int = render_height
        self.base_color: Tuple[int] = base_color
        self.background_color: Tuple[int] = background_color
        self.font_name: str = font_name
        self.default_size: int = default_size
        self.padding: Tuple[int] = padding # 0: top, 1: right, 2: bottom, 3: left
        
        # mutable variables
        self.rendered_text: pg.Surface = pg.Surface((self.wrap_px, self.render_height))
        self.rendered_text.fill((255, 255, 255))
        
    def render(self) -> pg.Surface:
        # clear the previous text
        self.rendered_text.fill(self.background_color)
        
        # styles
        bold: bool = False
        italic: bool = False
        underline: bool = False
        color: Tuple[int] = self.base_color
        bg_color: Tuple[int] = self.background_color
        font_name: str = self.font_name
        size: int = self.default_size
        
        text_font: pg.Font = pg.font.SysFont(font_name, size, bold, italic)
        
        tag: str = ""
        tag_text: str = ""
        in_tag: bool = False
        
        curr_x: int = self.padding[3]
        curr_y: int = self.padding[0]
        largetst_y: int = 0
        
        for char in self.html_text:
            # entered tag
            if char == '<':
                in_tag = True
                
            # exited tag
            elif char == '>':
                # apply styles
                bold, italic, underline, line_break = get_styles(tag_text, bold, italic, underline)

                # br tag
                if line_break:
                    curr_x, curr_y = feed_line(curr_x, curr_y, largetst_y, 16, self.padding)
                    curr_x += 15 * (self.default_size / 16)
                
                # reload font with the new attributes
                text_font = pg.font.SysFont(font_name, size, bold, italic)
                
                in_tag = False
                tag_text = ""
                
            # in tag
            elif in_tag:
                if char == " ":
                    # check for whitespace at the start
                    if tag_text == "": continue
                    else:
                        tag_text += char
                
                else:
                    tag_text += char
                    
            # text
            else:
                # newline
                if char == '\n':
                    # wrap text
                    curr_x, curr_y = feed_line(curr_x, curr_y, largetst_y, 16, self.padding)
                    largetst_y = 0
                
                new_char: pg.Surface = text_font.render(char, True, color, bg_color)

                char_width: int = new_char.get_width()
                char_height: int = new_char.get_height()

                if char_height > largetst_y:
                    largetst_y = char_height
                
                # text wrapping
                if curr_x + char_width > self.wrap_px - self.padding[1]:
                    curr_x, curr_y = feed_line(curr_x, curr_y, largetst_y, char_height, self.padding)
                    curr_x += 15 * (self.default_size / 16)
                    largetst_y = 0
                    
                self.rendered_text.blit(new_char, (curr_x, curr_y))

                # underline
                if underline:
                    pg.draw.line(self.rendered_text, color, (curr_x, curr_y+char_height), (curr_x+char_width, curr_y+char_height))
                    
                curr_x += char_width + 1
                
        return self.rendered_text