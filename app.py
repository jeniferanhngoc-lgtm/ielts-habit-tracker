import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Cấu hình trang
st.set_page_config(
    page_title="IELTS Practice Tracker", page_icon="📚", layout="wide"
)

DATA_FILE = "lich_su_bai_lam.json"

# Dữ liệu dạng bài
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


def calculate_band(correct, total):
    if total == 40:
        if correct >= 39:
            return 9.0
        elif correct >= 37:
            return 8.5
        elif correct >= 35:
            return 8.0
        elif correct >= 33:
            return 7.5
        elif correct >= 30:
            return 7.0
        elif correct >= 27:
            return 6.5
        elif correct >= 23:
            returnĐể chuyển đổi ứng dụng **Tkinter** (chạy trên máy tính cá nhân) thành một **Web App trên Streamlit** và đưa lên **GitHub** (để truy cập từ bất kỳ đâu), bạn cần hiểu điểm khác biệt quan trọng:

* **Tkinter** là thư viện desktop GUI native của Python, **không thể chạy trực tiếp trên trình duyệt web**.
* **Streamlit** là framework Python chuyên biệt cho Web App. Việc viết ứng dụng bằng Streamlit đơn giản hơn Tkinter rất nhiều (không cần quản lý Frame, Canvas, Scrollbar hay Canvas Arc thủ công).
* **GitHub + Streamlit Community Cloud** cho phép bạn lưu mã nguồn và đưa web lên mạng **hoàn toàn miễn phí**.

---

## 🛑 Lưu ý quan trọng về dữ liệu trên Streamlit Cloud

Khi bạn đưa web lên **Streamlit Community Cloud (miễn phí)**:
1. Môi trường lưu trữ là **éphemeral (tạm thời)**. Nếu web khởi động lại hoặc không dùng trong một thời gian, các file ghi cục bộ như `lich_su_bai_lam.json` sẽ bị xóa sạch về trạng thái ban đầu trên GitHub.
2. Để **lưu trữ dữ liệu cá nhân lâu dài**, giải pháp chuẩn nhất là dùng **Google Sheets** hoặc **Supabase / SQLite trên Cloud**. Tuy nhiên, để bắt đầu đơn giản nhất, bạn có thể lưu file `json` lên GitHub, hoặc kết nối Google Sheets với Streamlit chỉ qua vài dòng code.

---

## 🛠️ Bước 1: Viết lại ứng dụng bằng Streamlit (`app.py`)

Hãy tạo một file Python mới đặt tên là `app.py` và dán toàn bộ đoạn mã Streamlit đã được tối ưu hóa đầy đủ tính năng bên dưới. Code này đã thay thế toàn bộ Tkinter Canvas bằng các biểu đồ hiện đại của **Plotly** và **Pandas**.

```python
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

# Cấu hình trang
st.set_page_config(
    page_title="IELTS Practice & Habit Tracker", page_icon="📝", layout="wide"
)

DATA_FILE = "lich_su_bai_lam.json"

# --- DANH SÁCH DẠNG BÀI ---
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


# --- QUẢN LÝ DỮ LIỆU ---
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


# Nạp dữ liệu vào Session State
if "all_data" not in st.session_state:
    st.session_state.all_data = load_data()

# --- TIÊU ĐỀ TRANG ---
st.title("📝 Theo Dõi Luyện Tập & Habit Tracker (IELTS)")

# Chia bố cục 2 cột: Cột trái (Nhập liệu), Cột phải (Hiển thị)
col_left, col_right = st.columns([1, 2], gap="large")

# -----------------------------------------------------
# CỘT TRÁI: FORM NHẬP DỮ LIỆU
# -----------------------------------------------------
with col_left:
    st.subheader("📝 Nhập Bài Làm")

    title = st.text_input("1. Tên đề bài", value="Cam 18 - Test 1")
    skill_type = st.radio("2. Dạng kỹ năng", ["Reading", "Listening"], horizontal=True)

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
    st.markdown("**6. Số câu sai theo từng dạng bài:**")

    current_types = READING_TYPES if skill_type == "Reading" else LISTENING_TYPES
    errors = []

    for item_type in current_types:
        err_val = st.number_input(
            f"{item_type}", min_value=0, max_value=int(total_q), value=0, key=item_type
        )
        errors.append(err_val)

    if st.button("💾 Lưu Bài Làm", type="primary", use_container_width=True):
        total_wrong = sum(errors)
        if total_wrong > total_q:
            st.error(
                "❌ Tổng số câu sai không thể vượt quá tổng số câu hỏi!"
            )
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
                "types": current_types,
                "errors": errors,
            }

            st.session_state.all_data.append(entry_data)
            save_data(st.session_state.all_data)
            st.success(f"🎉 Đã lưu bài làm '{title}'!")
            st.rerun()

# -----------------------------------------------------
# CỘT PHẢI: HIỂN THỊ HABIT, BIỂU ĐỒ & BẢNG
# -----------------------------------------------------
with col_right:
    # Hàng trên: Habit Tracker & Biểu đồ tròn
    col_habit, col_chart = st.columns(2)

    all_data = st.session_state.all_data

    # 1. HABIT TRACKER
    with col_habit:
        st.subheader("🔥 Habit Tracker")

        today = datetime.now().date()
        day_counts = {}
        for item in all_data:
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
            days_to_show = [
                start_of_week + timedelta(days=i) for i in range(7)
            ]
            active_days = sum(1 for d in days_to_show if day_counts.get(d, 0) > 0)
            st.caption(f"📅 Tuần này hoàn thành: **{active_days}/7** ngày")
        else:
            days_to_show = [(today - timedelta(days=i)) for i in range(29, -1, -1)]
            active_days = sum(1 for d in days_to_show if day_counts.get(d, 0) > 0)
            st.caption(f"📅 30 ngày qua hoàn thành: **{active_days}/30** ngày")

        # Chuẩn bị dữ liệu hiển thị heatmap
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
            color_continuous_scale="Greens",
            text_auto=True,
        )
        fig_habit.update_layout(
            height=230,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_habit, use_container_width=True)

    # 2. BIỂU ĐỒ LỖI SAI (PIE CHART)
    with col_chart:
        st.subheader("📊 Biểu Đồ Lỗi Sai Lần Gần Nhất")
        if all_data:
            latest = all_data[-1]
            types_list = latest.get("types", [])
            errors_list = latest.get("errors", [])

            df_pie = pd.DataFrame(
                {"Dạng bài": types_list, "Số câu sai": errors_list}
            )
            df_pie = df_pie[df_pie["Số câu sai"] > 0]

            if not df_pie.empty:
                fig_pie = px.pie(
                    df_pie,
                    names="Dạng bài",
                    values="Số câu sai",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_pie.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.balloons()
                st.success("🎉 Bài làm gần nhất không sai câu nào!")
        else:
            st.info("Chưa có dữ liệu bài làm.")

    st.markdown("---")

    # 3. LỊCH SỬ LÀM BÀI
    st.subheader("🗓 Lịch Sử Làm Bài")

    if all_data:
        df_display = pd.DataFrame(all_data)[
            ["time", "title", "type", "correct", "score", "duration", "note"]
        ]
        df_display.columns = [
            "Thời gian",
            "Tên đề bài",
            "Kỹ năng",
            "Số câu đúng",
            "Band",
            "Thời gian",
            "Ghi chú",
        ]

        st.dataframe(df_display.iloc[::-1], use_container_width=True, hide_index=True)

        col_del, col_exp = st.columns(2)
        with col_exp:
            # Xuất file TXT / JSON
            json_string = json.dumps(all_data, ensure_ascii=False, indent=4)
            st.download_button(
                label="📄 Tải Báo Cáo JSON",
                data=json_string,
                file_name="lich_su_bai_lam.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_del:
            if st.button("❌ Xóa toàn bộ dữ liệu", use_container_width=True):
                st.session_state.all_data = []
                save_data([])
                st.rerun()
