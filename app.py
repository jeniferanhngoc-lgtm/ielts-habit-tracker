import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
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
        st.subheader("Thống Kê Luyện Tập")
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

        view_mode = st.radio(
            "Chế độ xem",
            ["Tuần này", "30 Ngày"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view_mode == "Tuần này":
            week_days_str = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            start_of_week = today - timedelta(days=today.weekday())
            days_to_show = [
                start_of_week + timedelta(days=i) for i in range(7)
            ]
            active_days = sum(
                1 for d in days_to_show if day_counts.get(d, 0) > 0
            )
            st.caption(f"📅 Tuần này: Đã luyện tập {active_days}/7 ngày")

            x_labels = [
                f"<b>{week_days_str[i]}</b><br>{d.strftime('%d/%m')}"
                for i, d in enumerate(days_to_show)
            ]
            counts = [day_counts.get(d, 0) for d in days_to_show]

            # Biểu diễn theo ô vuông (Heatmap 1 hàng)
            fig_habit = px.imshow(
                [counts],
                labels=dict(x="Ngày", y="", color="Số bài"),
                x=x_labels,
                y=[""],
                color_continuous_scale=[
                    "#ebedf0",
                    "#9be9a8",
                    "#40c463",
                    "#30a14e",
                    "#216e39",
                ],
                text_auto=True,
            )
            fig_habit.update_coloraxes(showscale=False)
            fig_habit.update_layout(
                height=180,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(tickangle=0),
            )
            st.plotly_chart(fig_habit, use_container_width=True)

        else:
            days_to_show = [
                (today - timedelta(days=i)) for i in range(29, -1, -1)
            ]
            active_days = sum(
                1 for d in days_to_show if day_counts.get(d, 0) > 0
            )
            st.caption(f"📅 30 ngày qua: Đã luyện tập {active_days}/30 ngày")

            habit_df = pd.DataFrame(
                [
                    {
                        "Ngày": d.strftime("%d/%m"),
                        "Số bài": day_counts.get(d, 0),
                    }
                    for d in days_to_show
                ]
            )
            fig_habit = px.bar(
                habit_df,
                x="Ngày",
                y="Số bài",
                color="Số bài",
                color_continuous_scale="Blues",
                text_auto=True,
            )
            # Cố định gốc trục Y từ 0 trở lên
            fig_habit.update_yaxes(rangemode="tozero", dtick=1)
            fig_habit.update_layout(
                height=200,
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_habit, use_container_width=True)

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
