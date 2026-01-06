import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Bus Booking", layout="centered")

CSV_FILE = "bus_booking_data.csv"

# ---------- INIT SESSION STATE ----------
if "selected_seat" not in st.session_state:
    st.session_state.selected_seat = None

if "selected_bus" not in st.session_state:
    st.session_state.selected_bus = "Bus 1"

# ---------- LOAD / CREATE DATA ----------
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=[
        "Bus", "Seat", "Name", "Mobile",
        "Boarding Point", "Payment Time", "Screenshot"
    ])
    df.to_csv(CSV_FILE, index=False)
else:
    df = pd.read_csv(CSV_FILE)

# ---------- UI ----------
st.title("🚌 Mahashivaratri Bus Booking")

bus = st.selectbox(
    "Select a bus",
    ["Bus 1", "Bus 2", "Bus 3", "Bus 4"],
    index=["Bus 1", "Bus 2", "Bus 3", "Bus 4"].index(st.session_state.selected_bus)
)

st.session_state.selected_bus = bus

st.subheader(f"Seat Layout for {bus}")

bus_df = df[df["Bus"] == bus]
booked_seats = bus_df["Seat"].tolist()
all_seats = list(range(1, 50))

# ---------- SEAT GRID ----------
cols = st.columns(7)
for i, seat in enumerate(all_seats):
    col = cols[i % 7]

    if seat in booked_seats:
        col.button(f"Seat {seat}", disabled=True)
    else:
        if col.button(f"Seat {seat}", key=f"{bus}_{seat}"):
            st.session_state.selected_seat = seat

# ---------- BOOKING FORM ----------
if st.session_state.selected_seat:
    st.divider()
    st.subheader(f"Booking Seat {st.session_state.selected_seat}")

    with st.form("booking_form", clear_on_submit=True):
        name = st.text_input("Your name")
        mobile = st.text_input("Mobile number")
        boarding = st.selectbox("Boarding point", ["Tampines", "Punggol"])
        payment_time = st.text_input("Payment time (e.g. 9:30 PM)")
        screenshot = st.file_uploader("Payment screenshot (optional)", type=["jpg", "png", "jpeg"])

        submit = st.form_submit_button("Confirm Booking")

        if submit:
            if not name or not mobile or not payment_time:
                st.error("Please fill all required fields")
            else:
                new_row = {
                    "Bus": bus,
                    "Seat": st.session_state.selected_seat,
                    "Name": name,
                    "Mobile": mobile,
                    "Boarding Point": boarding,
                    "Payment Time": payment_time,
                    "Screenshot": screenshot.name if screenshot else ""
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)

                st.success(f"Seat {st.session_state.selected_seat} booked successfully!")

                # RESET SEAT AFTER BOOKING
                st.session_state.selected_seat = None
                st.experimental_rerun()
