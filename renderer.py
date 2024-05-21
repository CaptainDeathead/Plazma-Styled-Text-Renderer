import pygame as pg
import logging
from typing import List, Tuple, Dict
from copy import deepcopy
from Engine.STR.font import FontManager
from math import floor
from config import LINK_NORMAL_COLOR, PRESSED_LINK_COLOR

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
    return num_str.replace("cm", "").replace("mm", "").replace("in", "").replace("pc", "").replace("pt", "").replace("px", "").replace("%", "")

def add_style(style_with_value: Tuple[str, str], styles: Dict[str, any]):
    style, value = style_with_value

    if style == "font": styles["font"] = value
    elif style == "font-size": styles["font-size"] = int(remove_units(value))
    else: styles[style] = value

def feed_line(current_x: int, current_y: int, line_size: int, default_line_size: int, padding: Tuple[int]) -> Tuple[int]:
    if line_size == 0:
        line_size = default_line_size

    current_x = padding[3]
    current_y += line_size + padding[0]

    return (current_x, current_y)

def surface_from_list(surface_list: List[pg.Surface]) -> pg.Surface:
    size_x: float = 0.0
    size_y: float = 0.0

    surface_sizes: List[Tuple[float, float]] = []
    
    # pre-calculate the size of the new surface
    for surface in surface_list:
        surface_size = surface.get_size()

        size_x += surface_size[0]
        size_y += surface_size[1]
        surface_sizes.append(surface_size)

    new_surface: pg.Surface = pg.Surface((size_x, size_y))    

    for i, surface in enumerate(surface_list):
        new_surface.blit(surface, surface_sizes[i])

    return new_surface

class StyledText:
    def __init__(self, html_text: str, wrap_px: int, render_height: int, base_color: Tuple[int], background_color: Tuple[int], font_name: str, default_size: int, padding: Tuple[int]) -> None:
        # setup variables
        self.html_text: str = html_text
        self.wrap_px: int = wrap_px
        self.render_height: int = render_height

        self.font_manager: FontManager = FontManager()

        self.base_styles: Dict[str, any] = {
            'color': base_color,
            'background-color': background_color,
            'font': font_name,
            'font-size': default_size,
            'padding': padding, # 0: top, 1: right, 2: bottom, 3: left

            'bold': False,
            'italic': False,
            'underline': False,

            'link': False
        }

        self.curr_x: float = self.base_styles["padding"][3]
        self.curr_y: float = self.base_styles["padding"][0]
        self.largest_y: float = 0
        
        # mutable variables
        self.rendered_text_screens: List[pg.Surface] = [pg.Surface((self.wrap_px, self.render_height)), pg.Surface((self.wrap_px, self.render_height))]
        self.curr_screen: int = 0
        self.clear()

    def clear(self) -> List[pg.Surface]:
        self.curr_x = self.base_styles["padding"][3]
        self.curr_y = self.base_styles["padding"][0]

        self.curr_screen = 0
        self.rendered_text_screens = [pg.Surface((self.wrap_px, self.render_height)), pg.Surface((self.wrap_px, self.render_height))]
        
        for screen in self.rendered_text_screens: screen.fill((255, 255, 255))

        self.renderStyledText('\n')

        return self.rendered_text_screens

    def renderHTMLText(self, html_text: str, tag_styles: Dict[str, any] = None) -> Tuple[pg.Rect, pg.Rect]:
        # styles
        styles = deepcopy(self.base_styles)

        if tag_styles is not None:
            for style in tag_styles:
                add_style((style, tag_styles[style]), styles)
        
        text_font: pg.Font = self.font_manager.get_font(styles['font'], styles['font-size'])
        text_font.set_bold(styles['bold'])
        text_font.set_italic(styles['italic'])

        tag_text: str = ""
        in_tag: bool = False

        text_rects: List[pg.Rect] = []
        
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
                text_font = self.font_manager.get_font(styles['font'], styles['font-size'])
                text_font.set_bold(styles['bold'])
                text_font.set_italic(styles['italic'])
                
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
                except Exception as e:
                    logging.warning(f"Error while creating character surface! Continuing anyway...    Error: '{str(e)}'")
                    continue

                text_rects.append(new_char.get_rect())

                char_width: int = new_char.get_width()
                char_height: int = new_char.get_height()

                if char_height > self.largest_y:
                    self.largest_y = char_height
                
                # text wrapping
                if self.curr_x + char_width > self.wrap_px - styles['padding'][1]:
                    self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, char_height, styles['padding'])
                    self.curr_x += 15 * (styles['font-size'] / 16)
                    self.largest_y = 0
                    
                self.curr_screen = floor((self.curr_y) / self.render_height)

                if self.curr_screen != floor((self.curr_y+char_height) / self.render_height):
                    self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, char_height, styles['padding'])
                    self.curr_screen = floor((self.curr_y+char_height) / self.render_height)

                if self.curr_screen > len(self.rendered_text_screens) - 1:
                    new_surf: pg.Surface = pg.Surface((self.wrap_px, self.render_height))
                    new_surf.fill((255, 255, 255))
                    self.rendered_text_screens.append(new_surf)

                self.rendered_text_screens[self.curr_screen].blit(new_char, (self.curr_x, (self.curr_y%self.render_height)))

                # underline
                if styles['underline']:
                    pg.draw.line(self.rendered_text_screens[self.curr_screen], styles['color'], (self.curr_x, self.curr_y+char_height),
                                 (self.curr_x+char_width, self.curr_y+char_height))
                    
                self.curr_x += char_width + 1

        total_rect: pg.Rect = pg.Rect(text_rects[0].x, text_rects[0].y, self.wrap_px, text_rects[-1].y - text_rects[0].y)

        last_text_end: float = text_rects[-1].x+text_rects[-1].width
        unused_rect: pg.Rect = pg.Rect(last_text_end, text_rects[-1].y, total_rect.width-last_text_end, self.largest_y)
                
        return total_rect, unused_rect
    
    def renderStyledText(self, text: str, tag_styles: Dict[str, any] = None) -> Tuple[pg.Rect, pg.Rect]:
        # styles
        styles = deepcopy(self.base_styles)

        if tag_styles is not None:
            for style in tag_styles:
                add_style((style, tag_styles[style]), styles)

        text_font: pg.Font = self.font_manager.get_font(styles['font'], styles['font-size'])
        text_font.set_bold(styles['bold'])
        text_font.set_italic(styles['italic'])

        text_rects: List[pg.Rect] = []

        for char in text:
            # newline
            if char == '\n':
                # wrap text
                self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, 16, styles['padding'])
                self.largest_y = 0
            
            try: new_char: pg.Surface = text_font.render(char, True, styles['color'], styles['background-color'])
            except Exception as e:
                logging.warning(f"Error while creating character surface! Continuing anyway...    Error: '{str(e)}'")
                continue

            text_rects.append(new_char.get_rect())

            char_width: int = new_char.get_width()
            char_height: int = new_char.get_height()

            if char_height > self.largest_y:
                self.largest_y = char_height
            
            # text wrapping
            if self.curr_x + char_width > self.wrap_px - styles['padding'][1]:
                self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, char_height, styles['padding'])
                self.curr_x += 15 * (styles['font-size'] / 16)
                self.largest_y = 0
                
            self.curr_screen = floor((self.curr_y) / self.render_height)

            if self.curr_screen != floor((self.curr_y+char_height) / self.render_height):
                self.curr_x, self.curr_y = feed_line(self.curr_x, self.curr_y, self.largest_y, char_height, styles['padding'])
                self.curr_screen = floor((self.curr_y+char_height) / self.render_height)

            if self.curr_screen > len(self.rendered_text_screens) - 1:
                new_surf: pg.Surface = pg.Surface((self.wrap_px, self.render_height))
                new_surf.fill((255, 255, 255))
                self.rendered_text_screens.append(new_surf)

            self.rendered_text_screens[self.curr_screen].blit(new_char, (self.curr_x, (self.curr_y%self.render_height)))

            # underline
            if styles['underline']:
                pg.draw.line(self.rendered_text_screens[self.curr_screen], styles['color'], (self.curr_x, self.curr_y+char_height),
                                (self.curr_x+char_width, self.curr_y+char_height))
                
            self.curr_x += char_width + 1

        total_rect: pg.Rect = pg.Rect(text_rects[0].x, text_rects[0].y, self.wrap_px, text_rects[-1].y - text_rects[0].y)

        last_text_end: float = text_rects[-1].x+text_rects[-1].width
        unused_rect: pg.Rect = pg.Rect(last_text_end, text_rects[-1].y, total_rect.width-last_text_end, self.largest_y)
                
        return total_rect, unused_rect