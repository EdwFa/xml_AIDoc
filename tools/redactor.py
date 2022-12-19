from bs4 import BeautifulSoup as bs
import os
import re
import lxml
from lxml import etree
import pandas as pd
import streamlit as st
from io import StringIO, BytesIO
from .title_changers import VIT_PARAMS, RESINSTR_PARAMS, MORFRES_PARAMS, VAC_PARAMS, DRUG_PARAMS, NODRUG_PARAMS, \
    SURG_PARAMS, PROC_PARAMS, REACT_PARAMS, SCORES_PARAMS, STATEDIS_PARAMS, BASE_PARAMS, PDIAG_PARAMS, ZDIAG_PARAMS, \
    ANAMNEZ_PARAMS, LAB_PARAMS, CONSULT_PARAMS, RECOM_PARAMS, SERVICE_PARAM


change_titles = {
    'ОБЩИЕ ДАННЫЕ О ГОСПИТАЛИЗАЦИИ':
        {'changer': [BASE_PARAMS, PDIAG_PARAMS, ZDIAG_PARAMS], 'content': None},
    'АНАМНЕЗ':
        {'changer': ANAMNEZ_PARAMS, 'content': None},
    'СОСТОЯНИЕ ПРИ ВЫПИСКЕ':
        {'changer': STATEDIS_PARAMS, 'code': 'Наименование', 'content': None},
    'СОСТОЯНИЕ ПРИ ПОСТУПЛЕНИИ':
        {'changer': STATEDIS_PARAMS, 'code': 'Наименование', 'content': None},
    'ВИТАЛЬНЫЕ ПАРАМЕТРЫ':
        {'changer': VIT_PARAMS, 'code': 'NAME', 'content': None},
    'ОБЪЕКТИВИЗИРОВАННАЯ ОЦЕНКА СОСТОЯНИЯ БОЛЬНОГО':
        {'changer': SCORES_PARAMS, 'code': 'Наименование', 'content': None},
    'ПАТОЛОГИЧЕСКИЕ РЕАКЦИИ':
        {'changer': REACT_PARAMS, 'code': 'Наименование', 'content': None},
    'Результаты инструментальных исследований':
        {'changer': RESINSTR_PARAMS, 'code': 'Наименование', 'content': None},
    'Результаты лабораторных исследований':
        {'changer': LAB_PARAMS, 'content': None},
    'Результаты морфологических исследований':
        {'changer': MORFRES_PARAMS, 'code': 'Наименование', 'content': None},
    'Консультации врачей специалистов':
        {'changer': CONSULT_PARAMS, 'content': None},
    'ВАКЦИНАЦИЯ И ИММУНИЗАЦИЯ':
        {'changer': VAC_PARAMS, 'code': 'Наименование', 'content': None},
    'Медикаментозное лечение':
        {'changer': DRUG_PARAMS, 'code': 'Наименование', 'content': None},
    'Немедикаментозное лечение':
        {'changer': NODRUG_PARAMS, 'code': 'Наименование', 'content': None},
    'ХИРУРГИЧЕСКИЕ ВМЕШАТЕЛЬСТВА':
        {'changer': SURG_PARAMS, 'code': 'Наименование', 'content': None},
    'МЕДИЦИНСКИЕ ПРОЦЕДУРЫ':
        {'changer': PROC_PARAMS, 'code': 'Наименование', 'content': None},
    'Режим и диета':
        {'changer': RECOM_PARAMS, 'content': None},
    'Рекомендованное лечение':
        {'changer': RECOM_PARAMS, 'content': None},
    'Трудовые рекомендации':
        {'changer': RECOM_PARAMS, 'content': None},
    'Прочие рекомендации':
        {'changer': RECOM_PARAMS, 'content': None},
    'МЕДИЦИНСКИЕ УСЛУГИ':
        {'changer': SERVICE_PARAM, 'content': None}
}

def viewer(file, save_path):

    with st.expander("Валидация документа по схеме .xsd"):
        path = os.path.abspath('data/epi_stac')
        xsd_file_name = 'CDA.xsd'
        try:
            schema_root = etree.parse(os.path.join(path, xsd_file_name).replace('\\', '/'))
        except ValueError:
            st.error(ValueError)

        schema = etree.XMLSchema(schema_root)
        xml = etree.parse(save_path)

        if not schema.validate(xml):
            try:
                st.error("xml-файл содержит ошибки и не соответсвует xsd-схеме. Протокол ошибок ниже :" )
                st.error(schema.error_log)
            except ValueError:
                st.error(ValueError)
        else:
            st.success("xml-файл не содержит ошибок")

    output = BytesIO(file)

    xsl_file_name = 'DischSum.xsl'
    try:
        xslt = lxml.etree.parse(os.path.join('data/epi_stac', xsl_file_name))
    except ValueError:
        st.error(ValueError)
    dom = lxml.etree.parse(output)
    transform = lxml.etree.XSLT(xslt)
    newdom = transform(dom)
    html = lxml.etree.tostring(newdom, pretty_print=True)
    st.components.v1.html(html, width=None, height=960, scrolling=True)

    output.close()

class Redactor:
    def __init__(self, _file):
        """"""
        self.name = _file.name
        self.file = _file
        self.content = None
        self.titles = change_titles
        self.subtitles = None
        self.store_dir = os.path.abspath('store/saved_files')
        self.saved_dir = os.path.abspath('store/epicrises')
        if not os.path.exists(self.saved_dir):
            os.mkdir(self.saved_dir)
        if not os.path.exists(self.store_dir):
            os.mkdir(self.store_dir)
        self.codes_dir = os.path.abspath('store/codes')
        if not os.path.exists(self.codes_dir):
            os.mkdir(self.codes_dir)
        self.items = None

        self.changer = None

    def loader(self):
        """Check format file (only xml files)
        open file and parce this as bs object"""

        if self.name.split('.')[-1] != 'xml':
            self.get_state(False, 'Not "XML" format file!')

        save_file = os.path.join(self.store_dir, self.name)
        if os.path.exists(save_file):
            content = open(save_file, encoding='utf-8').read()
        else:
            bytes_data = self.file.getvalue()
            string = StringIO(bytes_data.decode('utf-8'))

            content = string.readlines()
            content = ''.join(content)

        bs_content = bs(content, 'xml')
        self.content = bs_content
        self.reload_changes()
        return save_file

    def get_titles(self):
        """Parse content and search titles"""
        title_contents = self.content.find_all('title')
        titles = [title.contents[0].replace('\n', '').split(' ') for title in title_contents]
        titles = [' '.join([word for word in title if word != '']) for title in titles]
        print(titles)
        for title, content in zip(titles, title_contents):
            if title in self.titles.keys():
                self.titles[title]['content'] = content.parent
        return self.titles.keys()

    def select_title(self, label):
        """Parse each content of title and select current table or text for user"""
        title = self.titles[label]
        content = title['content'].find('text').find_all('table')
        if len(content) == 0:
            if label == 'Результаты лабораторных исследований':
                new_name_table = st.text_input('Название', value='')
                if st.button('Добавить пустую таблицу'):
                    self.changer = title['changer'](self.content, title['content'].find('text'))
                    self.changer.create_new_table(new_name_table)
                return False, None
            if label == 'АНАМНЕЗ':
                rw = st.checkbox('Перезаписать все поля', key='rewrite')

            print('None tables only text')
            content = title['content'].find('text')
            self.changer = title['changer'](self.content, content)
            return False, content
        if len(content) == 1 and label != 'Результаты лабораторных исследований':
            content = content[0]
            self.changer = title['changer'](self.content, content)
            return True, content
        else:
            if label == 'ОБЩИЕ ДАННЫЕ О ГОСПИТАЛИЗАЦИИ':
                subtitle = st.selectbox('Выберите таблицу', [i for i in range(len(content))])
                content = content[subtitle]
                self.changer = title['changer'][subtitle](self.content, content)
                return True, content
            if label == 'Результаты лабораторных исследований':
                new_name_table = st.text_input('Название', value='')
                if st.button('Добавить пустую таблицу'):
                    self.changer = title['changer'](self.content, content[0].parent)
                    self.changer.create_new_table(new_name_table)
                    return False, None

                subtitle = st.selectbox('Выберите таблицу', [i for i in range(len(content))])
                content = content[subtitle]
                self.changer = title['changer'](self.content, content, subtitle)

                state = st.selectbox('Выберите тип вставляемого поля', ['исследование', 'примечание', 'результат'])
                st.session_state['state_write_field'] = state
                return True, content


    def parse_text(self, subtitle):
        return subtitle

    def parce_table(self, subtitle):
        """parce table and turn on in pandas dataframe"""
        datatable = []
        max_width = 0

        for row in subtitle.find('tbody').find_all('tr'):
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
        df = pd.DataFrame(datatable)

        st.dataframe(df)
        return max_height - 1, max_width - 1

    def get_form(self, i, max_widht):
        self.changer.change_form(i, max_widht)

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        self.changer.change_cell(i, max_height, max_width)

    def change_text(self):
        self.changer.change_text()

    """Сохраниение и скачивание результата в виде xml"""
    def reload_changes(self):
        """save cahnges in new file"""

        name = os.path.join(self.store_dir, self.name)
        with open(name, 'w', encoding='utf-8') as xml_file:
            xml_file.write(str(self.content.prettify()))

    def save_changes(self, new_name):
        """save file like new xml epicrise"""
        new_name = f'{new_name}.xml'
        name = os.path.join(self.store_dir, self.name)
        new_name = os.path.join(self.saved_dir, new_name)
        os.rename(name, new_name)
        return new_name

    def download_changes(self, new_path, new_name):
        new_file = open(new_path, encoding='utf-8').read()
        st.download_button(
            label='Download file',
            data=new_file,
            file_name=f'{new_name}.xml',
        )

    def get_state(self, state: bool, text):
        """request state(bool, True = success, False = error)
        text(string if False, other if True)"""
        if not state:
            st.error(text)

    def get_content(self):
        return self.content.prettify()


