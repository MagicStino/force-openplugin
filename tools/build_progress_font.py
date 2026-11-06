"""Rasterize the bundled OFL Titillium font for the offline progress display."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path

def build(font_path,output):
    font=ImageFont.truetype(str(font_path),36)
    glyphs=[];advances=[]
    for code in range(32,127):
        image=Image.new('L',(40,48));ImageDraw.Draw(image).text((1,0),chr(code),font=font,fill=255)
        glyphs.append(list(image.getdata()));advances.append(round(font.getlength(chr(code))))
    Path(output).write_text('/* Generated from bundled Titillium Web (OFL); see font license. */\nstatic const unsigned char glyph_advance[95]={'+','.join(map(str,advances))+'};\nstatic const unsigned char glyph_pixels[95][1920]={\n'+',\n'.join('{'+','.join(map(str,row))+'}' for row in glyphs)+'};\n')
