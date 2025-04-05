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

# --- Calculate Box Tuples (x0, y0, x1, y1) ---
# These are derived from the X, Y, W, H values above and used by the drawing functions
DAY_BOX = (DAY_X, DAY_Y, DAY_X + DAY_W, DAY_Y + DAY_H)
MONTH_BOX = (MONTH_X, MONTH_Y, MONTH_X + MONTH_W, MONTH_Y + MONTH_H)
NUMBER_BOX = (NUMBER_X, NUMBER_Y, NUMBER_X + NUMBER_W, NUMBER_Y + NUMBER_H)
PUB_BOX = (PUB_X, PUB_Y, PUB_X + PUB_W, PUB_Y + PUB_H)

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
    # Removed print statement for cleaner Streamlit output, uncomment if debugging size issues
    # print(f"    Finding font size for '{text}' in box W={target_w}, H={target_h}")
    if target_w <= 0 or target_h <= 0: return 10
    font_size = int(target_h * 0.9); best_size = 10
    while font_size >= 10:
        try:
            font = ImageFont.truetype(font_path, font_size) # Use full font_path
            bbox = draw.textbbox((0, 0), text, font=font, anchor="lt")
            text_w = bbox[2] - bbox[0]; text_h = bbox[3] - bbox[1]
            if text_w <= target_w and text_h <= target_h:
                best_size = font_size
                # print(f"    Found best fit: size {best_size} (Text W={text_w:.0f}, H={text_h:.0f})")
                return best_size
            font_size -= 5
            if font_size < 10: font_size = 9
        except IOError:
            st.error(f"FATAL ERROR: Font file '{font_path}' not found during size calculation. Cannot proceed.")
            return None # Indicate fatal error
        except Exception as e:
            print(f"    Error calc bbox size {font_size}: {e}"); font_size -= 5 # Continue trying smaller sizes
    # print(f"    Warning: Could not fit '{text}'. Using {best_size}.")
    return best_size

# --- Main Image Generation Logic ---
def create_poster(day_of_week, month, day_num_str, pub_name):
    """Generates the poster image object."""
    print(f"\n--- Generating Poster ---") # Keep console logs for debugging
    print(f"Date: {day_of_week} {month} {day_num_str}, Pub: {pub_name}")
    print(f"Using Template: {TEMPLATE_PATH}")
    print(f"Using Font: {FONT_PATH}")

    try:
        # Check if template and font exist before proceeding
        if not os.path.exists(TEMPLATE_PATH):
            st.error(f"Template image not found at: {TEMPLATE_PATH}")
            return None
        if not os.path.exists(FONT_PATH):
            st.error(f"Font file not found at: {FONT_PATH}")
            return None

        img = Image.open(TEMPLATE_PATH).convert("RGB")
        print(f"Template size: {img.size}")
        draw = ImageDraw.Draw(img)

        # --- Prepare Text ---
        day_text = day_of_week.upper()
        month_text = month.upper()
        try:
            day_num = int(day_num_str); day_num_text = str(day_num)
        except ValueError:
             st.error(f"Internal Error: Invalid day number '{day_num_str}'.")
             return None
        suffix_text = get_ordinal_suffix(day_num).upper()
        pub_text = pub_name.upper()

        # --- Determine Optimal Font Sizes ---
        print("Determining optimal font sizes...")
        day_opt_size = find_max_font_size(day_text, FONT_PATH, DAY_BOX, draw)
        month_opt_size = find_max_font_size(month_text, FONT_PATH, MONTH_BOX, draw)
        num_opt_size = find_max_font_size(day_num_text, FONT_PATH, NUMBER_BOX, draw)
        pub_opt_size = find_max_font_size(pub_text, FONT_PATH, PUB_BOX, draw)

        # Check if any font size calculation failed (returned None)
        if None in [day_opt_size, month_opt_size, num_opt_size, pub_opt_size]:
            # Error already shown by find_max_font_size if font wasn't found
            return None

        # --- Load Fonts with Optimal Sizes ---
        print("Loading fonts with determined sizes...")
        try:
            font_day = ImageFont.truetype(FONT_PATH, day_opt_size)
            font_month = ImageFont.truetype(FONT_PATH, month_opt_size)
            font_day_num = ImageFont.truetype(FONT_PATH, num_opt_size)
            font_suffix = ImageFont.truetype(FONT_PATH, SUFFIX_SIZE)
            font_pub = ImageFont.truetype(FONT_PATH, pub_opt_size)
        # IOError should be caught by earlier check or find_max_font_size, but catch defensively
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

        print("Text drawing complete.")

        # --- Return the Image Object ---
        return img # Return the modified PIL Image object

    except FileNotFoundError:
        # This specific error might be redundant due to earlier checks, but good backup
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
date_str_input = st.text_input(
    "Enter Event Date!!",
    placeholder="e.g., 18 March or Tuesday 18 March",
    help="Enter the date like 'Month Day' or 'Weekday Day Month'"
)
pub_name_input = st.text_input("Enter Pub Name")

# --- Generate Button and Logic ---
if st.button("✨ Generate Poster ✨"):
    if not date_str_input or not pub_name_input:
        st.warning("✋ Please enter both a date and a pub name.")
    else:
        day_of_week, month, day_num_str = None, None, None
        event_date = None

        # --- Date Parsing ---
        print(f"Attempting to parse date: {date_str_input}") # Console log
        try:
            parsed = False
            # Try common date formats
            for fmt in ("%B %d", "%A %d %B", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y",
                        "%A, %B %d", "%a %b %d", "%A %d", "%d %B"):
                 try:
                     now = datetime.datetime.now()
                     parsed_date = datetime.datetime.strptime(date_str_input, fmt)
                     # Handle cases where year is missing - default to current/next year
                     if parsed_date.year == 1900:
                         event_date = parsed_date.replace(year=now.year).date()
                     else:
                         event_date = parsed_date.date()
                     # Sensible year check (if date seems far in the past, assume next year)
                     if event_date < now.date() - datetime.timedelta(days=180):
                         event_date = event_date.replace(year=event_date.year + 1)
                     parsed = True; break # Stop on first successful parse
                 except ValueError:
                     continue # Try next format

            if parsed:
                day_of_week = event_date.strftime("%A")
                month = event_date.strftime("%B")
                day_num_str = str(event_date.day)
                st.info(f"🗓️ Using date: {day_of_week}, {month} {day_num_str} ({event_date.year})")
            else:
                st.error("❌ Could not automatically parse date. Please use format like '4 July' or 'Tuesday 18 March'.")

        except Exception as e:
            st.error(f"🤯 Error during date parsing: {e}")
            event_date = None # Ensure we don't proceed if parsing fails unexpectedly

        # --- Call Image Generation if Date is Valid ---
        if day_of_week and month and day_num_str:
            with st.spinner("⏳ Generating image... keep yer pants on"): # Show a loading indicator
                generated_image = create_poster(day_of_week, month, day_num_str, pub_name_input)

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
                        label="💾 Download Poster",
                        data=byte_im,
                        file_name=download_filename,
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"Could not prepare image for download: {e}")

            else:
                # Error message already shown by create_poster or find_max_font_size
                st.error("🙁 Image generation failed. See console/logs for details if running locally.")
        # else: (Error message for date parsing shown above)

# --- Footer ---
st.markdown("---")
st.caption("Enter the event details above and click generate. big up dan (me)")