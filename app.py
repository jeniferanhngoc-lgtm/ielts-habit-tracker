import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="IELTS Practice & Habit Tracker", layout="wide"
)

DATA_FILE = "lich_su_bai_lam.json"

# Danh sách dạng bài chuẩn
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


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


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
    st.session_state.all_data = load_data()

st.title("Theo Dõi Luyện Tập IELTS")

col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.subheader("Nhập Bài Làm")

    title = st.text_input("1. Tên đề bài", value="Cam 18 - Test 1")
    skill_type = st.radio("2. Kỹ năng", ["Reading", "Listening"], horizontal=True)

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
    
    # Chọn danh sách Parts/Passages và Types theo kỹ năng
    current_parts = READING_PARTS if skill_type == "Reading" else LISTENING_PARTS
    current_types = READING_TYPES if skill_type == "Reading" else LISTENING_TYPES

    # Thanh chọn Passage/Part
    selected_part = st.selectbox("6. Chọn Phần/Passage để nhập câu sai:", current_parts)

    # Khởi tạo bộ nhớ tạm cho các câu sai theo từng part trong Session State
    if "temp_errors" not in st.session_state:
        st.session_state.temp_errors = {}

    # Nhập số câu sai cho Passage đang chọn
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
        # Tính tổng tất cả câu sai của các Part/Passage thuộc bài làm hiện tại
        total_wrong = 0
        detail_errors = []

        for p in current_parts:
            for t in current_types:
                k = f"{skill_type}_{p}_{t}"
                err_count = st.session_state.temp_errors.get(k, 0)
                total_wrong += err_count
                if err_count > 0:
                    detail_errors.append({"part": p, "type": t, "count": err_count})

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

            st.session_state.all_data.append(entry_data)
            save_data(st.session_state.all_data)
            
            # Xóa dữ liệu tạm
            st.session_state.temp_errors = {}
            st.success(f"Đã lưu bài làm: {title}")
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
            "Chế độ xem", ["30 Ngày", "Tuần này"], horizontal=True, label_visibility="collapsed"
        )

        if view_mode == "Tuần này":
            start_of_week = today - timedelta(days=today.weekday())
            days_to_show = [start_of_week + timedelta(days=i) for i in range(7)]
            active_days = sum(1 for d in days_to_show if day_counts.get(d, 0) > 0)
            st.caption(f"Tuần này hoàn thành: {active_days}/7 ngày")
        else:
            days_to_show = [(today - timedelta(days=i)) for i in range(29, -1, -1)]
            active_days = sum(1 for d in days_to_show if day_counts.get(d, 0) > 0)
            st.caption(f"30 ngày qua hoàn thành: {active_days}/30 ngày")

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
        fig_habit.update_layout(
            height=230,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_habit, use_container_width=True)

    with col_chart:
        st.subheader("Phân Bố Lỗi Sai (Lần Gần Nhất)")
        if all_data:
            latest = all_data[-1]
            details = latest.get("details", [])

            if details:
                df_pie = pd.DataFrame(details)
                # Gom nhóm theo Dạng bài hoặc Passage để hiển thị
                df_grouped = df_pie.groupby("type")["count"].sum().reset_index()

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
        
        required_cols = ["time", "title", "type", "correct", "score", "duration", "note"]
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

        st.dataframe(df_display.iloc[::-1], use_container_width=True, hide_index=True)

        col_del, col_exp = st.columns(2)
        with col_exp:
            json_string = json.dumps(all_data, ensure_ascii=False, indent=4)
            st.download_button(
                label="Tải Báo Cáo JSON",
                data=json_string,
                file_name="lich_su_bai_lam.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_del:
            if st.button("Xóa toàn bộ dữ liệu", use_container_width=True):
                st.session_state.all_data = []
                save_data([])
                st.rerun()
