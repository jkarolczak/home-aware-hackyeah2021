import sys
sys.path.append('.')
import streamlit as st
import pandas as pd

sess = st.session_state

def main():
	if 'variants' not in sess:
		sess.variants = []

	st.title('Wizard')

	st.header("I'm interested in...")

	st.subheader('New appartment')
	with st.form(key='new-loc'):
		city = st.text_input('City', value='Łódź')
		street = st.text_input('Street')
		building_no = st.text_input('Building No.')
		new_variant = st.form_submit_button('Add appartment')

	if new_variant:
		sess.variants.append(dict(city=city, street=street, building_no=building_no))

	st.subheader('Variants')
	st.dataframe(pd.DataFrame(sess.variants))

	st.header('I like...')

	profile = st.selectbox("I'm a...", ['Student', 'Family', 'Pensioner'])
	pref_safety = st.slider('Safety', min_value=1, max_value=5, value=3)
	pref_cost = st.slider('Cost', min_value=1, max_value=5, value=3)
	pref_local = st.slider('Localization', min_value=1, max_value=5, value=3)
	pref_transp = st.slider('Transport', min_value=1, max_value=5, value=3)

	st.header('Some analysis')
	st.write('Hello, world!')

if __name__ == '__main__':
	main()
