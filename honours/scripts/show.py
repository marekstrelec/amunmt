#!/usr/bin/env python2

from PIL import Image

for filename in ['means.png', 'vars.png', 'cumsum.png', 'zipf']:
    img = Image.open(filename)
    img.show()
