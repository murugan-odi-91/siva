import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid

st.set_page_config(page_title="Bus Booking", layout="centered")

# -----------------------
# Storage paths (Streamlit Cloud safe)
# -----------------------
DATA_DIR = Path("/tmp/bus_booking_app")
DATA_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = DATA_DIR / "bus_booking_data.csv"
UPLOAD_DIR = DATA_DIR / "payment_screenshots"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------
# Session state
# -----------------------
if "selected_bus" not in st.session_state:
    st.session_state.selected_bus = "Bus 1"
if "selected_seats" not in st.session_state:
    st.session_state.selected_seats = []  # list[int]
if "seat_count" not in st.session_state:
    st.session_state.seat_count = 1

# -----------------------
# Load / init CSV
# -----------------------
def load_df() -> pd.DataFrame:
    if CSV_FILE.exists():
        df_ = pd.read_csv(CSV_FILE)
        # Ensure Seat is int for comparisons
        if not df_.empty:
            df_["Seat"] = df_["Seat"].astype(int)
        return df_
    else:
        df_ = pd.DataFrame(columns=[
            "BookingID", "Bus", "Seat",
            "Name", "Mobile",
            "BoardingPoint", "PaymentTime",
            "ScreenshotFile", "CreatedAt"
        ])
        df_.to_csv(CSV_FILE, index=False)
        return df_

def save_df(df_: pd.DataFrame) -> None:
    df_.to_csv(CSV_FILE, index=False)

df = load_df()

# -----------------------
# Helpers
# -----------------------
def booked_seats_for_bus(bus: str) -> set:
    if df.empty:
        return set()
    return set(df.loc[df["Bus"] == bus, "Seat"].astype(int).tolist())

def toggle_seat(seat: int, booked: set, max_count: int):
    # Cannot select booked seat
    if seat in booked:
        return

    # Toggle selection
    if seat in st.session_state.selected_seats:
        st.session_state.selected_seats.remove(seat)
    else:
        # Limit to requested seat count
        if len(st.session_state.selected_seats) < max_count:
            st.session_state.selected_seats.append(seat)

# -----------------------
# UI
# -----------------------
st.title("Bus Booking App")

bus = st.selectbox(
    "Select a bus",
    ["Bus 1", "Bus 2", "Bus 3", "Bus 4"],
    index=["Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(st.session_state.selected_bus),
)

# If bus changed, clear selection
if bus != st.session_state.selected_bus:
    st.session_state.selected_bus = bus
    st.session_state.selected_seats = []

st.session_state.seat_count = st.number_input(
    "Number of seats needed",
    min_value=1,
    max_value=49,
    value=int(st.session_state.seat_count),
    step=1
)

booked = booked_seats_for_bus(bus)

st.subheader(f"Seat Layout for {bus}")
st.caption("Legend: 🟩 Available | 🟥 Booked | ✅ Selected")

# Seat grid
cols = st.columns(7)
for i in range(1, 50):
    col = cols[(i - 1) % 7]

    is_booked = i in booked
    is_selected = i in st.session_state.selected_seats

    if is_booked:
        label = f"🟥 Seat {i}"
        col.button(label, key=f"{bus}_seat_{i}", disabled=True)
    else:
        label = f"✅ Seat {i}" if is_selected else f"🟩 Seat {i}"
        if col.button(label, key=f"{bus}_seat_{i}"):
            toggle_seat(i, booked, int(st.session_state.seat_count))

# Selected seats display
st.write(f"Selected seats: **{sorted(st.session_state.selected_seats)}** "
         f"({len(st.session_state.selected_seats)}/{int(st.session_state.seat_count)})")

# Booking form (only if seats selected)
if len(st.session_state.selected_seats) > 0:
    st.divider()
    st.subheader("Enter booking details")

    with st.form("booking_form", clear_on_submit=True):
        name = st.text_input("Name *")
        mobile = st.text_input("Mobile number *")
        boarding = st.selectbox("Boarding point *", ["Tampines", "Punggol"])
        payment_time = st.text_input("Payment time * (e.g., 9:30 PM or 2026-01-06 21:30)")
        screenshot = st.file_uploader("Payment screenshot (optional)", type=["jpg", "jpeg", "png"])

        submit = st.form_submit_button("Confirm Booking")

    if submit:
        # Basic validation
        if not name.strip() or not mobile.strip() or not payment_time.strip():
            st.error("Please fill all required fields (*)")
        elif len(st.session_state.selected_seats) != int(st.session_state.seat_count):
            st.error("Please select the exact number of seats you requested before confirming.")
        else:
            # Re-check availability at the moment of submit (avoid race condition)
            df = load_df()
            booked_now = booked_seats_for_bus(bus)
            clash = set(st.session_state.selected_seats).intersection(booked_now)
            if clash:
                st.error(f"These seats were just booked by someone else: {sorted(clash)}. Please reselect.")
            else:
                booking_id = str(uuid.uuid4())[:8]
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                screenshot_filename = ""
                if screenshot is not None:
                    ext = Path(screenshot.name).suffix.lower()
                    screenshot_filename = f"{booking_id}{ext}"
                    with open(UPLOAD_DIR / screenshot_filename, "wb") as f:
                        f.write(screenshot.getbuffer())

                # Save one row per seat (simplifies availability)
                rows = []
                for seat in st.session_state.selected_seats:
                    rows.append({
                        "BookingID": booking_id,
                        "Bus": bus,
                        "Seat": int(seat),
                        "Name": name.strip(),
                        "Mobile": mobile.strip(),
                        "BoardingPoint": boarding,
                        "PaymentTime": payment_time.strip(),
                        "ScreenshotFile": screenshot_filename,
                        "CreatedAt": created_at
                    })

                df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
                save_df(df)

                st.success(f"Booking successful! Bus: {bus}, Seats: {sorted(st.session_state.selected_seats)}, BookingID: {booking_id}")

                # Clear selection and refresh
                st.session_state.selected_seats = []
                st.rerun()

# Admin download (optional but useful)
st.divider()
st.subheader("Download bookings (Admin)")

df_latest = load_df()
csv_bytes = df_latest.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv_bytes,
    file_name="bus_booking_data.csv",
    mime="text/csv"
)

st.caption(f"CSV storage location (server): {CSV_FILE}")
