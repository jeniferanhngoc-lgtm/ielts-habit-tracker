import calendar
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="IELTS Practice & Habit Tracker", layout="wide"
)

SHEET_NAME = "IELTS TRACKER"
WORKSHEET_NAME = "History"


@st.cache_resource(ttl=600)
def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials_dict = dict(st.secrets["gspread"])
    creds = Credentials.from_service_account_info(
        credentials_dict, scopes=scopes
    )
    return gspread.authorize(creds)


def load_data_from_gsheets():
    try:
        client = get_gsheet_client()
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        records = sheet.get_all_records()
        for item in records:
            if "details" in item and isinstance(item["details"], str):
                try:
                    item["details"] = json.loads(item["details"])
                except Exception:
                    item["details"] = []
        return records
    except Exception:
        return []


def save_entry_to_gsheets(entry):
    try:
        client = get_gsheet_client()
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        details_str = json.dumps(entry.get("details", []), ensure_ascii=False)
        row = [
            entry.get("time", ""),
            entry.get("title", ""),
            entry.get("type", ""),
            entry.get("correct", ""),
            entry.get("score", ""),
            entry.get("duration", ""),
            entry.get("note", ""),
            entry.get("total_wrong", 0),
            details_str,
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False


READING_TYPES = [
    "True / False / Not Given",
    "Yes / No / Not Given",
    "Matching Headings",
    "Matching Info / Features",
    "Multiple Choice",
    "Gap Fill (Summary/Notes/Sentence)",
]
LISTENING_TYPES = [
    "Form / Note / Table Completion",
    "Multiple Choice",
    "Matching Options / Features",
    "Map / Plan / Diagram Labelling",
    "Short Answer Questions",
]
READING_PARTS = ["Passage 1", "Passage 2", "Passage 3"]
LISTENING_PARTS = ["Part 1", "Part 2", "Part 3", "Part 4"]


def calculate_score(correct_count, total_q):
    if total_q == 40:
        if correct_count >= 39:
            return 9.0
        if correct_count >= 37:
            return 8.5
        if correct_count >= 35:
            return 8.0
        if correct_count >= 33:
            return 7.5
        if correct_count >= 30:
            return 7.0
        if correct_count >= 27:
            return 6.5
        if correct_count >= 23:
            return 6.0
        if correct_count >= 19:
            return 5.5
        if correct_count >= 15:
            return 5.0
        return 4.0
    return round((correct_count / total_q) * 10, 1)


if "all_data" not in st.session_state:
    st.session_state.all_data = load_data_from_gsheets()

st.title("IELTS Practice & Habit Tracker")
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("Log Test Results")
    title = st.text_input("1. Test Title", value="Cam 18 - Test 1")
    skill_type = st.radio(
        "2. Skill", ["Reading", "Listening"], horizontal=True
    )

    col_q, col_d = st.columns(2)
    with col_q:
        total_q = st.number_input(
            "3. Total Questions", min_value=1, max_value=200, value=40
        )
    with col_d:
        duration = st.number_input(
            "4. Duration (mins)", min_value=1, max_value=180, value=60
        )

    note = st.text_input("5. Notes / Key Vocabulary")
    st.markdown("---")

    current_parts = (
        READING_PARTS if skill_type == "Reading" else LISTENING_PARTS
    )
    current_types = (
        READING_TYPES if skill_type == "Reading" else LISTENING_TYPES
    )

    selected_part = st.selectbox(
        "6. Select Section/Passage to log errors:", current_parts
    )

    if "temp_errors" not in st.session_state:
        st.session_state.temp_errors = {}

    st.markdown(f"**Incorrect answers for [{selected_part}]:**")
    for q_type in current_types:
        key_name = f"{skill_type}_{selected_part}_{q_type}"
        val = st.number_input(
            q_type,
            min_value=0,
            max_value=int(total_q),
            value=st.session_state.temp_errors.get(key_name, 0),
            key=key_name,
        )
        st.session_state.temp_errors[key_name] = val

    if st.button("Save Entry", type="primary", use_container_width=True):
        total_wrong = 0
        detail_errors = []
        for p in current_parts:
            for t in current_types:
                k = f"{skill_type}_{p}_{t}"
                err_count = st.session_state.temp_errors.get(k, 0)
                total_wrong += err_count
                if err_count > 0:
                    detail_errors.append(
                        {"part": p, "type": t, "count": err_count}
                    )

        if total_wrong > total_q:
            st.error("Total incorrect answers exceed total questions.")
        else:
            correct_count = total_q - total_wrong
            score = calculate_score(correct_count, total_q)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            entry_data = {
                "time": timestamp,
                "title": title,
                "type": skill_type,
                "correct": f"{correct_count}/{total_q}",
                "score": score,
                "duration": f"{duration} mins",
                "note": note,
                "total_wrong": total_wrong,
                "details": detail_errors,
            }

            if save_entry_to_gsheets(entry_data):
                st.session_state.all_data = load_data_from_gsheets()
                st.session_state.temp_errors = {}
                st.success(f"Saved successfully: {title}")
                st.rerun()

with col_right:
    col_habit, col_chart = st.columns(2)
    all_data = st.session_state.all_data

    with col_habit:
        st.subheader("Practice Habit Grid")
        today = datetime.now().date()

        day_counts = {}
        for item in all_data:
            if isinstance(item, dict) and "time" in item:
                try:
                    dt = datetime.strptime(
                        item["time"], "%Y-%m-%d %H:%M:%S"
                    ).date()
                    day_counts[dt] = day_counts.get(dt, 0) + 1
                except Exception:
                    pass

        # Xác định ngày đầu tiên và ngày cuối cùng của tháng hiện tại
        first_day_of_month = today.replace(day=1)
        _, last_day_num = calendar.monthrange(today.year, today.month)
        last_day_of_month = today.replace(day=last_day_num)

        # Căn lùi về thứ Hai của tuần chứa ngày 1
        start_date = first_day_of_month - timedelta(
            days=first_day_of_month.weekday()
        )
        # Căn tiến đến Chủ Nhật của tuần chứa ngày cuối tháng
        end_date = last_day_of_month + timedelta(
            days=(6 - last_day_of_month.weekday())
        )

        num_weeks = int(((end_date - start_date).days + 1) / 7)

        grid_data = np.zeros((7, num_weeks))
        hover_text = []

        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for row in range(7):
            hover_row = []
            for col in range(num_weeks):
                d = start_date + timedelta(days=col * 7 + row)

                # Chỉ đếm số bài nếu ngày nằm trong tháng hiện tại
                if d.month == today.month and d.year == today.year:
                    cnt = day_counts.get(d, 0)
                    grid_data[row, col] = cnt
                    hover_row.append(
                        f"{d.strftime('%Y-%m-%d')} ({days_of_week[row]}): {cnt} test(s)"
                    )
                else:
                    # Các ngày thuộc tháng khác trong cùng tuần sẽ ẩn (đặt -1)
                    grid_data[row, col] = -1
                    hover_row.append(f"{d.strftime('%Y-%m-%d')} (Out of month)")
            hover_text.append(hover_row)

        # Colorscale:
        # -1 (Ngoài tháng): Nền trong suốt hoàn toàn
        #  0 (0 bài làm): Trắng nhạt (#f8f9fa)
        #  1 bài: Xanh nhạt (#9be9a8)
        #  2 bài: Xanh vừa (#40c463)
        #  3 bài: Xanh đậm (#30a14e)
        # >=4 bài: Xanh rất đậm (#216e39)
        colorscale = [
            [0.0, "rgba(0,0,0,0)"],
            [0.1, "rgba(0,0,0,0)"],
            [0.1001, "#f8f9fa"],
            [0.2, "#f8f9fa"],
            [0.2001, "#9be9a8"],
            [0.4, "#9be9a8"],
            [0.4001, "#40c463"],
            [0.6, "#40c463"],
            [0.6001, "#30a14e"],
            [0.8, "#30a14e"],
            [0.8001, "#216e39"],
            [1.0, "#216e39"],
        ]

        # Đặt tiêu đề trục X chỉ hiện đúng tên tháng hiện tại ở giữa
        x_labels = [""] * num_weeks
        x_labels[num_weeks // 2] = today.strftime("%b")

        fig_grid = go.Figure(
            data=go.Heatmap(
                z=grid_data,
                x=list(range(num_weeks)),
                y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                text=hover_text,
                hoverinfo="text",
                colorscale=colorscale,
                zmin=-1,
                zmax=4,
                showscale=False,
                xgap=3,
                ygap=3,
            )
        )

        fig_grid.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=25, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(
                autorange="reversed",
                showgrid=False,
                zeroline=False,
                tickfont=dict(color="#31333F", size=11),
                scaleanchor="x",
                scaleratio=1,
                constrain="domain",
            ),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                side="top",
                tickmode="array",
                tickvals=list(range(num_weeks)),
                ticktext=x_labels,
                tickfont=dict(color="#31333F", size=12, family="Arial Bold"),
            ),
        )

        st.plotly_chart(fig_grid, use_container_width=True)

    with col_chart:
        st.subheader("Error Distribution (Latest)")
        if all_data:
            latest = all_data[-1]
            details = latest.get("details", [])
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = []

            if details:
                df_pie = pd.DataFrame(details)
                df_grouped = (
                    df_pie.groupby("type")["count"].sum().reset_index()
                )
                fig_pie = px.pie(
                    df_grouped,
                    names="type",
                    values="count",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig_pie.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No errors recorded in the latest session.")
        else:
            st.info("No test history available.")

    st.markdown("---")
    st.subheader("Practice History")

    if all_data:
        df_all = pd.DataFrame(all_data)
        required_cols = [
            "time",
            "title",
            "type",
            "correct",
            "score",
            "duration",
            "note",
        ]
        for col in required_cols:
            if col not in df_all.columns:
                df_all[col] = ""

        df_display = df_all[required_cols]
        df_display.columns = [
            "Timestamp",
            "Test Title",
            "Skill",
            "Correct",
            "Band Score",
            "Duration",
            "Notes",
        ]
        st.dataframe(
            df_display.iloc[::-1], use_container_width=True, hide_index=True
        )
