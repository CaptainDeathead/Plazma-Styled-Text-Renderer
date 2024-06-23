import pygame as pg
from copy import deepcopy
from typing import Dict
from os import getcwd

class FontManager:
    FONT_PATH: str = getcwd() + "/Engine/STR/fonts/"

    def __init__(self) -> None:
        self.fonts: Dict[str, str] = {
            "andale": "andale.ttf",
            "arial black": "arial_black.ttf",
            "arial": "arial.ttf",
            "baskerville": "baskerville.ttf",
            "bradley hand": "bradley_hand.ttf",
            "brush script mt": "brush_script_mt.ttf",
            "brush script": "brush_script_mt.ttf",
            "comic sans ms": "comic_sans_ms.ttf",
            "comic sans": "comic_sans_ms.ttf",
            "courier": "courier.ttf",
            "georgia": "georgia.ttf",
            "gill sans": "gill_sans.ttf",
            "helvetica": "helvetica.ttf",
            "impact": "impact.ttf",
            "luminari": "luminari.ttf",
            "monaco": "monaco.ttf",
            "palatino": "palatino.ttf",
            "tahoma": "tahoma.ttf",
            "times new roman": "times_new_roman.ttf",
            "times new": "times_new_roman.ttf",
            "times": "times_new_roman.ttf",
            "trebuchet ms": "trebuchet_ms.ttf",
            "trebuchet": "trebuchet_ms.ttf",
            "verdana": "verdana.ttf"
        }

        self.font_cache: Dict[str, Dict[int, pg.Font]] = {}

    def add_font(self, font_name: str, size: int) -> str:
        font_name = self.fonts.get(font_name, 'arial.ttf')
        
        if font_name in self.font_cache:
            self.font_cache[font_name][size] = pg.font.Font(self.FONT_PATH + font_name, size)
        else:
            self.font_cache[font_name] = {size: pg.font.Font(self.FONT_PATH + font_name, size)}

        return font_name

    def get_font(self, font_name: str, size: int) -> pg.Font:
        if font_name in self.font_cache:
            if size in self.font_cache[font_name]:
                return self.font_cache[font_name][size]
        
        # if no font was returned
        font_name = self.add_font(font_name, size)

        return self.get_font(font_name, size)