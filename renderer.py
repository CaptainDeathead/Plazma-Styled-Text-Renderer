import pygame as pg
import logging
import warnings
from typing import Tuple, Dict
from copy import deepcopy

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

# TODO: Make this actually convert the units rather than replace the strings
def remove_units(num_str: str) -> str:
    return num_str.replace("cm", "").replace("mm", "").replace("in", "").replace("pc", "").replace("pt", "").replace("px", "")

def add_style(style_with_value: Tuple[str, str], styles: Dict[str, any]) -> None:
    style, value = style_with_value

    if style == "font": styles["font"] = value
    elif style == "font-size": styles["font-size"] = int(remove_units(value))

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

        self.curr_x: float = self.base_styles["padding"][3]
        self.curr_y: float = self.base_styles["padding"][0]
        self.largest_y: float = 0
        
        # mutable variables
        self.rendered_text: pg.Surface = pg.Surface((self.wrap_px, self.render_height))
        self.clear()

    def clear(self) -> pg.Surface:
        self.renderText('\n')
        self.rendered_text.fill(self.base_styles['background-color'])
        return self.rendered_text
    
    def renderText(self, html_text: str, tag_styles: Dict[str, any] = None):
        # styles
        styles = deepcopy(self.base_styles)

        if tag_styles is not None:
            for style in tag_styles:
                add_style((style, tag_styles[style]), styles)
                #styles[style] = tag_styles[style]
        
        text_font: pg.Font = pg.font.SysFont(styles['font'], styles['font-size'], styles['bold'], styles['italic'])
        
        tag_text: str = ""
        in_tag: bool = False
        
        for char in html_text:
            # entered tag
            if char == '<':
                in_tag = True
                
            # exited tag
            elif char == '>':
                # apply styles
                styles['bold'], styles['italic'], styles['underline'], line_break = get_styles(tag_text, styles['bold'], styles['italic'], styles['underline'])

                # br tag
                if line_break:
                    self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, 16, styles['padding'])
                    self.curr_x += 15 * (styles['font-size'] / 16)
                
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
                    self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, 16, styles['padding'])
                    self.largest_y = 0
                
                try: new_char: pg.Surface = text_font.render(char, True, styles['color'], styles['background-color'])
                except Exception as e: logging.warning(f"Error while creating character surface! Continuing anyway...    Error: '{str(e)}'")

                char_width: int = new_char.get_width()
                char_height: int = new_char.get_height()

                if char_height > self.largest_y:
                    self.largest_y = char_height
                
                # text wrapping
                if self.curr_x + char_width > self.wrap_px - styles['padding'][1]:
                    self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, char_height, styles['padding'])
                    self.curr_x += 15 * (styles['font-size'] / 16)
                    self.largest_y = 0
                    
                self.rendered_text.blit(new_char, (self.curr_x, self.curr_y))

                # underline
                if styles['underline']:
                    pg.draw.line(self.rendered_text, styles['color'], (self.curr_x, self.curr_y+char_height),
                                 (self.curr_x+char_width, self.curr_y+char_height))
                    
                self.curr_x += char_width + 1
                
        return self.rendered_text

    def renderAll(self) -> pg.Surface:
        warnings.warn("This function is inneficiant and outdated! Consider using 'renderText' instead.")

        # styles
        styles = deepcopy(self.base_styles)
        
        text_font: pg.Font = pg.font.SysFont(styles['font'], styles['font-size'], styles['bold'], styles['italic'])
        
        tag_text: str = ""
        in_tag: bool = False
        
        curr_x: float = styles['padding'][3]
        curr_y: float = styles['padding'][0]
        largetst_y: float = 0
        
        for char in self.html_text:
            # entered tag
            if char == '<':
                in_tag = True
                
            # exited tag
            elif char == '>':
                # apply styles
                styles['bold'], styles['italic'], styles['underline'], line_break = get_styles(tag_text, styles['bold'], styles['italic'], styles['underline'])

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