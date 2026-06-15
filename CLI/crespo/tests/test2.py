from PIL import Image, ImageDraw, ImageFont

lines = [
    ("██████╗██████╗ ███████╗███████╗██████╗  ██████╗", (100, 200, 140)),
    ("██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗", (100, 200, 140)),
    ("██║     ██████╔╝█████╗  ███████╗██████╔╝██║   ██║", (110, 180, 160)),
    ("██║     ██╔══██╗██╔══╝  ╚════██║██╔═══╝ ██║   ██║", (120, 160, 180)),
    ("╚██████╗██║  ██║███████╗███████║██║     ╚██████╔╝", (130, 110, 200)),
    (" ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝      ╚═════╝ ", (140, 100, 220)),
]

# Transparent background (RGBA, alpha=0)
img = Image.new("RGBA", (1400, 350), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 36)

y = 20
for text, color in lines:
    draw.text((20, y), text, fill=(*color, 255), font=font)
    y += 45

draw.text(
    (20, y + 20),
    "Crisp repos. Sharp AI.",
    fill=(100, 200, 140, 255),
    font=font,
)

img.save("crespo-banner2.png")