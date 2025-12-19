import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# ---------------- Sidebar Styling ----------------
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { width: 350px; }
    [data-baseweb="select"] { min-width: 300px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- Load Data (CACHED) ----------------
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_excel("2025-12-12 Updated Summary Sheet.xlsx", sheet_name="Sheet1")
    df = df.rename(columns={"Updated Initiative": "Initiative"})
    return df

# ---------------- Preprocess (CACHED) ----------------
@st.cache_data(show_spinner=False)
def preprocess_df(df):
    df = df.copy()

    # -------- Tokenization --------
    df["location_tokens"] = df["Location Identified"].apply(
        lambda cell: [p.strip() for p in str(cell).split(",") if p.strip()]
    )

    df["stakeholder_tokens"] = df["Filtering-Contributors-Categories"].apply(
        lambda cell: [p.strip() for p in str(cell).split(",") if p.strip()]
    )

    # -------- Timeline parsing --------
    def parse_timeline(val):
        try:
            val = str(val).strip()
            if "-" in val:
                start, end = val.split("-")
                return int(start), int(end)
            year = int(val)
            return year, year
        except:
            return None, None

    df[["timeline_start", "timeline_end"]] = df["Expected Timeline"].apply(
        lambda x: pd.Series(parse_timeline(x))
    )

    # -------- Image check --------
    df["has_image"] = df["ID"].apply(lambda x: os.path.exists(f"assets/{x}.png"))

    return df[df["has_image"]]

df = preprocess_df(load_data())

st.title("Atlantic Housing Innovation Strategy")

# ---------------- Session State ----------------
FILTER_KEYS = [
    "category_filter",
    "subcategory_filter",
    "location_filter",
    "stakeholder_filter",
    "timeline_filter",
]

for key in FILTER_KEYS:
    st.session_state.setdefault(key, [])

# ---------------- Sidebar ----------------
st.sidebar.header("Filters")

def reset_filters():
    for k in FILTER_KEYS:
        st.session_state[k] = []

st.sidebar.button("Reset Filters", on_click=reset_filters)

# ---------------- Helpers ----------------
def no_filters_applied():
    return all(not st.session_state[k] for k in FILTER_KEYS)

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

    # -------- Timeline year filter --------
    if st.session_state.timeline_filter:
        selected_years = set(st.session_state.timeline_filter)
        filtered = filtered[
            filtered.apply(
                lambda row: any(
                    row["timeline_start"] <= y <= row["timeline_end"]
                    for y in selected_years
                    if pd.notna(row["timeline_start"]) and pd.notna(row["timeline_end"])
                ),
                axis=1
            )
        ]

    return filtered

# ---------------- Filter Options (CASCADING) ----------------
filtered_for_options = filter_df()

category_options = sorted(filtered_for_options["Category"].dropna().unique())
subcategory_options = sorted(filtered_for_options["Sub-Category"].dropna().unique())
location_options = sorted({l for tokens in filtered_for_options["location_tokens"] for l in tokens})
stakeholder_options = sorted({s for tokens in filtered_for_options["stakeholder_tokens"] for s in tokens})

# -------- Dynamic timeline options --------
def get_valid_timeline_years(df):
    years = set()
    for start, end in zip(df["timeline_start"], df["timeline_end"]):
        if pd.notna(start) and pd.notna(end):
            years.update(range(int(start), int(end) + 1))
    return sorted(years)

timeline_options = get_valid_timeline_years(filtered_for_options)

# -------- Prune invalid selections --------
st.session_state.category_filter = [v for v in st.session_state.category_filter if v in category_options]
st.session_state.subcategory_filter = [v for v in st.session_state.subcategory_filter if v in subcategory_options]
st.session_state.location_filter = [v for v in st.session_state.location_filter if v in location_options]
st.session_state.stakeholder_filter = [v for v in st.session_state.stakeholder_filter if v in stakeholder_options]
st.session_state.timeline_filter = [v for v in st.session_state.timeline_filter if v in timeline_options]

# ---------------- Sidebar Widgets ----------------
st.sidebar.multiselect("Category", category_options, key="category_filter")
st.sidebar.multiselect("Subcategory", subcategory_options, key="subcategory_filter")
st.sidebar.multiselect("Expected Timeline (Year)", timeline_options, key="timeline_filter")
st.sidebar.multiselect("Location Identified", location_options, key="location_filter")
st.sidebar.multiselect("Contributor / Owner Category", stakeholder_options, key="stakeholder_filter")

# ---------------- Final Filtered DF ----------------
filtered = filter_df()

# ---------------- Tabs ----------------
tab1, tab2 = st.tabs(
    ["Dashboard View", "Initiatives View"]
)

# ---------------- Dashboard View ----------------
with tab1:
    st.header("Dashboards")
    st.write("---")

    if filtered.empty:
        st.write("No images match your filters.")
    else:
        for img_id in filtered["ID"]:
            st.image(f"assets/{img_id}.png", width=1200)

# ---------------- Initiatives View ----------------
with tab2:
    st.header("Initiatives Overview")
    st.write("---")

    if filtered.empty:
        st.write("No initiatives match your filters.")
    else:
        cols = ["ID", "Initiative", "Category", "Location Identified", "Expected Timeline"]
        subset = filtered[cols].copy()
        subset["Initiative"] = subset["Initiative"].str.replace("\n", "<br>")

        st.markdown(
            subset.to_html(index=False, escape=False),
            unsafe_allow_html=True
        )

