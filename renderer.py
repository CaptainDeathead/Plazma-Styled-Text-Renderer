import pygame as pg
import logging
import time
from typing import List, Tuple, Dict
from copy import deepcopy
from Engine.STR.font import FontManager
from math import floor
from config import LINK_NORMAL_COLOR, PRESSED_LINK_COLOR

def ishex(string: str) -> bool:
    if "#" not in string: return False

    try:
        int(string.replace('#', ''), 16)
        return True
    except: return False

def hex_to_rgb(hex_string: str) -> Tuple[int, int, int]:
    if len(hex_string) < 7:
        for _ in range(7-len(hex_string)): hex_string += "0"

    return tuple(int(hex_string[i:i+2], 16) for i in range(1, 6, 2))

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

def convert_keywords(string: str) -> Tuple[float, str] | None:
    if string == "xx-small": return (0.5625, "rem")
    elif string == "x-small": return (0.625, "rem")
    elif string == "small": return (0.8125, "rem")
    elif string == "medium": return (1.0, "rem")
    elif string == "large": return (1.125, "rem")
    elif string == "x-large": return (1.5, "rem")
    elif string == "xx-large": return (2.0, "rem")
    else: return None

def find_nums(string_with_nums: str) -> Tuple[float, str] | None:
    for i in range(len(string_with_nums)):
        if string_with_nums[i].isalpha() or string_with_nums[i] == '%':
            if string_with_nums[:i] == '': return None

            try: return float(string_with_nums[:i]), string_with_nums[i:]
            except: return None

    return convert_keywords(string_with_nums)

def remove_units(num_str: str, tag_size: float, parent_size: float, view_width: float, view_height: float) -> float:
    if type(num_str) == int or type(num_str) == float: return num_str

    num_str = num_str.lower().split(' ')[0]

    split_num: Tuple[float, str] | None = find_nums(num_str)

    if split_num is None: 
        if type(tag_size) == str: return 16
        else: return tag_size
    
    value, unit = split_num
    
    if unit == "cm": return value * 37.8
    elif unit == "mm": return value * 3.78
    elif unit == "q": return value * 0.945
    elif unit == "in": return value * 96
    elif unit == "pc": return value * 16
    elif unit == "pt": return value * 1.333333
    elif unit == "px": return value

    # relative sizes
    elif unit == "em": return value * parent_size
    elif unit == "rem": return value * tag_size
    elif unit == "vw": return view_width / value
    elif unit == "vh": return view_height / value
    elif unit == "%":
        if type(tag_size) == str: return 16
        return tag_size * value / 100

    # Style not found    
    if type(tag_size) == str: return 16
    else: return tag_size

def add_style(style_with_value: Tuple[str, str], styles: Dict[str, any]):
    style, value = style_with_value

    if style == "font": styles["font"] = value
    elif style == "font-size": styles["font-size"] = int(remove_units(value, styles.get("text-tag-size", 16), styles.get("parent-tag-size", 16), styles["view-width"], styles["view-height"]))
    elif style == "background-color" or style == "color" and (type(value) == tuple or type(value) == str):
        if ishex(value): styles[style] = hex_to_rgb(value)
        else: styles[style] = value

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
    def __init__(self, html_text: str, wrap_px: int, render_height: int, base_color: Tuple[int], background_color: Tuple[int],
                 font_name: str, default_size: int, padding: Tuple[int], screenshot_saver: bool = False) -> None:
        
        # setup variables
        self.html_text: str = html_text
        self.wrap_px: int = wrap_px
        self.render_height: int = render_height

        self.screenshot_saver: bool = screenshot_saver

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

        self.total_x: float = self.base_styles["padding"][3]
        self.total_y: float = self.base_styles["padding"][0]
        self.largest_y: float = 0
        
        # mutable variables     
        self.rendered_text: pg.Surface = pg.Surface((self.wrap_px, self.render_height))

        self.clear()

    def clear(self) -> None:
        self.total_x = self.base_styles["padding"][3]
        self.total_y = self.base_styles["padding"][0]

        self.rendered_text = pg.Surface((self.wrap_px, self.render_height))

        self.rendered_text.fill((255, 255, 255))
        self.renderStyledText('\n')
    
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
                self.total_x, self.total_y = feed_line(self.total_x, self.total_y, self.largest_y, 16, styles['padding'])
                self.largest_y = 0
            
            try: new_char: pg.Surface = text_font.render(char, True, styles['color'], styles['background-color'])
            except Exception as e:
                logging.warning(f"Error while creating character surface! Continuing anyway...    Error: '{str(e)}'")
                continue

            char_rect: pg.Rect = new_char.get_rect()

            text_rects.append(pg.Rect(self.total_x, self.total_y, char_rect.width, char_rect.height))

            char_width: int = new_char.get_width()
            char_height: int = new_char.get_height()

            if char_height > self.largest_y:
                self.largest_y = char_height
            
            if self.total_x + char_width > self.rendered_text.get_width():
                resized_rendered_text: pg.Surface = pg.Surface((self.rendered_text.get_width()+self.wrap_px, self.rendered_text.get_height()))
                resized_rendered_text.fill((255, 255, 255))
                resized_rendered_text.blit(self.rendered_text, (0, 0))
                self.rendered_text = resized_rendered_text

            elif self.total_y + char_height > self.rendered_text.get_height():
                resized_rendered_text: pg.Surface = pg.Surface((self.rendered_text.get_width(), self.rendered_text.get_height()+self.render_height))
                resized_rendered_text.fill((255, 255, 255))
                resized_rendered_text.blit(self.rendered_text, (0, 0))
                self.rendered_text = resized_rendered_text

            # text wrapping
            #if self.total_x + char_width > self.wrap_px - styles['padding'][1]:
            #    self.total_x, self.total_y = feed_line(self.total_x, self.total_y, self.largest_y, char_height, styles['padding'])
            #    self.total_x += 15 * (styles['font-size'] / 16)
            #    self.largest_y = 0
            
            self.rendered_text.blit(new_char, (self.total_x, self.total_y))

            # underline
            if styles['underline']:
                pg.draw.line(self.rendered_text, styles['color'], (self.total_x, self.total_y+char_height),
                                (self.total_x+char_width, self.total_y+char_height))
                
            self.total_x += char_width + 1

        if self.screenshot_saver: pg.image.save(self.rendered_text, "screenshots/" + str(time.time()) + ".png")

        sorted_text_rects_widths: List[pg.Rect] = sorted(text_rects, key=lambda rect: rect.x)

        try: total_rect: pg.Rect = pg.Rect(text_rects[0].x, text_rects[0].y, sorted_text_rects_widths[-1].x + sorted_text_rects_widths[-1].width - sorted_text_rects_widths[0].x, text_rects[-1].y + text_rects[-1].height - text_rects[0].y)
        except Exception as e:
            logging.warning(f"Error while creating character rect! Continuing anyway...    Error: '{str(e)}'")
            return pg.Rect(0, 0, 0, 0), pg.Rect(0, 0, 0, 0)

        last_text_end: float = text_rects[-1].x+text_rects[-1].width
        unused_rect: pg.Rect = pg.Rect(last_text_end, text_rects[-1].y, total_rect.x + total_rect.width-last_text_end, text_rects[-1].height)
        
        return total_rect, unused_rect