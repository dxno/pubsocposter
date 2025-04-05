# app.py
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import traceback
from io import BytesIO # Needed for download button

# --- Configuration ---
# Ensure these files are in the same directory as app.py
TEMPLATE_IMAGE = "template.png"
FONT_NAME = "Grandstander-Black.ttf"
# Construct full paths relative to the script location for robustness
SCRIPT_DIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, TEMPLATE_IMAGE)
FONT_PATH = os.path.join(SCRIPT_DIR, FONT_NAME)


# --- Define TARGET Areas using Top-Left Corner (X, Y) and Dimensions (W, H) ---
# *** ADJUST THESE VALUES TO MATCH YOUR DESIRED LAYOUT ON THE TEMPLATE ***

# 1. DAY Area ("MONDAY")
DAY_X = 180    # Pixels from Left Edge to Start Day Box
DAY_Y = 1700   # Pixels from Top Edge to Start Day Box
DAY_W = 1450   # Width of Day Box in Pixels
DAY_H = 350    # Height of Day Box in Pixels

# 2. MONTH Area ("MARCH")
MONTH_X = 1000  # Pixels from Left Edge to Start Month Box
MONTH_Y = 1960 # Pixels from Top Edge to Start Month Box (Below Day)
MONTH_W = 575  # Width of Month Box in Pixels
MONTH_H = 150  # Height of Month Box in Pixels

# 3. NUMBER Area ("100")
NUMBER_X = 1640 # Pixels from Left Edge to Start Number Box (Right of Day)
NUMBER_Y = 1690 # Pixels from Top Edge to Start Number Box
NUMBER_W = 525  # Width of Number Box in Pixels
NUMBER_H = 525  # Height of Number Box in Pixels

# 4. SUFFIX ("TH") - Positioned relative to the NUMBER area, not its own box
SUFFIX_SIZE = 80     # Fixed small size for suffix
SUFFIX_X_OFFSET = -55  # Pixels relative to NUMBER's top-right corner (Adjust X)
SUFFIX_Y_OFFSET = 55 # Pixels relative to NUMBER's top-right corner (Adjust Y)

# 5. PUB Area ("THE RED LION")
PUB_X = 710    # Pixels from Left Edge to Start Pub Box
PUB_Y = 2690   # Pixels from Top Edge to Start Pub Box
PUB_W = 1480   # Width of Pub Box in Pixels
PUB_H = 260    # Height of Pub Box in Pixels

# --- NEW: Optional Details Area Definitions ---
DEFAULT_EVENT_TYPE = "WEEKLY EVENT"
DEFAULT_TIME = "8PM"
DEFAULT_FIRST_PLACE = "@ COURTYARD"

# 6. EVENT TYPE Area (e.g., "WEEKLY EVENT") - Above Time/Place
#    Centered horizontally, adjust Y as needed
EVENT_TYPE_X = 180
EVENT_TYPE_Y = 2275 # Position this line vertically
EVENT_TYPE_W = 2000 # Wide box for centering text
EVENT_TYPE_H = 140  # Relatively small height

# 7. TIME Area (e.g., "8PM") - Below Event Type, Left-ish side
TIME_X = 160
TIME_Y = EVENT_TYPE_Y + EVENT_TYPE_H + 15 # Y position below Event Type line
TIME_W = 550  # Adjust width as needed
TIME_H = 210  # Height for Time/Place line

# 8. FIRST PLACE Area (e.g., "@ COURTYARD") - Below Event Type, Right-ish side
#    Starts slightly after the Time box ends
FIRST_PLACE_X = TIME_X + TIME_W + 10
FIRST_PLACE_Y = TIME_Y # Same vertical position as Time
FIRST_PLACE_W = 1600 # Adjust width as needed
FIRST_PLACE_H = TIME_H # Same height as Time


# --- Calculate Box Tuples (x0, y0, x1, y1) ---
DAY_BOX = (DAY_X, DAY_Y, DAY_X + DAY_W, DAY_Y + DAY_H)
MONTH_BOX = (MONTH_X, MONTH_Y, MONTH_X + MONTH_W, MONTH_Y + MONTH_H)
NUMBER_BOX = (NUMBER_X, NUMBER_Y, NUMBER_X + NUMBER_W, NUMBER_Y + NUMBER_H)
PUB_BOX = (PUB_X, PUB_Y, PUB_X + PUB_W, PUB_Y + PUB_H)
EVENT_TYPE_BOX = (EVENT_TYPE_X, EVENT_TYPE_Y, EVENT_TYPE_X + EVENT_TYPE_W, EVENT_TYPE_Y + EVENT_TYPE_H)
TIME_BOX = (TIME_X, TIME_Y, TIME_X + TIME_W, TIME_Y + TIME_H)
FIRST_PLACE_BOX = (FIRST_PLACE_X, FIRST_PLACE_Y, FIRST_PLACE_X + FIRST_PLACE_W, FIRST_PLACE_Y + FIRST_PLACE_H)

# --- Colors ---
TEXT_COLOR = (34, 34, 46)            # Off-Black

# --- Helper Functions ---
def get_ordinal_suffix(day):
    """Gets the ordinal suffix (st, nd, rd, th) for a day number."""
    if 11 <= day <= 13: return 'th'
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    return suffixes.get(day % 10, 'th')

def find_max_font_size(text, font_path, target_box, draw):
    """Finds the largest font size that fits text within the target_box."""
    target_w = target_box[2] - target_box[0]
    target_h = target_box[3] - target_box[1]
    # print(f"    Finding font size for '{text}' in box W={target_w}, H={target_h}")
    if not text: return 10 # Handle empty string case
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
        except IOError:
            st.error(f"FATAL ERROR: Font file '{font_path}' not found. Cannot calculate size.")
            return None # Indicate fatal error
        except Exception as e:
            print(f"    Error calc bbox size {font_size} for '{text}': {e}"); font_size -= 5
    # print(f"    Warning: Could not fit '{text}'. Using {best_size}.")
    return best_size

# --- Main Image Generation Logic ---
# <<< MODIFIED Function Signature >>>
def create_poster(day_of_week, month, day_num_str, pub_name, event_type_text, time_text, first_place_text):
    """Generates the poster image object."""
    print(f"\n--- Generating Poster ---")
    print(f"Date: {day_of_week} {month} {day_num_str}, Pub: {pub_name}")
    print(f"Details: '{event_type_text}', '{time_text}', '{first_place_text}'") # Log new inputs
    print(f"Using Template: {TEMPLATE_PATH}")
    print(f"Using Font: {FONT_PATH}")

    try:
        if not os.path.exists(TEMPLATE_PATH): st.error(f"Template image not found: {TEMPLATE_PATH}"); return None
        if not os.path.exists(FONT_PATH): st.error(f"Font file not found: {FONT_PATH}"); return None

        img = Image.open(TEMPLATE_PATH).convert("RGB")
        print(f"Template size: {img.size}")
        draw = ImageDraw.Draw(img)

        # --- Prepare Text ---
        day_text = day_of_week.upper()
        month_text = month.upper()
        try:
            day_num = int(day_num_str); day_num_text = str(day_num)
        except ValueError: st.error(f"Internal Error: Invalid day number '{day_num_str}'."); return None
        suffix_text = get_ordinal_suffix(day_num).upper()
        pub_text = pub_name.upper()
        # Prepare optional text (handle if user clears the field)
        event_type_final_text = event_type_text.upper() if event_type_text else ""
        time_final_text = time_text.upper() if time_text else ""
        first_place_final_text = first_place_text.upper() if first_place_text else ""


        # --- Determine Optimal Font Sizes ---
        print("Determining optimal font sizes...")
        day_opt_size = find_max_font_size(day_text, FONT_PATH, DAY_BOX, draw)
        month_opt_size = find_max_font_size(month_text, FONT_PATH, MONTH_BOX, draw)
        num_opt_size = find_max_font_size(day_num_text, FONT_PATH, NUMBER_BOX, draw)
        pub_opt_size = find_max_font_size(pub_text, FONT_PATH, PUB_BOX, draw)
        # <<< NEW: Calculate sizes for optional fields >>>
        event_type_opt_size = find_max_font_size(event_type_final_text, FONT_PATH, EVENT_TYPE_BOX, draw)
        time_opt_size = find_max_font_size(time_final_text, FONT_PATH, TIME_BOX, draw)
        first_place_opt_size = find_max_font_size(first_place_final_text, FONT_PATH, FIRST_PLACE_BOX, draw)

        # Check if any essential font size calculation failed
        if None in [day_opt_size, month_opt_size, num_opt_size, pub_opt_size,
                    event_type_opt_size, time_opt_size, first_place_opt_size]:
            # Error should have been shown by find_max_font_size if font not found
            st.error("Failed to determine one or more font sizes.")
            return None

        # --- Load Fonts with Optimal Sizes ---
        print("Loading fonts with determined sizes...")
        try:
            font_day = ImageFont.truetype(FONT_PATH, day_opt_size)
            font_month = ImageFont.truetype(FONT_PATH, month_opt_size)
            font_day_num = ImageFont.truetype(FONT_PATH, num_opt_size)
            font_suffix = ImageFont.truetype(FONT_PATH, SUFFIX_SIZE)
            font_pub = ImageFont.truetype(FONT_PATH, pub_opt_size)
            # <<< NEW: Load fonts for optional fields >>>
            font_event_type = ImageFont.truetype(FONT_PATH, event_type_opt_size)
            font_time = ImageFont.truetype(FONT_PATH, time_opt_size)
            font_first_place = ImageFont.truetype(FONT_PATH, first_place_opt_size)
        except IOError: st.error(f"ERROR: Font '{FONT_PATH}' could not be loaded!"); return None
        except Exception as e: st.error(f"Error loading fonts: {e}"); traceback.print_exc(); return None

        # --- Draw Text Elements ---
        print("Drawing text elements...")
        # 1. Draw Day (Aligned Right)
        day_right_x = DAY_BOX[2]; day_middle_y = (DAY_BOX[1] + DAY_BOX[3]) / 2
        draw.text((day_right_x, day_middle_y), day_text, fill=TEXT_COLOR, font=font_day, anchor="rm")
        # 2. Draw Month (Centered)
        month_center_x = (MONTH_BOX[0] + MONTH_BOX[2]) / 2; month_center_y = (MONTH_BOX[1] + MONTH_BOX[3]) / 2
        draw.text((month_center_x, month_center_y), month_text, fill=TEXT_COLOR, font=font_month, anchor="mm")
        # 3. Draw Number (Centered)
        num_center_x = (NUMBER_BOX[0] + NUMBER_BOX[2]) / 2; num_center_y = (NUMBER_BOX[1] + NUMBER_BOX[3]) / 2
        draw.text((num_center_x, num_center_y), day_num_text, fill=TEXT_COLOR, font=font_day_num, anchor="mm")
        # 4. Draw Suffix
        suffix_pos_x = NUMBER_BOX[2] + SUFFIX_X_OFFSET; suffix_pos_y = NUMBER_BOX[1] + SUFFIX_Y_OFFSET
        draw.text((suffix_pos_x, suffix_pos_y), suffix_text, fill=TEXT_COLOR, font=font_suffix, anchor="lt")
        # 5. Draw Pub Name (Centered)
        pub_center_x = (PUB_BOX[0] + PUB_BOX[2]) / 2; pub_center_y = (PUB_BOX[1] + PUB_BOX[3]) / 2
        draw.text((pub_center_x, pub_center_y), pub_text, fill=TEXT_COLOR, font=font_pub, anchor="mm")

        # <<< NEW: Draw Optional Fields >>>
        # 6. Draw Event Type (Centered) - Only draw if text exists
        if event_type_final_text:
            event_type_center_x = (EVENT_TYPE_BOX[0] + EVENT_TYPE_BOX[2]) / 2
            event_type_center_y = (EVENT_TYPE_BOX[1] + EVENT_TYPE_BOX[3]) / 2
            draw.text((event_type_center_x, event_type_center_y), event_type_final_text, fill=TEXT_COLOR, font=font_event_type, anchor="mm")

        # 7. Draw Time (Right-aligned) - Only draw if text exists
        if time_final_text:
            time_right_x = TIME_BOX[2] # Right edge
            time_middle_y = (TIME_BOX[1] + TIME_BOX[3]) / 2 # Vertical center
            draw.text((time_right_x, time_middle_y), time_final_text, fill=TEXT_COLOR, font=font_time, anchor="rm") # Use 'rm'

        # 8. Draw First Place (Left-aligned) - Only draw if text exists
        if first_place_final_text:
            first_place_left_x = FIRST_PLACE_BOX[0] # Left edge
            first_place_middle_y = (FIRST_PLACE_BOX[1] + FIRST_PLACE_BOX[3]) / 2 # Vertical center
            draw.text((first_place_left_x, first_place_middle_y), first_place_final_text, fill=TEXT_COLOR, font=font_first_place, anchor="lm") # Use 'lm'


        print("Text drawing complete.")

        # --- Return the Image Object ---
        return img # Return the modified PIL Image object

    except FileNotFoundError:
        st.error(f"Error: Required file not found. Check paths.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during image generation.")
        print(f"Detailed Error: {e}") # Log detail to console
        traceback.print_exc()       # Log traceback to console
        return None

# --- Streamlit UI Code ---
st.set_page_config(layout="centered", page_title="Pub Society Poster")
st.title("🍻 Pub Soc Poster Generator 🦆")

# --- User Inputs ---
st.header("Required Info")
date_str_input = st.text_input(
    "Event Date", # Changed label slightly
    placeholder="e.g., 18 March or Tuesday 18 March",
    help="Enter the date like 'Month Day' or 'Weekday Day Month'"
)
pub_name_input = st.text_input("Pub Name (after first place)") # Clarified label

# <<< NEW: Optional Inputs Section >>>
st.markdown("---")
st.header("Optional Details (Defaults from Template)")

event_type_input = st.text_input("Event Type Text", value=DEFAULT_EVENT_TYPE)
time_input = st.text_input("Time", value=DEFAULT_TIME)
first_place_input = st.text_input("First Place Name", value=DEFAULT_FIRST_PLACE)
st.caption("Clear a field above if you don't want that text to appear.")

st.markdown("---") # Separator before button

# --- Generate Button and Logic ---
if st.button("✨ Generate Poster ✨"):
    # Basic validation for required fields
    if not date_str_input or not pub_name_input:
        st.warning("✋ Please enter at least the Date and Pub Name.")
    else:
        day_of_week, month, day_num_str = None, None, None
        event_date = None

        # --- Date Parsing ---
        print(f"Attempting to parse date: {date_str_input}")
        try:
            parsed = False
            for fmt in ("%B %d", "%A %d %B", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y",
                        "%A, %B %d", "%a %b %d", "%A %d", "%d %B"):
                 try:
                     now = datetime.datetime.now()
                     parsed_date = datetime.datetime.strptime(date_str_input, fmt)
                     if parsed_date.year == 1900: event_date = parsed_date.replace(year=now.year).date()
                     else: event_date = parsed_date.date()
                     if event_date < now.date() - datetime.timedelta(days=180): event_date = event_date.replace(year=event_date.year + 1)
                     parsed = True; break
                 except ValueError: continue

            if parsed:
                day_of_week = event_date.strftime("%A")
                month = event_date.strftime("%B")
                day_num_str = str(event_date.day)
                st.info(f"🗓️ Using date: {day_of_week}, {month} {day_num_str} ({event_date.year})")
            else:
                st.error("❌ Could not automatically parse date. Please use format like '4 July' or 'Tuesday 18 March'.")

        except Exception as e:
            st.error(f"🤯 Error during date parsing: {e}")
            event_date = None

        # --- Get Optional Values ---
        # These are retrieved directly from the input widgets now
        event_type_val = event_type_input
        time_val = time_input
        first_place_val = first_place_input

        # --- Call Image Generation if Date is Valid ---
        if day_of_week and month and day_num_str:
            with st.spinner("⏳ Generating image... keep yer pants on"):
                # <<< MODIFIED Function Call >>>
                generated_image = create_poster(
                    day_of_week, month, day_num_str, pub_name_input,
                    event_type_val, time_val, first_place_val # Pass new values
                )

            # --- Display Result ---
            if generated_image:
                st.success("✅ Poster Generated! now post to the IG x")
                st.image(generated_image, caption="Generated Poster", use_container_width=True)

                # --- Add Download Button ---
                try:
                    buf = BytesIO()
                    generated_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    download_filename = f"poster_{day_of_week.upper()}_{month.upper()}_{day_num_str}.png"
                    st.download_button(
                        label="💾 Download Poster", data=byte_im,
                        file_name=download_filename, mime="image/png"
                    )
                except Exception as e: st.error(f"Could not prepare image for download: {e}")
            else:
                 st.error("🙁 Image generation failed. Check errors above or console logs.")
        # else: Error message for date parsing shown above

# --- Footer ---
st.markdown("---")
st.caption("Enter the event details above and click generate. big up dan (me)")
