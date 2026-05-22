import cv2
import numpy as np
from PIL import Image, ImageDraw
import time
import math

# ==============================
# VECTOR FONT (for digital look)
# ==============================
def draw_vector_string(draw, text, x, y, color=(0,255,255), scale=2):
    font = {
        '0': [(0,0,1,0),(1,0,1,2),(1,2,0,2),(0,2,0,0)],
        '1': [(0.5,0,0.5,2)],
        '2': [(0,0,1,0),(1,0,1,1),(1,1,0,1),(0,1,0,2),(0,2,1,2)],
        '3': [(0,0,1,0),(1,0,1,2),(0,1,1,1),(0,2,1,2)],
        '4': [(0,0,0,1),(0,1,1,1),(1,0,1,2)],
        '5': [(1,0,0,0),(0,0,0,1),(0,1,1,1),(1,1,1,2),(1,2,0,2)],
        '6': [(1,0,0,0),(0,0,0,2),(0,2,1,2),(1,2,1,1),(1,1,0,1)],
        '7': [(0,0,1,0),(1,0,0,2)],
        '8': [(0,0,1,0),(1,0,1,2),(1,2,0,2),(0,2,0,0),(0,1,1,1)],
        '9': [(1,2,1,0),(1,0,0,0),(0,0,0,1),(0,1,1,1)],
        '.': [(0.5,2,0.5,2.1)],
        'M': [(0,2,0,0),(0,0,0.5,1),(0.5,1,1,0),(1,0,1,2)],
        'W': [(0,0,0.3,2),(0.3,2,0.6,1),(0.6,1,0.9,2),(0.9,2,1.2,0)],
        'H': [(0,0,0,2),(1,0,1,2),(0,1,1,1)],
        'z': [(0,0,1,0),(1,0,0,2),(0,2,1,2)]
    }

    offset_x = x
    for char in text:
        if char in font:
            for line in font[char]:
                x1 = offset_x + line[0]*20*scale
                y1 = y + line[1]*20*scale
                x2 = offset_x + line[2]*20*scale
                y2 = y + line[3]*20*scale
                draw.line((x1,y1,x2,y2), fill=color, width=2)
        offset_x += 30*scale


# ==============================
# DRAW FUNCTION
# ==============================
def draw_dial(png_path, mw, hz):
    try:
        img = Image.open(png_path).convert("RGBA")
    except Exception as e:
        print("Image load error:", e)
        return None

    draw = ImageDraw.Draw(img)

    w, h = img.size

    # Center area of dial (adjust if needed)
    cx = int(w * 0.35)
    cy = int(h * 0.65)

    # Text
    mw_text = f"{mw:.1f} MW"
    hz_text = f"{hz:.2f} Hz"

    # Draw values
    draw_vector_string(draw, mw_text, cx, cy - 60, (0,255,255), scale=2)
    draw_vector_string(draw, hz_text, cx, cy + 40, (255,255,0), scale=2)

    return img


# ==============================
# MAIN LOOP
# ==============================
PNG_PATH = "your_dial.png"   # <-- PUT YOUR IMAGE NAME HERE

while True:
    # Dummy changing values (replace with real sensor data)
    t = time.time()
    mw_value = 500 + 100 * math.sin(t)
    hz_value = 50 + 0.5 * math.sin(t/2)

    img = draw_dial(PNG_PATH, mw_value, hz_value)

    if img is None:
        break

    # Convert PIL -> OpenCV
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)

    cv2.imshow("Dial Dashboard", frame)

    if cv2.waitKey(100) & 0xFF == 27:
        break

cv2.destroyAllWindows()
