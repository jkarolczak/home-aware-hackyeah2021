import re
import sys

sys.path.append(".")
import streamlit as st
import pandas as pd
import numpy as np
import graphviz as graphviz
import seaborn as sns
import matplotlib.pyplot as plt

from src.req import criterions
from src.model import partial_utilities, global_utility

plt.style.use('ggplot')

sess = st.session_state

app_name = "HomeFinder"

demo_variants = [
    {'City': 'Łódź', 'Street': 'ALEKSANDROWSKA', 'Building No.': '104', 'Postal Code': '91224'},
]

def read_profiles():
    df = pd.read_csv('src/presets.csv', index_col='function')
    return {col_name: df[col_name].to_dict() for col_name in df.columns}

# profile name -> default preferences
profiles = read_profiles()

coarse_criteria = [
    "Safety",
    "Education",
    "Nature",
    "Transport",
    "Services",
    "Comfort",
    "Community",
    "Extraversion",
]

hidden_criteria = {
    "Safety": ["Number of car collisions with pedestrians"],
    "Education": ["Universities nearby", "Schools nearby"],
    "Nature": ["Amount of green spaces"],
    "Transport": [
        "Number of garages",
        "Tram stop nearby",
        "Bus stop nearby",
        "Railway station nearby",
    ],
    "Services": [
        "Post office nearby",
        "Mall nearby",
        "Culture entertainment nearby",
        "Health services nearby",
    ],
    "Comfort": [
        "Parcel lockers",
        "Distance to civil services",
        "Distance to railway tracks",
        "Distance to freeways",
    ],
    "Community": [
        "Amount of people playing sports",
        "Amout of older people",
        "Places of worship nearby",
    ],
    "Extraversion": ["Amount of dating apps users", "Amount of young adults"],
}


@st.experimental_memo
def variant_details(x):
    return criterions(city=x['City'], street=x['Street'], buildingNumber=int(x['Building No.']), code=int(x['Postal Code']))


def format_variant(x):
    return f"{x['Street']} {x['Building No.']}, {x['City']}"


def page_variants():
    st.markdown("# 🏘️ Locations")
    st.markdown("Please add addresses for a few interesting locations.")
    st.markdown("## New location")
    with st.form("new-location", clear_on_submit=True):
        cols = st.columns(4)
        city = cols[0].text_input("City", value="Łódź")
        street = cols[1].text_input("Street")
        building_no = cols[2].text_input("Building No.")
        postcode = re.sub("[^0-9]", "", cols[3].text_input("Postcode"))
        new_variant = st.form_submit_button("Add")

    if new_variant:
        sess.variants.append(
            {
                "City": city,
                "Street": street,
                "Building No.": building_no,
                "Postcode": postcode,
            }
        )

    st.markdown("## My locations")
    st.table(pd.DataFrame(sess.variants))

    st.markdown("## Remove location")

    coords = np.random.randn(20, 2) / 20 + [51.75, 19.45]
    st.map(pd.DataFrame(coords, columns=["lat", "lon"]))

    st.markdown('## New location')
    with st.form('new-location', clear_on_submit=False):
        cols = st.columns(4)
        city = cols[0].text_input('City', value='Łódź')
        street = cols[1].text_input('Street')
        building_no = cols[2].text_input('Building No.')
        postal_code = re.sub('[^0-9]', '', cols[3].text_input('Postal Code'))
        new_variant = st.form_submit_button('Add')

    if new_variant:
        if not city:
            st.error('City must be non-empty')
        elif not street:
            st.error('Street must be non-empty')
        elif not (building_no and building_no.isnumeric()):
            st.error('Building No. must be a number')
        elif postal_code:
            st.error('Postal Code must be non-empty')
        else:
            sess.variants.append({'City': city, 'Street': street, 'Building No.': building_no, 'Postal Code': postal_code})

    if sess.variants:
        st.markdown('## My locations')
        st.table(pd.DataFrame(sess.variants))

        coords = []
        for variant in sess.variants:
            details = variant_details(variant)
            lat, lon = details['latlon']
            coords.append(dict(lat=lat, lon=lon))
        st.map(pd.DataFrame(coords))

    if sess.show_variant_details:
        st.markdown('## Location details')
        for variant in sess.variants:
            st.write(variant_details(variant))

def page_profile():
    st.markdown("# 🧑 User Profile")

    sess.profile = st.selectbox("I'm best described as...", profiles.keys())

    n_cols = 3
    cols = st.columns(n_cols)
    for i, name in enumerate(coarse_criteria):
        cols[i % n_cols].slider(name, min_value=1, max_value=10, value=5)

    with st.expander("See advanced options"):
        option = st.selectbox(label='Choose category', options=coarse_criteria)
        if option:
            st.write("How important for you is:")
            for name in hidden_criteria[option]:
                st.number_input(name, min_value=1, max_value=10, value=5)


def page_analysis():
    st.markdown("# 🧑‍🔬 Analysis")


def page_preferences():
    st.markdown("# 🤔 Preferences")
    st.markdown(
        f"If given two choices, which one do you prefer? {app_name} will learn from your preferences and adjust your profile _a bit_."
    )

    with st.form("new-preference"):
        better = st.selectbox("Location 1", sess.variants, format_func=format_variant)
        st.markdown("**is better than**")
        worse = st.selectbox("Location 2", sess.variants, format_func=format_variant)
        new_pref = st.form_submit_button("Add")

    if new_pref and better != worse:
        if (format_variant(worse), format_variant(better)) in sess.preferences:
            sess.preferences.remove((format_variant(worse), format_variant(better)))
            st.warning(
                "Be careful! You've already compared those two options and your choice has changed."
            )
        sess.preferences.append((format_variant(better), format_variant(worse)))
    elif new_pref and better == worse:
        st.error(
            "You are trying to compare a house with itself! Find it a different opponent."
        )

    if sess.preferences:
        st.markdown("## Preference graph")
        g = graphviz.Digraph()
        for better, worse in sess.preferences:
            g.edge(better, worse)
        st.graphviz_chart(g, use_container_width=True)


def page_analysis():
    st.markdown('# 🧑‍🔬 Analysis')

    pref = profiles[sess.profile]
        
    st.subheader('Profile')
    st.write(pref)

    for variant in sess.variants:
        details = variant_details(variant)
        st.write(variant)

        util = partial_utilities(pref, details)
        score = global_utility(pref, details)

        fig, ax = plt.subplots()
        df = pd.DataFrame()
        df['Criterion'] = list(pref.keys())
        df['Utility'] = [pref[k]*util[k] for k in pref]
        df = df.sort_values(by='Utility', ascending=False)

        sns.barplot(y='Criterion', x='Utility', data=df, ax=ax)
        ax.set_ylabel('Criterion'); ax.set_xlabel('Utility')
        st.pyplot(fig)

        st.subheader(f'HomeScore: {score:.4f}')

        st.write(details)
        st.markdown('---')

def page_tuning():
    st.markdown("# 🔧 Fine-tuning")


def main():
    # initialize state
    if "variants" not in sess:
        sess.variants = []
    if 'preferences' not in sess:
        sess.preferences = []
    
    sess.profile = 'Student'

    st.set_page_config(
        page_title="Rośliniary App",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.sidebar.markdown(f"# {app_name} 🌟")

    pages = {
        '1️. Locations': page_variants,
        '2. User Profile': page_profile,
        '3. Preferences (optional)': page_preferences,
        '4. Analysis': page_analysis,
        #'5. Fine-tuning': page_tuning,
    }
    name = st.sidebar.radio('Select step', pages.keys(), index=3)

    st.sidebar.write('Demo controls')
    demo = st.sidebar.checkbox('Show demo locations', value=True)
    sess.show_variant_details = st.sidebar.checkbox('Show location details', value=False)

    if demo:
        sess.variants = demo_variants
    else:
        sess.variants = []

    # st.sidebar.info('Rośliniary Team :)')
    pages[name]()


if __name__ == "__main__":
    main()
