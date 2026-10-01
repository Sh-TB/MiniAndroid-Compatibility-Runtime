#!/usr/bin/env python3
"""S133 §22 — the 14 control pages: each isolates ONE browser capability.

Written once, byte-deterministic, served both as APK assets (harness APK)
and over localhost HTTP (WEB-001 network-tier proof). Every page paints a
DISTINCT visual signature so a screenshot alone identifies the passing
capability (no agent eyeballing needed: the forensics script reports the
unique colors).
"""
import os

PAGES = {}

PAGES["TEST-01"] = ("plain HTML", """<!DOCTYPE html>
<html><head><title>T01</title></head>
<body style="margin:0">
<div style="width:1000px;height:400px;background-color:#2244CC"></div>
<div style="width:1000px;height:400px;background-color:#CC4400"></div>
</body></html>""")

PAGES["TEST-02"] = ("CSS colors", """<!DOCTYPE html>
<html><head><style>
.a{background:#FF0000;width:500px;height:300px;display:inline-block}
.b{background:rgb(0,255,0);width:500px;height:300px;display:inline-block}
.c{background:rgba(0,0,255,1);width:1000px;height:300px}
</style></head>
<body style="margin:0">
<div class="a"></div><div class="b"></div><div class="c"></div>
</body></html>""")

PAGES["TEST-03"] = ("CSS layout block+flex", """<!DOCTYPE html>
<html><head><style>
.row{display:flex;flex-direction:row;height:300px}
.row>div{width:330px;height:300px}
.f1{background:#AA00AA}.f2{background:#00AAAA}.f3{background:#AAAA00}
.stack{width:1000px;height:300px;background:#555555}
</style></head>
<body style="margin:0">
<div class="row"><div class="f1"></div><div class="f2"></div><div class="f3"></div></div>
<div class="stack"></div>
</body></html>""")

PAGES["TEST-04"] = ("text", """<!DOCTYPE html>
<html><head><style>
h1{color:#112233;font-size:40px}
p{color:#444444;font-size:28px}
</style></head>
<body style="margin:0;background:#FFFFFF">
<h1>MiniAndroid Text Law</h1>
<p>The quick brown fox jumps over the lazy dog 0123456789.</p>
</body></html>""")

PAGES["TEST-05"] = ("image (asset png)", """<!DOCTYPE html>
<html><head><style>
body{margin:0;background:#FFFFFF}
.box{width:600px;height:600px;background:#EEEEEE}
</style></head>
<body>
<div class="box"></div>
<img src="fixture_red.png" width="300" height="300">
</body></html>""")

PAGES["TEST-06"] = ("SVG", """<!DOCTYPE html>
<html><head><style>body{margin:0;background:#FFFFFF}</style></head>
<body>
<svg width="600" height="600" xmlns="http://www.w3.org/2000/svg">
<circle cx="300" cy="300" r="200" fill="#0088FF"/>
<rect x="50" y="50" width="120" height="120" fill="#FF8800"/>
</svg>
</body></html>""")

PAGES["TEST-07"] = ("font weight/size", """<!DOCTYPE html>
<html><head><style>
.big{font-size:64px;font-weight:bold;color:#000000}
.small{font-size:24px;color:#666666}
</style></head>
<body style="margin:0;background:#FFFFFF">
<div class="big">Bold 64px</div>
<div class="small">Regular 24px</div>
</body></html>""")

PAGES["TEST-08"] = ("JS DOM mutation", """<!DOCTYPE html>
<html><head><style>
body{margin:0}
#mut{width:1000px;height:500px;background:#111111}
#after{width:1000px;height:300px;background:#DDDDDD;display:none}
</style></head>
<body>
<div id="mut"></div>
<div id="after"></div>
<script>
document.getElementById('mut').style.background = '#00CC44';
document.getElementById('after').style.display = 'block';
document.getElementById('after').innerHTML = '<div style="width:500px;height:300px;background:#990044"></div>';
</script>
</body></html>""")

PAGES["TEST-09"] = ("canvas 2D", """<!DOCTYPE html>
<html><head><style>body{margin:0}</style></head>
<body>
<canvas id="c" width="1000" height="800" style="background:#FFFFFF"></canvas>
<script>
var ctx = document.getElementById('c').getContext('2d');
ctx.fillStyle = '#FF00FF';
ctx.fillRect(50, 50, 400, 300);
ctx.fillStyle = '#00FFFF';
ctx.beginPath();
ctx.arc(700, 200, 150, 0, Math.PI * 2, false);
ctx.fill();
</script>
</body></html>""")

PAGES["TEST-10"] = ("scroll (tall page)", """<!DOCTYPE html>
<html><head><style>
body{margin:0}
.s{width:1080px;height:600px}
</style></head>
<body>
<div class="s" style="background:#CC0000"></div>
<div class="s" style="background:#00CC00"></div>
<div class="s" style="background:#0000CC"></div>
<div class="s" style="background:#CCCCCC"></div>
</body></html>""")

PAGES["TEST-11"] = ("clipping (overflow)", """<!DOCTYPE html>
<html><head><style>
body{margin:0}
.clip{width:500px;height:500px;overflow:hidden;background:#FFFFFF;position:relative}
.inner{width:1000px;height:1000px;background:linear-gradient(#FFAA00,#AA00FF)}
</style></head>
<body>
<div class="clip"><div class="inner"></div></div>
<div style="width:400px;height:400px;background:#00AA00"></div>
</body></html>""")

PAGES["TEST-12"] = ("transform", """<!DOCTYPE html>
<html><head><style>body{margin:0;background:#FFFFFF}</style></head>
<body>
<div style="width:400px;height:400px;background:#334455;transform:translate(100px,80px) rotate(15deg)"></div>
</body></html>""")

PAGES["TEST-13"] = ("opacity", """<!DOCTYPE html>
<html><head><style>body{margin:0;background:#FFFFFF}</style></head>
<body style="background:#00FF00">
<div style="width:600px;height:600px;background:#FF0000;opacity:0.5"></div>
</body></html>""")

PAGES["TEST-14"] = ("large page (2000 nodes)", """<!DOCTYPE html>
<html><head><style>
body{margin:0}
.cell{width:100px;height:100px;display:inline-block}
</style></head>
<body>
<script>
var s = '';
for (var i = 0; i < 2000; i++) {
  var hue = (i * 37) % 256;
  s += '<div class="cell" style="background:rgb(' + hue + ',128,255-' + hue + ')"></div>';
}
document.body.innerHTML = s;
</script>
</body></html>""")

OUT = "/home/z/my-project/fixtures/s133_webfix/assets"
os.makedirs(OUT, exist_ok=True)
index = ["<!DOCTYPE html><html><head><title>INDEX</title></head><body>"]
for tid, (desc, html) in sorted(PAGES.items()):
    path = os.path.join(OUT, f"{tid}.html")
    with open(path, "w") as f:
        f.write(html)
    index.append(f'<p>{tid}: {desc}</p>')
    print(f"{tid}: {desc} -> {path} ({len(html)} bytes)")
with open(os.path.join(OUT, "INDEX.html"), "w") as f:
    f.write("\n".join(index) + "</body></html>")
print("INDEX written")
