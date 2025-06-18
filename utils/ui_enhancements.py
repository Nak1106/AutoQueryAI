"""
UI Enhancements: Toasts, dark mode, export, tabs, expanders (Part 7).
"""
import streamlit as st

def show_toast(message, icon="✅"):
    st.toast(message, icon=icon)

def export_to_csv(df, filename="result.csv"):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Export CSV", csv, filename, "text/csv")

def export_to_png(fig, filename="chart.png"):
    fig.write_image(filename)
    with open(filename, "rb") as f:
        st.download_button("Export PNG", f, filename, "image/png")

def dark_mode_toggle():
    st.toggle("🌙 Dark mode")
