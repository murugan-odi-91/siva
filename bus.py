import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Load or create the CSV file
CSV_FILE = "bus_booking_data.csv"
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["Bus", "Seat", "Name", "Mobile", "Boarding Point", "Payment Time", "Payment Screenshot"])
    df.to_csv(CSV_FILE, index=False)
else:
    df = pd.read_csv(CSV_FILE)

st.title("Bus Booking App")

# Select a bus
bus_options = ["Bus 1", "Bus 2", "Bus 3", "Bus 4"]
bus_choice = st.selectbox("Select a bus", bus_options)

# Show seat layout (a simple grid of buttons)
bus_df = df[df["Bus"] == bus_choice]
all_seats = list(range(1, 50))
booked_seats = bus_df["Seat"].tolist()

st.subheader(f"Seat Layout for {bus_choice}")
cols = st.columns(7)  # Create 7 columns for seat buttons (adjust as needed)

selected_seat = None
for i, seat in enumerate(all_seats):
    is_booked = seat in booked_seats
    if is_booked:
        cols[i % 7].button(f"Seat {seat}", disabled=True)
    else:
        if cols[i % 7].button(f"Seat {seat}"):
            selected_seat = seat

# Get user details if a seat is selected
if selected_seat:
    name = st.text_input("Your name")
    mobile = st.text_input("Your mobile number")
    num_seats = st.number_input("Number of seats", min_value=1, max_value=49, value=1)
    boarding_point = st.selectbox("Choose boarding point", ["Tampines", "Punggol"])
    payment_time = st.text_input("Payment time (e.g., 2025-12-01 14:30)")
    payment_screenshot = st.file_uploader("Upload payment screenshot (optional)", type=["png", "jpg", "jpeg"])

    if st.button("Confirm Booking"):
        if name and mobile and payment_time:
            # Save booking data
            new_booking = {
                "Bus": bus_choice,
                "Seat": selected_seat,
                "Name": name,
                "Mobile": mobile,
                "Boarding Point": boarding_point,
                "Payment Time": payment_time,
                "Payment Screenshot": payment_screenshot.name if payment_screenshot else None
            }
            df = df.append(new_booking, ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success(f"Seat {selected_seat} on {bus_choice} booked successfully for {name}!")
        else:
            st.error("Please fill in all required fields.")

# You can add the cancellation logic here as well (similar to the previous example)
