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
        st.error(f"Lỗi khi lưu vào Google Sheets: {e}")
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

st.title("Theo Dõi Luyện Tập IELTS")
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("Nhập Bài Làm")
    title = st.text_input("1. Tên đề bài", value="Cam 18 - Test 1")
    skill_type = st.radio(
        "2. Kỹ năng", ["Reading", "Listening"], horizontal=True
    )

    col_q, col_d = st.columns(2)
    with col_q:
        total_q = st.number_input(
            "3. Tổng số câu", min_value=1, max_value=200, value=40
        )
    with col_d:
        duration = st.number_input(
            "4. Thời gian (phút)", min_value=1, max_value=180, value=60
        )

    note = st.text_input("5. Ghi chú / Từ vựng cần nhớ")
    st.markdown("---")

    current_parts = (
        READING_PARTS if skill_type == "Reading" else LISTENING_PARTS
    )
    current_types = (
        READING_TYPES if skill_type == "Reading" else LISTENING_TYPES
    )

    selected_part = st.selectbox(
        "6. Chọn Phần/Passage để nhập câu sai:", current_parts
    )

    if "temp_errors" not in st.session_state:
        st.session_state.temp_errors = {}

    st.markdown(f"**Nhập số câu sai cho [{selected_part}]:**")
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

    if st.button("Lưu Bài Làm", type="primary", use_container_width=True):
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
            st.error("Tổng số câu sai vượt quá tổng số câu hỏi.")
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
                "duration": f"{duration} phút",
                "note": note,
                "total_wrong": total_wrong,
                "details": detail_errors,
            }

            if save_entry_to_gsheets(entry_data):
                st.session_state.all_data = load_data_from_gsheets()
                st.session_state.temp_errors = {}
                st.success(f"Đã lưu thành công: {title}")
                st.rerun()

with col_right:
    col_habit, col_chart = st.columns(2)
    all_data = st.session_state.all_data

    with col_habit:
        st.subheader("Thói Quen Luyện Tập (Habit Grid)")
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

        # Chọn khoảng thời gian xem (12 tuần gần nhất (~3 tháng) hoặc 20 tuần)
        num_weeks = 16
        start_date = today - timedelta(
            days=today.weekday() + (num_weeks - 1) * 7
        )

        days_list = [start_date + timedelta(days=i) for i in range(num_weeks * 7)]
        grid_data = np.zeros((7, num_weeks))
        hover_text = []

        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for row in range(7):
            hover_row = []
            for col in range(num_weeks):
                d = start_date + timedelta(days=col * 7 + row)
                cnt = day_counts.get(d, 0)
                grid_data[row, col] = cnt
                hover_row.append(
                    f"{d.strftime('%Y-%m-%d')} ({days_of_week[row]}): {cnt} bài"
                )
            hover_text.append(hover_row)

        # Nhãn hiển thị tháng ở trục trên
        week_months = [
            (start_date + timedelta(days=c * 7)).strftime("%b")
            for c in range(num_weeks)
        ]

        # Tùy chỉnh dải màu Cyan/Xanh lá ngọc giống ảnh mẫu LeetCode/GitHub
        colorscale = [
            [0.0, "#1f292d"],  # Màu nền tối khi chưa làm bài (0 bài)
            [0.25, "#134e5e"],  # Xanh ngọc đậm (1 bài)
            [0.5, "#11998e"],  # Xanh ngọc vừa (2 bài)
            [0.75, "#00b4d8"],  # Cyan sáng (3 bài)
            [1.0, "#00f5d4"],  # Cyan nổi bật (>3 bài)
        ]

        fig_grid = go.Figure(
            data=go.Heatmap(
                z=grid_data,
                x=week_months,
                y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                text=hover_text,
                hoverinfo="text",
                colorscale=colorscale,
                showscale=False,
                xgap=3,  # Khoảng cách giữa các ô
                ygap=3,
            )
        )

        fig_grid.update_layout(
            height=240,
            margin=dict(l=10, r=10, t=25, b=10),
            plot_bgcolor="#181e24",  # Màu nền tối hợp chuẩn với hình mẫu
            paper_bgcolor="#0e1117",
            yaxis=dict(
                autorange="reversed",
                showgrid=False,
                zeroline=False,
                tickfont=dict(color="#8a99a8", size=11),
            ),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                side="top",
                tickfont=dict(color="#8a99a8", size=11),
            ),
        )

        st.plotly_chart(fig_grid, use_container_width=True)

    with col_chart:
        st.subheader("Phân Bố Lỗi Sai (Lần Gần Nhất)")
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
                st.info("Bài làm gần nhất không có câu sai.")
        else:
            st.info("Chưa có dữ liệu bài làm.")

    st.markdown("---")
    st.subheader("Lịch Sử Làm Bài")

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
            "Thời gian",
            "Tên đề bài",
            "Kỹ năng",
            "Số câu đúng",
            "Band",
            "Thời gian làm",
            "Ghi chú",
        ]
        st.dataframe(
            df_display.iloc[::-1], use_container_width=True, hide_index=True
        )
