# app.py
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import traceback
from io import BytesIO # Needed for download button

# --- Configuration ---
TEMPLATE_IMAGE = "template.png"
FONT_NAME = "Grandstander-Black.ttf"
FONT_NAME2 = "Grandstander-Bold.ttf"
SCRIPT_DIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, TEMPLATE_IMAGE)
FONT_PATH = os.path.join(SCRIPT_DIR, FONT_NAME)
FONT_PATH2 = os.path.join(SCRIPT_DIR, FONT_NAME2)



# --- Define TARGET Areas (BOXES for auto-sizing) ---
# *** ADJUST THESE VALUES TO MATCH YOUR DESIRED LAYOUT ON THE TEMPLATE ***

# 1. DAY Box ("MONDAY") - Fits text to box, aligned right
DAY_X = 180; DAY_Y = 1700; DAY_W = 1450; DAY_H = 350
DAY_BOX = (DAY_X, DAY_Y, DAY_X + DAY_W, DAY_Y + DAY_H)

# 2. MONTH Box ("MARCH") - Fits text to box, centered
MONTH_X = 1000; MONTH_Y = 1960; MONTH_W = 575; MONTH_H = 150
MONTH_BOX = (MONTH_X, MONTH_Y, MONTH_X + MONTH_W, MONTH_Y + MONTH_H)

# 3. NUMBER Box ("100") - Fits text to box, centered
NUMBER_X = 1640; NUMBER_Y = 1690; NUMBER_W = 525; NUMBER_H = 525
NUMBER_BOX = (NUMBER_X, NUMBER_Y, NUMBER_X + NUMBER_W, NUMBER_Y + NUMBER_H)

# 4. SUFFIX ("TH") - Relative position, fixed size
SUFFIX_SIZE = 80
SUFFIX_X_OFFSET = -55
SUFFIX_Y_OFFSET = 55

# 5. PUB Box ("THE RED LION") - Fits text to box, centered
PUB_X = 710; PUB_Y = 2690; PUB_W = 1480; PUB_H = 260
PUB_BOX = (PUB_X, PUB_Y, PUB_X + PUB_W, PUB_Y + PUB_H)

# --- NEW: Optional Details - Using BOXES for auto-sizing again ---
# *** ADJUST X, Y, W, H for these boxes ***
DEFAULT_EVENT_TYPE = "WEEKLY EVENT"
DEFAULT_TIME = "8PM"
DEFAULT_FIRST_PLACE = "@ COURTYARD"

# 6. EVENT TYPE Box - Fits text, will be left-aligned
EVENT_TYPE_X = 200
EVENT_TYPE_Y = 2295
EVENT_TYPE_W = 2020 # Wide to allow centering if needed later, but text aligns left
EVENT_TYPE_H = 165
EVENT_TYPE_BOX = (EVENT_TYPE_X, EVENT_TYPE_Y, EVENT_TYPE_X + EVENT_TYPE_W, EVENT_TYPE_Y + EVENT_TYPE_H)

# 7. TIME Box - Fits text, will be left-aligned
TIME_X = 155
TIME_Y = 2435
TIME_W = 530 # Adjust width to constrain font size if needed
TIME_H = 300
TIME_BOX = (TIME_X, TIME_Y, TIME_X + TIME_W, TIME_Y + TIME_H)

# 8. FIRST PLACE Box - Fits text, will be centered
FIRST_PLACE_X = 725
FIRST_PLACE_Y = 2435 # Same line as Time
FIRST_PLACE_W = 1650 # Adjust width
FIRST_PLACE_H = 300
FIRST_PLACE_BOX = (FIRST_PLACE_X, FIRST_PLACE_Y, FIRST_PLACE_X + FIRST_PLACE_W, FIRST_PLACE_Y + FIRST_PLACE_H)


# --- Colors ---
TEXT_COLOR = (34, 34, 46)            # Off-Black

# --- Helper Functions ---
def get_ordinal_suffix(day):
    if 11 <= day <= 13: return 'th'
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    return suffixes.get(day % 10, 'th')

# find_max_font_size used for ALL fitted text now
def find_max_font_size(text, font_path, target_box, draw):
    """Finds the largest font size that fits text within the target_box."""
    target_w = target_box[2] - target_box[0]
    target_h = target_box[3] - target_box[1]
    # print(f"    Finding font size for '{text}' in box W={target_w}, H={target_h}")
    if not text: return 10 # Handle empty string
    if target_w <= 0 or target_h <= 0: return 10
    font_size = int(target_h * 0.9); best_size = 10
    while font_size >= 10:
        try:
            font = ImageFont.truetype(font_path, font_size)
            bbox = draw.textbbox((0, 0), text, font=font, anchor="lt")
            text_w = bbox[2] - bbox[0]; text_h = bbox[3] - bbox[1]
            if text_w <= target_w and text_h <= target_h:
                best_size = font_size
                # print(f"    Found best fit: size {best_size} (Text W={text_w:.0f}, H={text_h:.0f})")
                return best_size
            font_size -= 5
            if font_size < 10: font_size = 9
        except IOError: st.error(f"FATAL ERROR: Font '{font_path}' not found."); return None
        except Exception as e: print(f"    Error calc bbox size {font_size} for '{text}': {e}"); font_size -= 5
    # print(f"    Warning: Could not fit '{text}'. Using {best_size}.")
    return best_size

# --- Main Image Generation Logic ---
def create_poster(day_of_week, month, day_num_str, pub_name, event_type_text, time_text, first_place_text):
    """Generates the poster image object."""
    print(f"\n--- Generating Poster ---")
    # (Keep console logs...)

    try:
        if not os.path.exists(TEMPLATE_PATH): st.error(f"Template image not found: {TEMPLATE_PATH}"); return None
        if not os.path.exists(FONT_PATH): st.error(f"Font file not found: {FONT_PATH}"); return None

        img = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)

        # --- Prepare Text ---
        day_text = day_of_week.upper()
        month_text = month.upper()
        try: day_num = int(day_num_str); day_num_text = str(day_num)
        except ValueError: st.error(f"Internal Error: Invalid day number '{day_num_str}'."); return None
        suffix_text = get_ordinal_suffix(day_num).upper()
        pub_text = pub_name.upper()
        event_type_final_text = event_type_text.upper() if event_type_text else ""
        time_final_text = time_text.upper() if time_text else ""
        first_place_final_text = first_place_text.upper() if first_place_text else ""

        # --- Determine Optimal Font Sizes (ALL Fitted Text) ---
        print("Determining optimal font sizes...")
        day_opt_size = find_max_font_size(day_text, FONT_PATH, DAY_BOX, draw)
        month_opt_size = find_max_font_size(month_text, FONT_PATH, MONTH_BOX, draw)
        num_opt_size = find_max_font_size(day_num_text, FONT_PATH, NUMBER_BOX, draw)
        pub_opt_size = find_max_font_size(pub_text, FONT_PATH, PUB_BOX, draw)
        # <<< Calculate optimal sizes for optional fields >>>
        event_type_opt_size = find_max_font_size(event_type_final_text, FONT_PATH2, EVENT_TYPE_BOX, draw)
        time_opt_size = find_max_font_size(time_final_text, FONT_PATH, TIME_BOX, draw)
        first_place_opt_size = find_max_font_size(first_place_final_text, FONT_PATH, FIRST_PLACE_BOX, draw)


        # Check essential sizes
        if None in [day_opt_size, month_opt_size, num_opt_size, pub_opt_size,
                    event_type_opt_size, time_opt_size, first_place_opt_size]:
             st.error("Failed to determine one or more font sizes.")
             return None

        # --- Load Fonts (All Optimal Sizes + Fixed Suffix) ---
        print("Loading fonts...")
        try:
            font_day = ImageFont.truetype(FONT_PATH, day_opt_size)
            font_month = ImageFont.truetype(FONT_PATH, month_opt_size)
            font_day_num = ImageFont.truetype(FONT_PATH, num_opt_size)
            font_suffix = ImageFont.truetype(FONT_PATH, SUFFIX_SIZE) # Suffix remains fixed size
            font_pub = ImageFont.truetype(FONT_PATH, pub_opt_size)
            # <<< Load optional fonts with OPTIMAL sizes >>>
            font_event_type = ImageFont.truetype(FONT_PATH, event_type_opt_size)
            font_time = ImageFont.truetype(FONT_PATH, time_opt_size)
            font_first_place = ImageFont.truetype(FONT_PATH, first_place_opt_size)
        except IOError: st.error(f"ERROR: Font '{FONT_PATH}' could not be loaded!"); return None
        except Exception as e: st.error(f"Error loading fonts: {e}"); traceback.print_exc(); return None

        # --- Draw Text Elements ---
        print("Drawing text elements...")
        # 1. Draw Day (Aligned Right in Box)
        day_right_x = DAY_BOX[2]; day_middle_y = (DAY_BOX[1] + DAY_BOX[3]) / 2
        draw.text((day_right_x, day_middle_y), day_text, fill=TEXT_COLOR, font=font_day, anchor="rm")
        # 2. Draw Month (Centered in Box)
        month_center_x = (MONTH_BOX[0] + MONTH_BOX[2]) / 2; month_center_y = (MONTH_BOX[1] + MONTH_BOX[3]) / 2
        draw.text((month_center_x, month_center_y), month_text, fill=TEXT_COLOR, font=font_month, anchor="mm")
        # 3. Draw Number (Centered in Box)
        num_center_x = (NUMBER_BOX[0] + NUMBER_BOX[2]) / 2; num_center_y = (NUMBER_BOX[1] + NUMBER_BOX[3]) / 2
        draw.text((num_center_x, num_center_y), day_num_text, fill=TEXT_COLOR, font=font_day_num, anchor="mm")
        # 4. Draw Suffix (Relative position)
        suffix_pos_x = NUMBER_BOX[2] + SUFFIX_X_OFFSET; suffix_pos_y = NUMBER_BOX[1] + SUFFIX_Y_OFFSET
        draw.text((suffix_pos_x, suffix_pos_y), suffix_text, fill=TEXT_COLOR, font=font_suffix, anchor="lt")
        # 5. Draw Pub Name (Centered in Box)
        pub_center_x = (PUB_BOX[0] + PUB_BOX[2]) / 2; pub_center_y = (PUB_BOX[1] + PUB_BOX[3]) / 2
        draw.text((pub_center_x, pub_center_y), pub_text, fill=TEXT_COLOR, font=font_pub, anchor="mm")

        # <<< MODIFIED: Draw Optional Fields with Specific Alignments >>>
        # 6. Draw Event Type (Left-aligned, vertically centered in its box)
        if event_type_final_text:
            event_type_left_x = EVENT_TYPE_BOX[0] # Left edge of the box
            event_type_middle_y = (EVENT_TYPE_BOX[1] + EVENT_TYPE_BOX[3]) / 2 # Vertical center
            print(f"  Drawing Event Type at ({event_type_left_x}, {event_type_middle_y}), anchor=lm")
            draw.text((event_type_left_x, event_type_middle_y), event_type_final_text, fill=TEXT_COLOR, font=font_event_type, anchor="lm") # Left-Middle anchor

        # 7. Draw Time (Left-aligned, vertically centered in its box)
        if time_final_text:
            time_left_x = TIME_BOX[0] # Left edge of the box
            time_middle_y = (TIME_BOX[1] + TIME_BOX[3]) / 2 # Vertical center
            print(f"  Drawing Time at ({time_left_x}, {time_middle_y}), anchor=lm")
            draw.text((time_left_x, time_middle_y), time_final_text, fill=TEXT_COLOR, font=font_time, anchor="lm") # Left-Middle anchor

        # 8. Draw First Place (Centered in its box)
        if first_place_final_text:
            first_place_center_x = (FIRST_PLACE_BOX[0] + FIRST_PLACE_BOX[2]) / 2 # Horizontal center
            first_place_middle_y = (FIRST_PLACE_BOX[1] + FIRST_PLACE_BOX[3]) / 2 # Vertical center
            print(f"  Drawing First Place at ({first_place_center_x}, {first_place_middle_y}), anchor=mm")
            draw.text((first_place_center_x, first_place_middle_y), first_place_final_text, fill=TEXT_COLOR, font=font_first_place, anchor="mm") # Middle-Middle anchor


        print("Text drawing complete.")
        return img # Return the modified PIL Image object

    # (Error Handling remains the same)
    except FileNotFoundError: st.error(f"Error: Required file not found."); return None
    except Exception as e: st.error(f"An unexpected error occurred."); print(f"Error: {e}"); traceback.print_exc(); return None

# --- Streamlit UI Code ---
st.set_page_config(layout="centered", page_title="Pub Society Poster")
st.title("🍻 Pub Soc Poster Generator 🦆")

# (UI Input Section remains the same - uses DEFAULT values)
st.header("Required Info")
date_str_input = st.text_input("Event Date", placeholder="e.g., 18 March or Tuesday 18 March", help="...")
pub_name_input = st.text_input("Pub Name (after first place)")
st.markdown("---")
st.header("Optional Details (Defaults from Template)")
event_type_input = st.text_input("Event Type Text", value=DEFAULT_EVENT_TYPE)
time_input = st.text_input("Time", value=DEFAULT_TIME)
first_place_input = st.text_input("First Place Name", value=DEFAULT_FIRST_PLACE)
st.caption("Clear a field above if you don't want that text to appear.")
st.markdown("---")

# (Generate Button and Logic remain the same)
if st.button("✨ Generate Poster ✨"):
    if not date_str_input or not pub_name_input:
        st.warning("✋ Please enter at least the Date and Pub Name.")
    else:
        # (Date Parsing remains the same)
        day_of_week, month, day_num_str = None, None, None; event_date = None
        print(f"Attempting to parse date: {date_str_input}")
        try:
            parsed = False
            for fmt in ("%B %d", "%A %d %B", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y", "%A, %B %d", "%a %b %d", "%A %d", "%d %B"):
                 try:
                     now = datetime.datetime.now()
                     parsed_date = datetime.datetime.strptime(date_str_input, fmt)
                     if parsed_date.year == 1900: event_date = parsed_date.replace(year=now.year).date()
                     else: event_date = parsed_date.date()
                     if event_date < now.date() - datetime.timedelta(days=180): event_date = event_date.replace(year=event_date.year + 1)
                     parsed = True; break
                 except ValueError: continue
            if parsed:
                day_of_week = event_date.strftime("%A"); month = event_date.strftime("%B"); day_num_str = str(event_date.day)
                st.info(f"🗓️ Using date: {day_of_week}, {month} {day_num_str} ({event_date.year})")
            else: st.error("❌ Could not parse date. Use format like '4 July' or 'Tuesday 18 March'.")
        except Exception as e: st.error(f"🤯 Error during date parsing: {e}"); event_date = None

        # Get Optional Values
        event_type_val = event_type_input
        time_val = time_input
        first_place_val = first_place_input

        # Call Image Generation
        if day_of_week and month and day_num_str:
            with st.spinner("⏳ Generating image..."):
                generated_image = create_poster(day_of_week, month, day_num_str, pub_name_input, event_type_val, time_val, first_place_val)
            # Display Result
            if generated_image:
                st.success("✅ Poster Generated!")
                st.image(generated_image, caption="Generated Poster", use_container_width=True)
                # (Download Button remains the same)
                try:
                    buf = BytesIO(); generated_image.save(buf, format="PNG"); byte_im = buf.getvalue()
                    download_filename = f"poster_{day_of_week.upper()}_{month.upper()}_{day_num_str}.png"
                    st.download_button(label="💾 Download Poster", data=byte_im, file_name=download_filename, mime="image/png")
                except Exception as e: st.error(f"Download prep failed: {e}")
            else: st.error("🙁 Image generation failed.")

# (Footer remains the same)
st.markdown("---")
st.caption("Enter the event details above and click generate. big up dan (me)")
