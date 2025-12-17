import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# Sidebar styling
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

# --- Load Excel (cached) ---
@st.cache_data(show_spinner=False)
def load_excel():
    return pd.read_excel(
        "2025-12-12 Updated Summary Sheet.xlsx",
        sheet_name="Sheet1"
    )

# --- Preprocess tokens and check images (cached) ---
@st.cache_data(show_spinner=False)
def preprocess_tokens(df):
    df = df.copy()
    df["location_tokens"] = df["Location Identified"].apply(
        lambda cell: [p.strip() for p in str(cell).split(",") if p.strip()]
    )
    df["stakeholder_tokens"] = df["Filtering-Contributors-Categories"].apply(
        lambda cell: [p.strip() for p in str(cell).split(",") if p.strip()]
    )
    df["has_image"] = df["ID"].apply(lambda x: os.path.exists(f"assets/{x}.png"))
    return df[df["has_image"]]

# --- Cached HTML table rendering ---
@st.cache_data(show_spinner=False)
def render_initiatives_html(df_subset):
    df_copy = df_subset.copy()
    df_copy["Initiative"] = df_copy["Initiative"].str.replace("\n", "<br>")
    return df_copy.to_html(index=False, table_id="custom_table", escape=False)

# --- Cached baseline initiatives HTML (NO FILTERS) ---
@st.cache_data(show_spinner=False)
def get_base_initiatives_html(df):
    display_cols = ["ID", "Initiative", "Category", "Location Identified"]
    return render_initiatives_html(df[display_cols])

# --- Load + preprocess ---
df_raw = load_excel()
df = preprocess_tokens(df_raw)

st.title("Atlantic Housing Innovation Strategy")

# --- Session State Initialization ---
for key in ["category_filter", "subcategory_filter", "location_filter", "stakeholder_filter"]:
    if key not in st.session_state:
        st.session_state[key] = []

# 🔑 Store baseline initiatives HTML ONCE per session
if "base_initiatives_html" not in st.session_state:
    st.session_state.base_initiatives_html = get_base_initiatives_html(df)

st.sidebar.header("Filters")

def reset_filters():
    st.session_state.category_filter = []
    st.session_state.subcategory_filter = []
    st.session_state.location_filter = []
    st.session_state.stakeholder_filter = []

st.sidebar.button("Reset Filters", on_click=reset_filters)

# --- Helper: detect no filters ---
def no_filters_applied():
    return (
        not st.session_state.category_filter
        and not st.session_state.subcategory_filter
        and not st.session_state.location_filter
        and not st.session_state.stakeholder_filter
    )

# --- Filter logic ---
def filter_df():
    if no_filters_applied():
        return df

    filtered = df
    if st.session_state.category_filter:
        filtered = filtered[filtered["Category"].isin(st.session_state.category_filter)]
    if st.session_state.subcategory_filter:
        filtered = filtered[filtered["Sub-Category"].isin(st.session_state.subcategory_filter)]
    if st.session_state.location_filter:
        selected = set(st.session_state.location_filter)
        filtered = filtered[
            filtered["location_tokens"].apply(lambda tokens: bool(selected & set(tokens)))
        ]
    if st.session_state.stakeholder_filter:
        selected = set(st.session_state.stakeholder_filter)
        filtered = filtered[
            filtered["stakeholder_tokens"].apply(lambda tokens: bool(selected & set(tokens)))
        ]
    return filtered

# --- Sidebar options logic ---
filtered_for_options = filter_df()

category_options = sorted(filtered_for_options["Category"].dropna().unique())
st.session_state.category_filter = [c for c in st.session_state.category_filter if c in category_options]

subcategory_options = sorted(filtered_for_options["Sub-Category"].dropna().unique())
st.session_state.subcategory_filter = [
    sc for sc in st.session_state.subcategory_filter if sc in subcategory_options
]

location_options = sorted({loc for tokens in filtered_for_options["location_tokens"] for loc in tokens})
st.session_state.location_filter = [
    l for l in st.session_state.location_filter if l in location_options
]

stakeholder_options = sorted({s for tokens in filtered_for_options["stakeholder_tokens"] for s in tokens})
st.session_state.stakeholder_filter = [
    s for s in st.session_state.stakeholder_filter if s in stakeholder_options
]

# --- Sidebar widgets ---
st.sidebar.multiselect("Category", options=category_options, key="category_filter")
st.sidebar.multiselect("Subcategory", options=subcategory_options, key="subcategory_filter")
st.sidebar.multiselect("Location Identified", options=location_options, key="location_filter")
st.sidebar.multiselect("Contributor/Owner Category", options=stakeholder_options, key="stakeholder_filter")

# --- Final filtered dataframe ---
filtered = filter_df()

tab1, tab2 = st.tabs(["Dashboard View", "Initiatives View"])

# -------------------- DASHBOARD VIEW --------------------
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

# -------------------- INITIATIVES VIEW --------------------
with tab2:
    st.header("Initiatives Overview")
    st.write("---")

    if filtered.empty:
        st.write("No initiatives match your filters.")
    else:
        if no_filters_applied():
            # 🔑 Reuse already-rendered baseline HTML
            html_table = st.session_state.base_initiatives_html
        else:
            display_cols = ["ID", "Initiative", "Category", "Location Identified"]
            html_table = render_initiatives_html(filtered[display_cols])

        st.markdown(html_table, unsafe_allow_html=True)

        st.markdown(
            """
            <style>
            #custom_table th:nth-child(1), #custom_table td:nth-child(1) { width: 70px; }
            #custom_table th:nth-child(2), #custom_table td:nth-child(2) { width: 450px; }
            #custom_table th:nth-child(3), #custom_table td:nth-child(3) { width: 175px; }
            #custom_table th:nth-child(4), #custom_table td:nth-child(4) { width: 175px; }

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
