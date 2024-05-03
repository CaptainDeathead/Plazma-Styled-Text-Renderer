import pygame as pg
from renderer import StyledText

pg.init()

screen: pg.Surface = pg.display.set_mode((800, 600))
pg.display.set_caption("Plazma Styled Text Renderer - Example")

test1: str = "this is normal <b>and this is bold</b> <i>and this is italic</i> and of course <u>underline</u>"
test2: str = "abcdefghijklmnopqrstuvwxyz"
test3: str = "<b>i am not<i> and i am</i> and im not</b> and im neither"

# initialize the styled text class
styled_text: StyledText = StyledText(test1, 800, 600, (0, 0, 0), (255, 255, 255), "Calibri", 16, 5)

clock = pg.time.Clock()
while 1:
    screen.fill((0, 0, 0))
    
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()
            
    screen.blit(styled_text.render(), (0, 0))
    
    clock.tick(60)
    pg.display.flip()