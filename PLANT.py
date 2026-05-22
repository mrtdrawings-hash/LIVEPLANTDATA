def draw_vector_string(draw, text, cx, cy, color):
    # 🔥 BIGGER DISPLAY SETTINGS (for long-distance visibility)
    digit_w = 60        # ⬅️ increased from 34
    digit_h = 100       # ⬅️ increased from 58
    thickness = 14      # ⬅️ thicker segments
    spacing = 10        # spacing between digits

    total_w = len(text) * (digit_w + spacing) - spacing
    start_x = cx - (total_w / 2)

    # 🔥 Move slightly upward so it stays centered visually
    start_y = cy - (digit_h / 2) - 10

    curr_x = start_x
    for char in text:
        if char in '0123456789.-':
            draw_custom_vector_digit(
                draw, curr_x, start_y,
                char, digit_w, digit_h, thickness, color
            )
        else:
            # 🔥 Bigger MW / Hz letters
            if char == 'M':
                draw.rectangle([curr_x, start_y, curr_x + 10, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 10, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y, curr_x + digit_w, start_y + 10], fill=color)
                draw.rectangle([curr_x + digit_w/2 - 5, start_y, curr_x + digit_w/2 + 5, start_y + digit_h], fill=color)

            elif char == 'W':
                draw.rectangle([curr_x, start_y, curr_x + 10, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 10, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 10, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w/2 - 5, start_y + 20, curr_x + digit_w/2 + 5, start_y + digit_h], fill=color)

            elif char == 'H':
                draw.rectangle([curr_x, start_y, curr_x + 10, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + digit_w - 10, start_y, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x, start_y + digit_h/2 - 5, curr_x + digit_w, start_y + digit_h/2 + 5], fill=color)

            elif char == 'z':
                draw.rectangle([curr_x, start_y + 20, curr_x + digit_w, start_y + 30], fill=color)
                draw.rectangle([curr_x, start_y + digit_h - 10, curr_x + digit_w, start_y + digit_h], fill=color)
                draw.rectangle([curr_x + 10, start_y + 30, curr_x + digit_w - 10, start_y + digit_h - 10], fill=color)

        curr_x += digit_w + spacing
