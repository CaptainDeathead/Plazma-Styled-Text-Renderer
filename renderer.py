import pygame as pg
import logging
import time
from typing import List, Tuple, Dict
from Engine.STR.font import FontManager
from Ui.elements import DEFUALT_BG_COLOR

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

def feed_line(x: int, current_y: int, line_size: int, default_line_size: int, padding_y: int) -> Tuple[int]:
    if line_size == 0:
        line_size = default_line_size

    current_y += line_size + padding_y

    return (x, current_y)

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

def merge_secondary_dict(dict1: Dict[any, any], dict2: Dict[any, any]) -> Dict[any, any]:
    for key in dict2:
        if key not in dict1:
            dict1[key] = dict2[key]

    return dict1

class StyledText:
    def __init__(self, html_text: str, width: int, height: int, screenshot_saver: bool = False) -> None:
        
        # setup variables
        self.html_text: str = html_text
        self.width: int = width
        self.height: int = height

        self.screenshot_saver: bool = screenshot_saver

        self.font_manager: FontManager = FontManager()
        
        # mutable variables     
        self.rendered_text: pg.Surface = pg.Surface((self.width, self.height))

        self.clear()

    def clear(self) -> None:
        self.rendered_text = pg.Surface((self.width, self.height))

        self.rendered_text.fill(DEFUALT_BG_COLOR)
        #self.renderStyledText('\n')
    
    def renderStyledText(self, text: str, font: Tuple[str, int], font_type: Tuple[bool, bool, bool], color: Tuple[int, int, int],
                         background_color: Tuple[int, int, int], x: int, y: int, max_width: int = 0, max_height: int = 0,
                         padding_y: int = 0) -> Tuple[pg.Rect, pg.Rect]:
        # styles
        #styles: Dict[str, any] = merge_secondary_dict(tag_styles, self.base_styles)

        font, font_size = font

        bold, italic, underline = font_type

        text_font: pg.Font = self.font_manager.get_font(font, font_size)
        text_font.set_bold(bold)
        text_font.set_italic(italic)

        text_rects: List[pg.Rect] = []

        curr_x: int = x
        curr_y: int = y
        largest_y: int = 0

        for char in text:
            # newline
            if char == '\n':
                # wrap text
                curr_x, curr_y = feed_line(x, curr_y, largest_y, 16, padding_y)
                largest_y = 0
            
            try: new_char: pg.Surface = text_font.render(char, True, color, background_color)
            except Exception as e:
                logging.warning(f"Error while creating character surface! Continuing anyway...    Error: '{str(e)}'")
                continue

            char_rect: pg.Rect = new_char.get_rect()

            text_rects.append(pg.Rect(curr_x, curr_y, char_rect.width, char_rect.height))

            char_width: int = new_char.get_width()
            char_height: int = new_char.get_height()

            if char_height > largest_y:
                largest_y = char_height
            
            if curr_x + char_width > self.rendered_text.get_width():
                resized_rendered_text: pg.Surface = pg.Surface((self.rendered_text.get_width()+self.width, self.rendered_text.get_height()))
                resized_rendered_text.fill(background_color)
                resized_rendered_text.blit(self.rendered_text, (0, 0))
                self.rendered_text = resized_rendered_text

            elif curr_y + char_height > self.rendered_text.get_height():
                resized_rendered_text: pg.Surface = pg.Surface((self.rendered_text.get_width(), self.rendered_text.get_height()+self.height))
                resized_rendered_text.fill(background_color)
                resized_rendered_text.blit(self.rendered_text, (0, 0))
                self.rendered_text = resized_rendered_text

            # text wrapping
            #if curr_x + char_width > self.width - styles['padding'][1]:
            #    curr_x, curr_y = feed_line(curr_x, curr_y, largest_y, char_height, styles['padding'])
            #    curr_x += 15 * (styles['font-size'] / 16)
            #    largest_y = 0
            
            self.rendered_text.blit(new_char, (curr_x, curr_y))

            # underline
            if underline:
                pg.draw.line(self.rendered_text, color, (curr_x, curr_y+char_height),
                                (curr_x+char_width, curr_y+char_height))
                
            curr_x += char_width + 1

        if self.screenshot_saver: pg.image.save(self.rendered_text, "screenshots/" + str(time.time()) + ".png")

        sorted_text_rects_widths: List[pg.Rect] = sorted(text_rects, key=lambda rect: rect.x)

        try: total_rect: pg.Rect = pg.Rect(text_rects[0].x, text_rects[0].y, sorted_text_rects_widths[-1].x + sorted_text_rects_widths[-1].width - sorted_text_rects_widths[0].x, text_rects[-1].y + text_rects[-1].height - text_rects[0].y)
        except Exception as e:
            logging.warning(f"Error while creating character rect! Continuing anyway...    Error: '{str(e)}'")
            return pg.Rect(0, 0, 0, 0), pg.Rect(0, 0, 0, 0)

        last_text_end: float = text_rects[-1].x+text_rects[-1].width
        unused_rect: pg.Rect = pg.Rect(last_text_end, text_rects[-1].y, total_rect.x + total_rect.width-last_text_end, text_rects[-1].height)
        
        return total_rect, unused_rect