import pygame as pg
import logging
from typing import Tuple, Dict
from copy import deepcopy

def get_styles(tag: str) -> Tuple[bool]:
    bold: bool = False
    italic: bool = False
    underline: bool = False
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

        self.base_styles: Dict[str, any] = {
            'color': base_color,
            'background-color': background_color,
            'font': font_name,
            'font-size': default_size,
            'padding': padding, # 0: top, 1: right, 2: bottom, 3: left

            'bold': False,
            'italic': False,
            'underline': False,
        }
        
        # mutable variables
        self.rendered_text: pg.Surface = pg.Surface((self.wrap_px, self.render_height))
        self.rendered_text.fill((255, 255, 255))
        
    def render(self) -> pg.Surface:
        # clear the previous text
        self.rendered_text.fill(self.base_styles['background-color'])
        
        # styles
        styles = deepcopy(self.base_styles)
        
        text_font: pg.Font = pg.font.SysFont(styles['font'], styles['font-size'], styles['bold'], styles['italic'])
        
        tag_text: str = ""
        in_tag: bool = False
        
        curr_x: int = styles['padding'][3]
        curr_y: int = styles['padding'][0]
        largetst_y: int = 0
        
        for char in self.html_text:
            # entered tag
            if char == '<':
                in_tag = True
                
            # exited tag
            elif char == '>':
                # apply styles
                styles['bold'], styles['italic'], styles['underline'], line_break = get_styles(tag_text)

                # br tag
                if line_break:
                    curr_x, curr_y = feed_line(curr_x, curr_y, largetst_y, 16, styles['padding'])
                    curr_x += 15 * (styles['font-size'] / 16)
                
                # reload font with the new attributes
                text_font = pg.font.SysFont(styles['font'], styles['font-size'], styles['bold'], styles['italic'])
                
                # reset tag vars
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
                    curr_x, curr_y = feed_line(curr_x, curr_y, largetst_y, 16, styles['padding'])
                    largetst_y = 0
                
                try: new_char: pg.Surface = text_font.render(char, True, styles['color'], styles['background-color'])
                except Exception as e: logging.warning(f"Error while creating character surface! Continuing anyway...    Error: '{str(e)}'")

                char_width: int = new_char.get_width()
                char_height: int = new_char.get_height()

                if char_height > largetst_y:
                    largetst_y = char_height
                
                # text wrapping
                if curr_x + char_width > self.wrap_px - styles['padding'][1]:
                    curr_x, curr_y = feed_line(curr_x, curr_y, largetst_y, char_height, styles['padding'])
                    curr_x += 15 * (styles['font-size'] / 16)
                    largetst_y = 0
                    
                self.rendered_text.blit(new_char, (curr_x, curr_y))

                # underline
                if styles['underline']:
                    pg.draw.line(self.rendered_text, styles['color'], (curr_x, curr_y+char_height), (curr_x+char_width, curr_y+char_height))
                    
                curr_x += char_width + 1
                
        return self.rendered_text