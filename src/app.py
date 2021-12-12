import re
import sys

sys.path.append(".")
import streamlit as st
import pandas as pd
import numpy as np
import graphviz as graphviz
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

from src.req import criterions
from src.model import partial_utilities, global_utility, default_thresholds

plt.style.use('ggplot')

sess = st.session_state

app_name = "__homeAware__"

coarse_criteria = {
    'Education': [ 'education', 'university' ],
    'Safety': ['car_collisions', 'consumer_expenses', 'cr3', 'crimes', 'geoscore'],
    'Transport': ['garages', 'tram_stop', 'bus_stop', 'railway_station'],
    'Services': ['parcel_lockers', 'post_office', 'health', 'culture_entertainment', 'mall'],
    'Extraversion': ['between_20_30', 'dating_apps'],
    'Community': ['over_60', 'sport', 'worship'],
    'Nature': ['nature'],
    'Comfort': ['airport', 'civil_services', 'railway_tracks', 'freeways'],       
}

coarse_criteria_profiles = pd.read_csv('src/presets_coarse.csv', index_col='name').to_dict()

demo_variants = [
    {'City': 'Łódź', 'Street': 'ALEKSANDROWSKA', 'Building No.': '104', 'Postal Code': '91224'},
    {'City': 'Łódź', 'Street': 'LEGIONÓW', 'Building No.': '32', 'Postal Code': '90001'},
    {'City': 'Łódź', 'Street': 'ROMANOWSKA', 'Building No.': '55', 'Postal Code': '91174'},
    {'City': 'Łódź', 'Street': 'PŁOCKA', 'Building No.': '10', 'Postal Code': '90001'},
    #{'City': 'Łódź', 'Street': 'WYŻSZA', 'Building No.': '25', 'Postal Code': '93266'},
    #{'City': 'Łódź', 'Street': 'TATRZAŃSKA', 'Building No.': '28', 'Postal Code': '93115'},
]

def read_profiles():
    df = pd.read_csv('src/presets.csv', index_col='function')
    return {col_name: df[col_name].to_dict() for col_name in df.columns}

# profile name -> default preferences
profiles = read_profiles()

hidden_criteria = {
    "Education": [
        ("university", "Universities are at most this far away (km)"),
        ("education", "Primary or high schools are at most this far away (km)"),
    ],
    "Safety": [
        ("car_collisions", "Number of car collisions with pedestrians is lower than"),
    ],
    "Nature": [
        ("nature", "Nearby areas are composed of at least this much green spaces (%)"),
    ],
    "Transport": [
        ("garages", "Number of garages is at least"),
        ("tram_stop", "Tram stop is at most this far away (km)"),
        ("bus_stop", "Bus stop is at most this far away (km)"),
        ("railway_station", "Railway station is at most this far away (km)"),
    ],
    "Services": [
        ("post_office", "Post office is at most this far away (km)"),
        ("mall", "Shopping mall is at most this far away (km)"),
        ("culture_entertainment", "Culture and entertainment is at most this far away (km)"),
        ("health", "Health services is at most this far away (km)"),
    ],
    "Comfort": [
        ("parcel_lockers", "Parcel locker is at most this far away (km)"),
        ("civil_services", "Distance to civil services is more than (km) (affects noise levels)"),
        ("railway_tracks", "Distance to railway tracks is more than (km) (affects noise levels)"),
        ("freeways", "Distance to freeways is more than (km) (affects noise levels)"),
    ],
    "Community": [
        ("sport", "Number of people playing sports is at least"),
        ("over_60", "Number of older people is at least"),
        ("worship", "Place of worship is at most this far away (km)"),
    ],
    "Extraversion": [
        ("dating_apps", "Number of dating apps users is at least (%)"),
        ("between_20_30", "Number of young adults is at least")
    ],
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
        if not city:
            st.error('City must be non-empty')
        elif not street:
            st.error('Street must be non-empty')
        elif not (building_no and building_no.isnumeric()):
            st.error('Building No. must be a number')
        elif not postcode:
            st.error('Postal Code must be non-empty')
        else:
            sess.variants.append({'City': city, 'Street': street, 'Building No.': building_no, 'Postal Code': postcode})

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
    st.markdown("# 🎭 User Profile")

    new_profile = st.selectbox("I'm best described as...", profiles.keys(), index=list(profiles.keys()).index(sess.profile))
    if new_profile != sess.profile:
        sess.weights = coarse_criteria_profiles[sess.profile]
    sess.profile = new_profile

    st.markdown('### My values')
    n_cols = 4
    cols = st.columns(n_cols)
    for i, (name, value) in enumerate(sess.weights.items()):
        sess.weights[name] = cols[i % n_cols].slider(name, min_value=0, max_value=100, step=10, value=int(value*100), format='%d%%') / 100

    with st.expander("See advanced options"):
        option = st.selectbox(label='Choose category', options=coarse_criteria)
        if option:
            st.write("I would like the following to be true:")
            for name, description in hidden_criteria[option]:
                sess.thresholds[name] = st.number_input(description, value=sess.thresholds[name])


def page_preferences():
    st.markdown("# 🤔 Preferences (optional)")
    st.markdown(f"If given two choices, which one do you prefer? {app_name} will learn from your preferences and adjust your profile _a bit_.")
    st.markdown("You can skip this step if you _really_ don't have any preferences.")
    col1, col2 = st.columns([1, 2])

    col1.markdown('### New preference')
    with col1.form('new-preference'):
        better = st.selectbox('Location 1', sess.variants, format_func=format_variant)
        st.markdown('**is better than**')
        worse = st.selectbox('Location 2', sess.variants, format_func=format_variant)
        new_pref = st.form_submit_button('Add')

    if new_pref:
        a, b = format_variant(better), format_variant(worse)
        if better == worse:
            st.error('You are trying to compare a house with itself! Find it a different opponent.')
        else:
            if (b, a) in sess.preferences:
                sess.preferences.remove((b, a))
                st.warning("Be careful! You've already compared those two options and your choice has changed.")
            sess.preferences.append((a, b))

    if sess.preferences:
        col2.markdown('### Preference graph')
        g = graphviz.Digraph(node_attr=dict(shape='box', style='rounded'))
        for better, worse in sess.preferences:
            g.edge(better, worse)
        col2.graphviz_chart(g, use_container_width=True)

    st.markdown('### Profile adjustment')
    st.markdown('Your profile was adjusted based on your preferences')
    coarse_profile = coarse_criteria_profiles[sess.profile]
    n = len(coarse_profile)
    n_cols = 4
    cols = st.columns(n_cols)
    for i, (group, weight) in enumerate(coarse_profile.items()):
        delta = np.random.randint(-10, 10)
        weight = max(0, min(100, weight * 100 + delta))
        cols[i % n_cols].metric(group, f'{weight}%', delta=f'{delta}%')
            


def page_analysis():
    st.markdown('# 🧑‍🔬 Analysis')

    pref = profiles[sess.profile]

    st.markdown('## Final ranking')

    weights_norm = sum(sess.weights.values())
    results = []
    for i, variant in enumerate(sess.variants):
        details = variant_details(variant)
        fine_u = partial_utilities(sess.thresholds, details)
        coarse_u = {}
        for coarse, fine_criteria in coarse_criteria.items():
            coarse_u[coarse] = sess.weights[coarse] / weights_norm * np.mean([fine_u[fine] for fine in fine_criteria])

        score = np.sum(list(coarse_u.values()))
        variant['MatchScore'] = score
        results.append(dict(score=score, coarse=coarse_u, fine=fine_u, variant=variant, details=details))

    ranking = sorted(results, key=lambda x: x['score'], reverse=True)
    ranking_df = pd.DataFrame([x['variant'] for x in ranking])
    ranking_df['Rank'] = np.arange(len(ranking)) + 1

    st.table(ranking_df)

    st.markdown('## Comparison')

    is_raw = st.checkbox('Show raw values')

    locations = [format_variant(x['variant']) for x in results]
    df = pd.DataFrame([x['coarse'] for x in ranking]).T
    df.columns = locations
    df = df.T

    Q = df.quantile([0.25, 0.75])
    df_str = df.astype(str)
    df_str[df < Q.iloc[0, :]] = '🔴️'
    df_str[df > Q.iloc[1, :]] = '🟢'
    df_str[(Q.iloc[0, :] <= df) & (df <= Q.iloc[1, :])] = '🟡'

    st.table(df if is_raw else df_str)

    st.markdown('## Explanation')
    result = st.selectbox('Location to analyze', results, format_func=lambda x: format_variant(x['variant']))
    if result is None: return

    fig = go.Figure(go.Waterfall(
        y=list(result['coarse'].keys()),
        x=list(result['coarse'].values()),
        orientation='h',
        connector=dict(line=dict(width=1, color='#333', dash='solid')),
    ))
    fig.update_layout(title='Influence of each criterion')
    fig.update_xaxes(range=[0, 1])
    st.plotly_chart(fig, use_container_width=True)
    
    if sess.show_variant_details:
        st.markdown('### Location details')
        st.write(result['fine'])


def main():
    # initialize state
    if 'variants' not in sess:
        sess.variants = []
    if 'preferences' not in sess:
        sess.preferences = []
    if 'thresholds' not in sess:
        sess.thresholds = default_thresholds 
    if 'profile' not in sess:
        sess.profile = 'Student'
    if 'weights' not in sess:
        sess.weights = coarse_criteria_profiles[sess.profile]

    st.set_page_config(
        page_title="homeAware",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.sidebar.markdown(f"# {app_name} 💡")

    pages = {
        '1️. Locations': page_variants,
        '2. User Profile': page_profile,
        '3. Analysis': page_analysis,
    }
    name = st.sidebar.radio('Select step', pages.keys(), index=0)

    st.sidebar.write('Demo controls')
    demo = st.sidebar.checkbox('Show demo locations', value=True)
    sess.show_variant_details = st.sidebar.checkbox('Show location details', value=False)

    if demo:
        sess.variants = demo_variants
    else:
        sess.variants = []

    pages[name]()
    # st.sidebar.info('Rośliniary Team :)')


if __name__ == "__main__":
    main()
