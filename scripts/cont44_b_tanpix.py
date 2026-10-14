from PIL import Image
import sys
im = Image.open('/home/z/my-project/run/cont44/tan_pre/screenshot.png').convert('RGB')
W,H = im.size
print('size', W, H)
px = im.load()
# scan column x=540 for color changes to find bands
prev = None
for y in range(0, H, 1):
    c = px[540, y]
    if prev is None or (abs(c[0]-prev[0])+abs(c[1]-prev[1])+abs(c[2]-prev[2]) > 12):
        print('y=%d rgb=%s' % (y, c))
        prev = c
