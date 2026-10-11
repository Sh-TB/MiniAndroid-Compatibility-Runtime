from PIL import Image
im = Image.open('/home/z/my-project/run/cont44/tan_pre/screenshot.png').convert('RGB')
W,H = im.size
px = im.load()
from collections import Counter
cnt = Counter()
dark = []
for y in range(0,H,2):
    for x in range(0,W,2):
        c = px[x,y]
        cnt[c]+=1
        if c[0]+c[1]+c[2] < 300:
            dark.append((x,y))
print('top colors:', cnt.most_common(6))
print('dark px count (sampled):', len(dark))
if dark:
    xs=[p[0] for p in dark]; ys=[p[1] for p in dark]
    print('dark bbox x', min(xs), max(xs), 'y', min(ys), max(ys))
# column scan at x=100
prev=None
for y in range(H):
    c=px[100,y]
    if prev is None or (abs(c[0]-prev[0])+abs(c[1]-prev[1])+abs(c[2]-prev[2])>12):
        print('x100 y=%d rgb=%s'%(y,c)); prev=c
