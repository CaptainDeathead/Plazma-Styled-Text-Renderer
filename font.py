import pygame as pg
from copy import deepcopy
from typing import Dict

class FontManager:
    def __init__(self) -> None:
        self.font_cache: Dict[str, Dict[int, pg.Font]] = {}

    def add_font(self, font_name: str, size: int):
        if font_name in self.font_cache:
            self.font_cache[font_name][size] = pg.font.SysFont(font_name, size)
        else:
            self.font_cache[font_name] = {size: pg.font.SysFont(font_name, size)}

    def get_font(self, font_name: str, size: int) -> pg.Font:
        if font_name in self.font_cache:
            if size in self.font_cache[font_name]:
                return self.font_cache[font_name][size]
        
        # if no font was returned
        self.add_font(font_name, size)

        return self.get_font(font_name, size)