import streamlit as st
import lxml
from lxml import etree
import os
from bs4 import BeautifulSoup as bs
import pandas as pd


def init_state(upload_file):
    if 'store' not in st.session_state:
        store = os.path.abspath('store')
        if not os.path.exists(store):
            os.mkdir(store)
        st.session_state.store = store
    if 'parse_xml' not in st.session_state:
        st.session_state.parse_xml = upload_file
        st.session_state.parse_xml_update = 0
        st.session_state.parse_xml_string = None

    print(st.session_state)


def update_state(update_parse):
    xml_name = st.session_state.parse_xml.split('/')[-1]
    print(xml_name)
    xml_name, xml_type = xml_name.split('.')
    print(xml_name, xml_type)
    if os.path.exists(st.session_state.parse_xml):
        st.session_state.parse_xml_update += 1
        if st.session_state.parse_xml_update == 0:
            new_xml = os.path.join(st.session_state.store, f'{xml_name}_1')
        else:
            xml_name = st.session_state.parse_xml.replace(f'_{st.session_state.parse_xml_update-1}', f'_{st.session_state.parse_xml_update}')
            new_xml = os.path.join(st.session_state.store, f'{xml_name}')
        st.session_state.parse_xml = new_xml
        print(st.session_state.parse_xml)
        with open(st.session_state.parse_xml, 'w') as xml_file:
            xml_file.write(str(update_parse))

    print(st.session_state)


def uploade_file():
    upload_file = st.file_uploader('Загрузите произвольный xml')

    if upload_file:
        """Upload xml file and parse him with bs4 and lxml"""
    else:
        """If None file was upload use one of saved files"""

        file_name = 'CDADocumentRuDischargeSummury_max.xml'
        store_dir = os.path.abspath('data/epi_stac/')
        upload_file = os.path.join(store_dir, file_name)

    init_state(upload_file)
    print(upload_file, os.path.exists(upload_file))

    return store_dir


def find_titles():
    contents = bs_content.find_all('title')
    labels = [str(content.contents[0]) for content in contents]
    labeltocontent = {k: v for k, v in zip(labels, contents)}
    return labels, labeltocontent


def find_tables_or_text(all_data):
    data = all_data.parent.find('text').find_all('table')
    if len(data) == 0:
        print('None tables, only text')
        data = all_data.parent.find('text')
        have_tables = False
    else:
        print('Exist tables')
        have_tables = True
    return data, have_tables


def select_table(data):
    table_label = [i+1 for i in range(len(data))]
    labeltodata = {k: v for k, v in zip(table_label, data)}
    return table_label, labeltodata


def parse_table(data):
    datatable = []
    max_width = 0

    for row in data.find_all('tr'):
        datatable_row = []
        num_cells = row.find_all('td')
        if len(num_cells) == 0:
            num_cells = row.find_all('th')
        for cell in num_cells:
            cell = cell.text.replace('\n', '')
            datatable_row.append(cell)
        if len(datatable_row) > max_width:
            max_width = len(datatable_row)
        datatable.append(datatable_row)

    max_height = len(datatable)
    st.write(data.prettify())

    df = pd.DataFrame(datatable)
    st.dataframe(df)
    return max_height - 1, max_width - 1

def select_text(data):
    lists = data.find_all('list')
    paragraphs = data.find_all('paragraph')
    if len(lists) == 0 and len(paragraphs) == 0:
        have_lp = False
        return data, have_lp
    else:
        labeltotext = {k: v for k, v in zip([t.find('caption').contents[0].replace('\n', '') for t in lists], lists)}
        for p in paragraphs:
            labeltotext[p.find('caption').contents[0].replace('\n', '')] = p
        print('------')
        print([[label, val] for label, val in labeltotext.items()])
        have_lp = True
        return labeltotext, have_lp


def select_item(text_content):
    items = text_content.find_all('item')
    if len(items) != 0:
        labeltoitem = {k: v for k, v in zip([item.find('content').contents[0].replace('\n', '')
                                             if item.find('content') else item.contents[0].replace('\n', '')
                                             for item in items], items)}
        print(labeltoitem)
        return True, labeltoitem
    else:
        items = text_content.text
        return False, items


if __name__ == '__main__':
    # st.set_page_config(layout='wide')
    st.header('Trying test refactor xml file')

    store_dir = uploade_file()
    view, structure = st.columns(2)

    with view:

        xsl_file_name = 'DischSum.xsl'

        try:
            xslt = lxml.etree.parse(os.path.join(store_dir, xsl_file_name))
        except ValueError:
            st.error(ValueError)
        dom = lxml.etree.parse(st.session_state.parse_xml)
        transform = lxml.etree.XSLT(xslt)
        newdom = transform(dom)
        html = lxml.etree.tostring(newdom, pretty_print=True)
        st.components.v1.html(html, width=None, height=960, scrolling=True)


    with structure:
        st.header('How this arranged')

        with open(st.session_state.parse_xml, "r") as file:
            content = file.readlines()
            content = "".join(content)
            bs_content = bs(content, "xml")

        file.close()

        labels, labeltocontent = find_titles()
        param = st.selectbox('Choise label', labels)

        all_data = labeltocontent[param]
        data, have_tables = find_tables_or_text(all_data)

        if have_tables:
            labels_table, labletotable = select_table(data)
            table_label = st.selectbox('Find_table', labels_table)
            current_table = labletotable[table_label]
            max_height, max_wigth = parse_table(current_table)

            with st.form(key='update_xml_file'):
                i = st.number_input('X', min_value=0, max_value=max_height+1, value=0, step=1)
                j = st.number_input('Y', min_value=0, max_value=max_wigth+1, value=0, step=1)
                change = st.text_input('Input num row num col and val')
                print(f'{i} ? {max_height}, {j} ? {max_wigth}')
                if change != '':
                    if (i <= max_height) and (j <= max_wigth):
                        st.write('table[{0},{1}] changed on {2}'.format(i, j, change))
                        try:
                            cell = current_table.find_all('tr')[i].find_all('td')[j]
                        except:
                            cell = current_table.find_all('tr')[i].find_all('th')[j]
                        st.write(cell.__dict__)
                        cell.string = change
                    else:
                        if i > max_height:
                            row = bs_content.new_tag('tr')
                            current_table.append(row)
                            state = 0
                        else:
                            row = current_table.find_all('tr')[i]
                            state = 1
                        print(row.prettify())
                        if len(current_table.find_all('tr')[0].find_all('td')) != 0:
                            tag = 'td'
                        else:
                            tag = 'th'
                        if state == 0:
                            if j > max_wigth:
                                count_tags = j
                            else:
                                count_tags = max_wigth
                            for num in range(count_tags+1):
                                cell = bs_content.new_tag(tag)
                                row.append(cell)
                                if j == num:
                                    cell.string = change
                        if state == 1:
                            cell = bs_content.new_tag(tag)
                            row.append(cell)
                            cell.string = change
                submit = st.form_submit_button(label='Update', on_click=update_state(bs_content.prettify()))

        else:
            text_contents, havelp = select_text(data)
            if havelp:
                text_labels = text_contents.keys()
                text_label = st.selectbox('Choice text', text_labels)
                text_content = text_contents[text_label]
                st.write(text_content.__dict__)

                list_type, items = select_item(text_content)
                if list_type:
                    item_labels = [k for k in items.keys()]
                    item_label = st.selectbox('Choise current param', item_labels + ['append'])

                    if item_label != 'append':
                        item = items[item_label]
                    else:
                        item = bs_content.new_tag('item')
                        text_content.append(item)
                        item.string = 'Write'

                    st.write(item.__dict__)
                    with st.form(key='Update text area'):
                        change = st.text_area('Change text', item_label)
                        try:
                            item.find('content').string.replace_with(change)
                        except:
                            item.string.replace_with(change)
                        if change == item_label:
                            st.write('Change text')
                            submit = st.form_submit_button()
                        else:
                            submit = st.form_submit_button(label='Update', on_click=update_state(bs_content.prettify()))

                else:
                    st.write(items)
                    st.write("Right now i don't now how do it")
                    # with st.form(key='Update Full text area'):
                    #     change = st.text_area('Change text', 'Something')
                    #
                    #     text_content.text = change
                    #     submit = st.form_submit_button(label='Update', on_click=update_state(bs_content.prettify()))
            else:
                st.write(text_contents.__dict__)
                with st.form(key='Update text'):
                    change = st.text_area('Update text', text_contents.string)
                    text_contents.string = change
                    submit = st.form_submit_button(label='Update', on_click=update_state(bs_content.prettify()))




