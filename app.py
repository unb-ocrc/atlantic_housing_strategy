import streamlit as st
import pandas as pd
import os



st.set_page_config(layout="wide")  

#sidebar
st.markdown(
    """
    <style>
    /* Make the sidebar wider */
    [data-testid="stSidebar"] {
        width: 350px;
    }
    /* Make multiselect dropdowns wider inside the sidebar */
    [data-baseweb="select"] {
        min-width: 300px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#load data
df = pd.read_excel("2025-12-12 Updated Summary Sheet.xlsx", sheet_name="Sheet1")

def extract_tokens(cell):
    if pd.isna(cell):
        return []
    return [part.strip() for part in str(cell).split(",") if part.strip() != ""]

# Only consider rows with existing images
df = df[df["ID"].apply(lambda x: os.path.exists(f"assets/{x}.png"))].copy()

st.title("Atlantic Housing Innovation Strategy")

# Session State Initialization
for key in ["category_filter", "subcategory_filter", "location_filter", "stakeholder_filter"]:
    if key not in st.session_state:
        st.session_state[key] = []


st.sidebar.header("Filters")

def reset_filters():
    st.session_state.category_filter = []
    st.session_state.subcategory_filter = []
    st.session_state.location_filter = []
    st.session_state.stakeholder_filter = []

st.sidebar.button("Reset Filters", on_click=reset_filters)

#filter logic
def filter_df():
    filtered = df.copy()
    if st.session_state.category_filter:
        filtered = filtered[filtered["Category"].isin(st.session_state.category_filter)]
    if st.session_state.subcategory_filter:
        filtered = filtered[filtered["Sub-Category"].isin(st.session_state.subcategory_filter)]
    if st.session_state.location_filter:
        filtered = filtered[
            filtered["Location Identified"].apply(
                lambda cell: any(loc in extract_tokens(cell) for loc in st.session_state.location_filter)
            )
        ]
    if st.session_state.stakeholder_filter:
        filtered = filtered[
            filtered["Filtering-Contributors-Categories"].apply(
                lambda cell: any(s in extract_tokens(cell) for s in st.session_state.stakeholder_filter)
            )
        ]
    return filtered

# find options
filtered_for_options = filter_df()

category_options = sorted(filtered_for_options["Category"].dropna().unique())
st.session_state.category_filter = [c for c in st.session_state.category_filter if c in category_options]

subcategory_options = sorted(filtered_for_options["Sub-Category"].dropna().unique())
st.session_state.subcategory_filter = [sc for sc in st.session_state.subcategory_filter if sc in subcategory_options]

location_options = sorted({loc for cell in filtered_for_options["Location Identified"] for loc in extract_tokens(cell)})
st.session_state.location_filter = [l for l in st.session_state.location_filter if l in location_options]

stakeholder_options = sorted({s for cell in filtered_for_options["Filtering-Contributors-Categories"] for s in extract_tokens(cell)})
st.session_state.stakeholder_filter = [s for s in st.session_state.stakeholder_filter if s in stakeholder_options]

# multiselect
category_filter = st.sidebar.multiselect("Category", options=category_options, key="category_filter")
subcategory_filter = st.sidebar.multiselect("Subcategory", options=subcategory_options, key="subcategory_filter")
location_filter = st.sidebar.multiselect("Location Identified", options=location_options, key="location_filter")
stakeholder_filter = st.sidebar.multiselect("Contributor/Owner Category", options=stakeholder_options, key="stakeholder_filter")

# filter for display
filtered = filter_df()

tab1, tab2 = st.tabs(["Dashboard View", "Initiatives View"])

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


with tab2:
    st.header("Initiatives Overview")
    st.write("---")
    
    if filtered.empty:
        st.write("No initiatives match your filters.")
    else:
        display_cols = ["ID", "Updated Initiative", "Category", "Location Identified"]
        filtered_subset = filtered[display_cols].copy()

        #  newline characters with <br> for HTML line breaks
        filtered_subset["Updated Initiative"] = filtered_subset["Updated Initiative"].str.replace("\n", "<br>")

        # convert df to html
        st.markdown(
            filtered_subset.to_html(index=False, table_id="custom_table", escape=False), 
            unsafe_allow_html=True
        )
        
        # control column widths and allow text wrapping
        st.markdown("""
        <style>
        /* Adjust column widths */
        #custom_table th:nth-child(1), #custom_table td:nth-child(1) { width: 70px; }     /* ID */
        #custom_table th:nth-child(2), #custom_table td:nth-child(2) { width: 450px; }    /* Initiative (wider) */
        #custom_table th:nth-child(3), #custom_table td:nth-child(3) { width: 175px; }    /* Category (narrower) */
        #custom_table th:nth-child(4), #custom_table td:nth-child(4) { width: 175px; }    /* Location Identified (narrower) */

        /* Table styling */
        #custom_table {
            border-collapse: collapse;
            width: 100%;
        }
        #custom_table th, #custom_table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            word-wrap: break-word;   /* allow text wrapping */
            word-break: break-word;  /* break long words if necessary */
        }
        #custom_table th {
            background-color: #f2f2f2;
        }
        </style>
        """, unsafe_allow_html=True)
