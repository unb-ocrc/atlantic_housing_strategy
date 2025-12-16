import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# ---------------- Sidebar Styling ----------------
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        width: 350px;
    }
    [data-baseweb="select"] {
        min-width: 300px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- Load Data ----------------
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel("2025-12-12 Updated Summary Sheet.xlsx", sheet_name="Sheet1")
    df["Expected Timeline"] = df["Expected Timeline"].astype(str)
    df = df.rename(columns={"Updated Initiative": "Initiative"})
    return df

df = load_data()

# ---------------- Preprocess Tokens & Images ----------------
@st.cache_data(show_spinner=False)
def preprocess_tokens(df):
    df = df.copy()
    df["location_tokens"] = df["Location Identified"].apply(
        lambda cell: [part.strip() for part in str(cell).split(",") if part.strip() != ""]
    )
    df["stakeholder_tokens"] = df["Filtering-Contributors-Categories"].apply(
        lambda cell: [part.strip() for part in str(cell).split(",") if part.strip() != ""]
    )
    df["has_image"] = df["ID"].apply(lambda x: os.path.exists(f"assets/{x}.png"))
    return df[df["has_image"]]

df = preprocess_tokens(df)

st.title("Atlantic Housing Innovation Strategy")

# ---------------- Session State Initialization ----------------
for key in [
    "category_filter",
    "subcategory_filter",
    "location_filter",
    "stakeholder_filter",
    "timeline_filter",
    "active_tab"
]:
    if key not in st.session_state:
        st.session_state[key] = [] if "tab" not in key else "Dashboard View"

st.sidebar.header("Filters")

# ---------------- Reset Filters ----------------
def reset_filters():
    st.session_state.category_filter = []
    st.session_state.subcategory_filter = []
    st.session_state.location_filter = []
    st.session_state.stakeholder_filter = []
    st.session_state.timeline_filter = []

st.sidebar.button("Reset Filters", on_click=reset_filters)

# ---------------- Filter Logic ----------------
def filter_df():
    filtered = df.copy()

    if st.session_state.category_filter:
        filtered = filtered[filtered["Category"].isin(st.session_state.category_filter)]

    if st.session_state.subcategory_filter:
        filtered = filtered[filtered["Sub-Category"].isin(st.session_state.subcategory_filter)]

    if st.session_state.location_filter:
        filtered = filtered[
            filtered["location_tokens"].apply(
                lambda tokens: any(l in tokens for l in st.session_state.location_filter)
            )
        ]

    if st.session_state.stakeholder_filter:
        filtered = filtered[
            filtered["stakeholder_tokens"].apply(
                lambda tokens: any(s in tokens for s in st.session_state.stakeholder_filter)
            )
        ]

    if st.session_state.timeline_filter:
        filtered = filtered[filtered["Expected Timeline"].isin(st.session_state.timeline_filter)]

    return filtered

# ---------------- Filter Options ----------------
filtered_for_options = filter_df()

category_options = sorted(filtered_for_options["Category"].dropna().unique())
st.session_state.category_filter = [c for c in st.session_state.category_filter if c in category_options]

subcategory_options = sorted(filtered_for_options["Sub-Category"].dropna().unique())
st.session_state.subcategory_filter = [sc for sc in st.session_state.subcategory_filter if sc in subcategory_options]

location_options = sorted({
    loc
    for cell in filtered_for_options["Location Identified"]
    for loc in (cell.split(",") if pd.notna(cell) else [])
})
st.session_state.location_filter = [l for l in st.session_state.location_filter if l in location_options]

stakeholder_options = sorted({
    s
    for cell in filtered_for_options["Filtering-Contributors-Categories"]
    for s in (cell.split(",") if pd.notna(cell) else [])
})
st.session_state.stakeholder_filter = [s for s in st.session_state.stakeholder_filter if s in stakeholder_options]

timeline_options = sorted(filtered_for_options["Expected Timeline"].dropna().astype(str).unique())
st.session_state.timeline_filter = [t for t in st.session_state.timeline_filter if t in timeline_options]

# ---------------- Sidebar Multiselects ----------------
st.sidebar.multiselect("Category", options=category_options, key="category_filter")
st.sidebar.multiselect("Subcategory", options=subcategory_options, key="subcategory_filter")
st.sidebar.multiselect("Expected Timeline", options=timeline_options, key="timeline_filter")
st.sidebar.multiselect("Location Identified", options=location_options, key="location_filter")
st.sidebar.multiselect("Contributor/Owner Category", options=stakeholder_options, key="stakeholder_filter")

# ---------------- Filtered Data ----------------
filtered = filter_df()

# ---------------- Tabs ----------------
tab1, tab2 = st.tabs(["Dashboard View", "Initiatives View"])

# ---------------- Dashboard View ----------------
with tab1:
    st.header("Dashboards")
    st.write("---")

    if filtered.empty:
        st.write("No images match your filters.")
    else:
        for img_id in filtered["ID"]:
            file_path = f"assets/{img_id}.png"
            if os.path.exists(file_path):
                st.image(file_path, width=1200)
            else:
                st.write(f"Missing image: {img_id}.png")

# ---------------- Initiatives View ----------------
with tab2:
    st.header("Initiatives Overview")
    st.write("---")

    if filtered.empty:
        st.write("No initiatives match your filters.")
    else:
        display_cols = [
            "ID",
            "Initiative",
            "Category",
            "Location Identified",
            "Expected Timeline",
        ]

        filtered_subset = filtered[display_cols].copy()

        # Cached HTML table
        @st.cache_data(show_spinner=False)
        def render_initiatives_html(df_subset):
            df_copy = df_subset.copy()
            df_copy["Initiative"] = df_copy["Initiative"].str.replace("\n", "<br>")
            return df_copy.to_html(index=False, table_id="custom_table", escape=False)

        html_table = render_initiatives_html(filtered_subset)
        st.markdown(html_table, unsafe_allow_html=True)

        # CSS styling
        st.markdown(
            """
            <style>
            #custom_table th:nth-child(1), #custom_table td:nth-child(1) { width: 70px; }
            #custom_table th:nth-child(2), #custom_table td:nth-child(2) { width: 450px; }
            #custom_table th:nth-child(3), #custom_table td:nth-child(3) { width: 175px; }
            #custom_table th:nth-child(4), #custom_table td:nth-child(4) { width: 175px; }
            #custom_table th:nth-child(5), #custom_table td:nth-child(5) { width: 150px; }

            #custom_table {
                border-collapse: collapse;
                width: 100%;
            }
            #custom_table th, #custom_table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                word-wrap: break-word;
                word-break: break-word;
            }
            #custom_table th {
                background-color: #f2f2f2;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
