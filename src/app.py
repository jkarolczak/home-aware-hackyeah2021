import re
import sys
sys.path.append('.')
import streamlit as st
import pandas as pd
import numpy as np
import graphviz as graphviz

from src.req import criterions

sess = st.session_state

app_name = 'HomeFinder'

demo_variants = [
    {'City': 'Łódź', 'Street': 'ALEKSANDROWSKA', 'Building No.': '104', 'Postal Code': '91224'},
]

# profile name -> default preferences
profiles = {
    'Student': [],
    'Couple': [],
    'Family with children': [],
    'Working adult': [],
    'Pensioner': [],
}

coarse_criteria = {
	'basic': ['Education', 'Nature', 'Services', 'Community', 'Extraversion'],
	'advanced': ['Safety', 'Comfort', 'Transport', 'Amenities']
}


def variant_details(x):
    return criterions(city=x['City'], street=x['Street'], buildingNumber=int(x['Building No.']), code=int(x['Postal Code']))


def format_variant(x):
    return f"{x['Street']} {x['Building No.']}, {x['City']}"


def page_variants():
    st.markdown('# 🏘️ Locations')
    st.markdown('Please add addresses for a few interesting locations.')

    st.markdown('## New location')
    with st.form('new-location', clear_on_submit=True):
        cols = st.columns(4)
        city = cols[0].text_input('City', value='Łódź')
        street = cols[1].text_input('Street')
        building_no = cols[2].text_input('Building No.')
        postal_code = re.sub('[^0-9]', '', cols[3].text_input('Postal Code'))
        new_variant = st.form_submit_button('Add')

    if new_variant:
        sess.variants.append({'City': city, 'Street': street, 'Building No.': building_no, 'Postal Code': postal_code})

    st.markdown('## My locations')
    st.table(pd.DataFrame(sess.variants))

    coords = np.random.randn(20, 2)/20 + [51.75, 19.45]
    st.map(pd.DataFrame(coords, columns=['lat', 'lon']))

    if sess.show_variant_details:
        st.markdown('## Location details')
        for variant in sess.variants:
            st.write(variant_details(variant))

def page_profile():
    st.markdown('# 🧑 User Profile')

    profile = st.selectbox("I'm best described as...", profiles.keys())

    n_cols = 3
    cols = st.columns(n_cols)
    for i, name in enumerate(coarse_criteria['basic']):
    	cols[i % n_cols].slider(name, min_value=1, max_value=10, value=5)
	
    with st.expander("See advanced options"):
        st.write('Choose your priorities')
        for name in coarse_criteria['advanced']:
            st.checkbox(name)

def page_analysis():
    st.markdown('# 🧑‍🔬 Analysis')

def page_preferences():
    st.markdown('# 🤔 Preferences')
    st.markdown(f'If given two choices, which one do you prefer? {app_name} will learn from your preferences and adjust your profile _a bit_.')

    with st.form('new-preference'):
        better = st.selectbox('Location 1', sess.variants, format_func=format_variant)
        st.markdown('**is better than**')
        worse = st.selectbox('Location 2', sess.variants, format_func=format_variant)
        new_pref = st.form_submit_button('Add')

    if new_pref and better != worse:
        if (format_variant(worse), format_variant(better)) in sess.preferences:
            sess.preferences.remove((format_variant(worse), format_variant(better)))
            st.warning('Be careful! You\'ve already compared those two options and your choice has changed.')
        sess.preferences.append((format_variant(better), format_variant(worse)))


    if sess.preferences:
        st.markdown('## Preference graph')
        g = graphviz.Digraph()
        for better, worse in sess.preferences:
            g.edge(better, worse)
        st.graphviz_chart(g, use_container_width=True)

def page_tuning():
    st.markdown('# 🔧 Fine-tuning')

def main():
    # initialize state
    if 'variants' not in sess:
        sess.variants = []
        sess.preferences = []

    st.set_page_config(page_title='Rośliniary App', page_icon='🌱',
        layout='wide', initial_sidebar_state='expanded')
    st.sidebar.markdown(f'# {app_name} 🌟')

    pages = {
        '1️. Locations': page_variants,
        '2. User Profile': page_profile,
        '3. Preferences (optional)': page_preferences,
        '4. Analysis': page_analysis,
        '5. Fine-tuning': page_tuning,
    }
    name = st.sidebar.radio('Select step', pages.keys())

    st.sidebar.write('Demo controls')
    demo = st.sidebar.checkbox('Show demo locations', value=True)
    sess.show_variant_details = st.sidebar.checkbox('Show location details', value=False)

    if demo:
        sess.variants = demo_variants
    else:
        sess.variants = []

    #st.sidebar.info('Rośliniary Team :)')
    pages[name]()
    #page_tuning()
    #page_preferences()


if __name__ == '__main__':
    main()
