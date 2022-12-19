import streamlit as st
from bs4 import BeautifulSoup as bs
from time import time
from tools import Redactor, viewer, authenticator

st.set_page_config(page_title="changer", layout="wide")

if __name__ == '__main__':
    if True:
    # if 'authentication_status' not in st.session_state:
    #     st.session_state['authentication_status'] = None

    # name, authentication_status, _ = authenticator.login('Login', 'main')
    # if authentication_status == False:
    #     st.error('Username/password is incorrect')
    # elif authentication_status is None:
    #     st.warning('Please enter your username and password')
    # elif authentication_status:
    #     st.write('Welcome *%s*' % (name))
        st.title('XML redactor')
        st.write('')

        xml_file = st.file_uploader('Choise file', accept_multiple_files=False)

        if xml_file:
            redactor = Redactor(xml_file)
            save_file = redactor.loader()


            view, change = st.columns(2)

            with view:
                st.header('Viewer')
                viewer(redactor.get_content().encode('utf-8'), save_file)

            with change:
                st.header('Redactor')
                title = st.selectbox('Choice title', redactor.get_titles())


                tables, subtitle_content = redactor.select_title(title)

                if subtitle_content:

                    if tables:
                        placeholder = st.empty()

                        max_height, max_width = redactor.parce_table(subtitle_content)
                        i = st.number_input('X', min_value=0, max_value=max_height + 1, value=0, step=1)

                        with placeholder.form(key='update table xml', clear_on_submit=True):
                            redactor.get_form(i, max_width)
                            st.form_submit_button(label='update', on_click=redactor.change_cell(i, max_height, max_width))



                    else:
                        placeholder = st.empty()
                        with st.form(key='Update text', clear_on_submit=True):
                            rewrite = redactor.get_form(1, 2)
                            st.form_submit_button(label='Update', on_click=redactor.change_text())

            redactor.reload_changes()

            new_name = st.text_input('name file without ".xml"')
            if st.button('save file'):
                new_path = redactor.save_changes(new_name)
                redactor.download_changes(new_path, new_name)
                st.write('Done!')


