from bs4 import BeautifulSoup as bs
import lxml
import pandas as pd
import streamlit as st
from io import StringIO, BytesIO
import json
import os
import decimal
from pprint import pprint
import copy


path_to_codes = 'store/codes'


def fill_code(current_code, row, codeSystem, codeSystemVersion, codeSystemName):
    ID, NAME = [x for x in row.values[0, :]]
    print(row.values)
    current_code['code'] = ID
    current_code['codeSystem'] = codeSystem
    current_code['codeSystemVersion'] = codeSystemVersion
    current_code['codeSystemName'] = codeSystemName
    current_code['displayName'] = NAME

def open_code(code_path):
    return pd.read_excel(code_path)


class VIT_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Данные поля витальных параметров
        здесь храним формат ячейки добавления и коды для записи/добавления
        так же храним формат ячейка entry
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')
        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.262',
            'codeSystemVersion': '5.9',
            'codeSystemName': 'Витальные параметры'
        }
        self.code['code_path'] = os.path.join(path_to_codes, f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.code['code_table'] = open_code(self.code['code_path'])
        self.codes_table = None

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.selectbox('Параметр', self.parse_code(), key=0)
            st.text_input(label=f'ед. измерения', value='', key=1)
            st.text_input(label=f'значение в первой дате', value='', key=2)
            st.text_input(label=f'значение во второй дате', value='', key=3)

    def parse_code(self):
        return [''] + [name for name in self.code['code_table']['NAME']]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        changes = [st.session_state[f'{i}'] for i in range(max_width + 1)]
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
            times = self.table.find('tbody').find_all('tr')[0].find_all('th')
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for k, cell in enumerate(changes):
            new_cell = self.content.new_tag(tag)
            if i == 0:
                new_cell.string = cell
            else:
                if k == 0:
                    row_code = self.code['code_table'][self.code['code_table']['NAME'] == cell]
                    print(row_code)
                    new_cell.string = cell
                elif k == 1:
                    unit_val = cell
                    new_cell.string = cell
                else:
                    if cell != '':
                        id_cell = f'VIT_{i}{k}'
                        content_cell = self.content.new_tag('content', ID=id_cell)
                        content_cell.string = cell
                        new_cell.append(content_cell)
                        self.change_entry(i, max_height, row_code, cell, unit_val, id_cell, times[k])
            row.append(new_cell)


    def change_entry(self, i, max_heigth, row, val_cell, unit_val, link, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.string.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        ID, NAME, _, _, _, DATA_TYPE, _ = [x for x in row.values[0, :]]
        print(row.values)

        current_entry = None
        if i <= max_heigth:
            for entry in self.entry:
                reference = entry.find('reference', value=link)
                if reference:
                    current_entry = entry

        current_entry = self.create_organizer(time, current_entry)
        current_observation = current_entry.find('observation')

        current_code = self.content.new_tag('code')
        current_code['code'] = ID
        current_code['codeSystem'] = self.code['codeSystem']
        current_code['codeSystemVersion'] = self.code['codeSystemVersion']
        current_code['codeSystemName'] = self.code['codeSystemName']
        current_code['displayName'] = NAME
        text = self.content.new_tag('originalText')
        new_link = self.content.new_tag('reference', value=link)
        text.append(new_link)
        current_code.append(text)

        val = self.content.new_tag('value')
        val['xsi:type'] = DATA_TYPE
        val['value'] = val_cell
        val['unit'] = unit_val

        current_observation.append(current_code)
        current_observation.append(val)


    def create_organizer(self, time, entry=None):
        if entry is None:
            entry = self.content.new_tag('entry')
            self.table.parent.parent.append(entry)
        entry.clear()
        organizer = self.content.new_tag('organizer', classCode="CLUSTER", moodCode="EVN")
        status_code = self.content.new_tag('statusCode', code='completed')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        organizer.append(status_code)
        organizer.append(ef_time)

        component = self.content.new_tag('component', typeCode="COMP")
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        component.append(observation)
        organizer.append(component)

        entry.append(organizer)
        return entry


class RESINSTR_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Поля хранящиеся в кодах
        дата: понятно с ней
        исследование: забираем из кодов
        результаты: понятно
        приоритет: коды"""
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')
        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.259',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Инструментальные исследования'
        }
        self.code['code_path'] = os.path.join(path_to_codes,
                                              f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.code['code_table'] = open_code(self.code['code_path'])

        self.scode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1070',
            'codeSystemVersion': '2.10',
            'codeSystemName': 'Номенклатура медицинских услуг'
        }

        self.pcode = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.258',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Справочник приоритетов'
        }
        self.pcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.pcode["codeSystem"]}_{self.pcode["codeSystemVersion"]}.xlsx')
        self.pcode['code_table'] = open_code(self.pcode['code_path'])
        self.scode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.scode["codeSystem"]}_{self.scode["codeSystemVersion"]}.xlsx')
        self.scode['code_table'] = open_code(self.scode['code_path'])

        self.codes_table = None

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        return [''] + [name for name in code_dtf[col]]

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Дата', value='', key=0)
            st.selectbox('Исследование', self.parse_code(self.code, 'Наименование'), key=1)
            st.text_input('Результат', value='', key=2)
            st.selectbox('Приоритет', self.parse_code(self.pcode, 'NAME'), key=3)
            st.selectbox('Услуга', self.parse_code(self.scode, 'NAME'), key=4)

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        changes = [st.session_state[f'{i}'] for i in range(max_width + 1)]
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for cell in changes[:4]:
            new_cell = self.content.new_tag(tag)
            new_cell.string = cell
            row.append(new_cell)
        self.change_entry(i, max_height, st.session_state['0'])

    def get_row(self, val, col, table_path, name):
        table = table_path['code_table']
        print(table.columns)
        if name:
            row = table[table[col] == val][['S_CODE', 'NAME']]
        else:
            row = table[table[col] == val]
        return row

    def change_entry(self, i, max_height, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        if i <= max_height:
            current_entry = self.entry[i-1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('observation', classCode="OBS", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_observation = current_entry.find('observation')

        type_code = self.content.new_tag('code')
        fill_code(type_code, self.get_row(st.session_state['1'], 'Наименование', self.code, False),
                  self.code['codeSystem'], self.code['codeSystemVersion'], self.code['codeSystemName'])
        current_observation.append(type_code)

        status_code = self.content.new_tag('statusCode', code='completed')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        current_observation.append(status_code)
        current_observation.append(ef_time)

        if st.session_state['3'] != '':
            priority_code = self.content.new_tag('priorityCode')
            fill_code(priority_code, self.get_row(st.session_state['3'], 'NAME', self.pcode, False),
                      self.pcode['codeSystem'], self.pcode['codeSystemVersion'], self.pcode['codeSystemName'])
            current_observation.append(priority_code)

        value = self.content.new_tag('value')
        value['xsi:type'] = 'ST'
        value.string = st.session_state['2']
        current_observation.append(value)

        entryRel = self.append_medservice(time)
        entry_code = entryRel.find('code')
        fill_code(entry_code, self.get_row(st.session_state['4'], 'NAME', self.scode, True),
                  self.scode['codeSystem'], self.scode['codeSystemVersion'], self.scode['codeSystemName'])
        current_observation.append(entryRel)

    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry

    def append_medservice(self, time):
        entryRel = self.content.new_tag('entryRelationship', typeCode="REFR", inversionInd="false")
        act = self.content.new_tag('act', classCode="ACT", moodCode="EVN")
        code = self.content.new_tag('code')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        act.append(code)
        act.append(ef_time)
        entryRel.append(act)
        return entryRel


class MORFRES_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Поля хранящиеся в кодах
        дата: понятно с ней
        исследование: забираем из кодов
        результаты: понятно
        исполнитель: пропускаем"""
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')

        self.scode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1070',
            'codeSystemVersion': '2.10',
            'codeSystemName': 'Номенклатура медицинских услуг'
        }

        self.pcode = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.258',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Справочник приоритетов'
        }

        self.pcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.pcode["codeSystem"]}_{self.pcode["codeSystemVersion"]}.xlsx')
        self.scode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.scode["codeSystem"]}_{self.scode["codeSystemVersion"]}.xlsx')
        self.scode['code_table'] = open_code(self.scode['code_path'])
        self.pcode['code_table'] = open_code(self.pcode['code_path'])

        self.codes_table = None

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        return [''] + [name for name in code_dtf[col]]

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Дата', value='', key=0)
            st.text_input('Исследование', value='', key=1)
            st.text_input('Результат', value='', key=2)
            st.selectbox('Приоритет', self.parse_code(self.pcode, 'NAME'), key=3)
            st.selectbox('Услуга', self.parse_code(self.scode, 'NAME'), key=4)

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            changes = [st.session_state[f'{i}'] for i in range(max_width + 1)]
        else:
            changes = [st.session_state[f'{i}'] for i in range(5)]
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for cell in changes[:3]:
            new_cell = self.content.new_tag(tag)
            new_cell.string = cell
            row.append(new_cell)
        new_cell = self.content.new_tag(tag)
        new_cell.string = 'Данные скрыты'
        row.append(new_cell)
        self.change_entry(i, max_height, st.session_state['0'])

    def get_row(self, val, col, table_path, name):
        table = table_path['code_table']
        print(table.columns)
        if name:
            row = table[table[col] == val][['S_CODE', 'NAME']]
        else:
            row = table[table[col] == val]
        return row

    def change_entry(self, i, max_height, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        if i <= max_height:
            current_entry = self.entry[i-1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('observation', classCode="OBS", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_observation = current_entry.find('observation')

        type_code = self.content.new_tag('code', nullFlavor='NA')
        current_observation.append(type_code)

        status_code = self.content.new_tag('statusCode', code='completed')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        current_observation.append(status_code)
        current_observation.append(ef_time)

        if st.session_state['3'] != '':
            priority_code = self.content.new_tag('priorityCode')
            fill_code(priority_code, self.get_row(st.session_state['3'], 'NAME', self.pcode, False),
                      self.pcode['codeSystem'], self.pcode['codeSystemVersion'], self.pcode['codeSystemName'])
            current_observation.append(priority_code)

        value = self.content.new_tag('value')
        value['xsi:type'] = 'ST'
        value.string = st.session_state['2']
        current_observation.append(value)

        entryRel = self.append_medservice(time)
        entry_code = entryRel.find('code')
        fill_code(entry_code, self.get_row(st.session_state['4'], 'NAME', self.scode, True),
                  self.scode['codeSystem'], self.scode['codeSystemVersion'], self.scode['codeSystemName'])
        current_observation.append(entryRel)

    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry

    def append_medservice(self, time):
        entryRel = self.content.new_tag('entryRelationship', typeCode="REFR", inversionInd="false")
        act = self.content.new_tag('act', classCode="ACT", moodCode="EVN")
        code = self.content.new_tag('code')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        act.append(code)
        act.append(ef_time)
        entryRel.append(act)
        return entryRel


class VAC_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Данные поля витальных параметров
        здесь храним формат ячейки добавления и коды для записи/добавления
        так же храним формат ячейка entry
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')
        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.11.1078',
            'codeSystemVersion': '4.5',
            'codeSystemName': 'Иммунобиологические лекарственные препараты'
        }
        self.code['code_path'] = os.path.join(path_to_codes, f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.code['code_table'] = open_code(self.code['code_path'])
        self.codes_table = None

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Дата', value='', key=0)
            st.selectbox('Препарат', self.parse_code(), key=1)
            st.text_input('Комментарий', value='', key=2)

    def parse_code(self):
        code_dtf = self.code['code_table']
        return [''] + [name for name in code_dtf['TRADENAME']]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        changes = [st.session_state[f'{i}'] for i in range(max_width + 1)]
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        table = self.code['code_table']
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for k, cell in enumerate(changes):
            new_cell = self.content.new_tag(tag)
            if k == 1:
                link = f'imm{i}'
                new_content = self.content.new_tag('content', ID=link)
                code_row = table[table['TRADENAME'] == cell][['ID', 'TRADENAME']]
                new_content.string = cell
                new_cell.append(new_content)
            else:
                new_cell.string = cell
            row.append(new_cell)
        print('--->', code_row)
        self.change_entry(i, code_row, max_height, link, st.session_state['0'])

    def change_entry(self, i, row, max_height, link, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        ID, NAME = [x for x in row.values[0, :]]
        print(row.values)

        if i <= max_height:
            current_entry = self.entry[i - 1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_sub = current_entry.find('substanceAdministration')

        text = self.content.new_tag('text')
        text.string = st.session_state['2']

        current_sub.append(text)

        ef_time = self.content.new_tag('effectiveTime', value=time)
        current_sub.append(ef_time)

        consumble = self.content.new_tag('consumable', typeCode="CSM")
        manufacture = self.content.new_tag('manufacturedProduct', classCode="MANU")
        product = self.content.new_tag('manufacturedMaterial', classCode="MMAT", determinerCode="KIND")

        current_code = self.content.new_tag('code')
        current_code['code'] = ID
        current_code['codeSystem'] = self.code['codeSystem']
        current_code['codeSystemVersion'] = self.code['codeSystemVersion']
        current_code['codeSystemName'] = self.code['codeSystemName']
        current_code['displayName'] = NAME

        code_text = self.content.new_tag('originalText')
        ref = self.content.new_tag('reference', value=f'#{link}')

        code_text.append(ref)
        current_code.append(code_text)
        product.append(current_code)
        manufacture.append(product)
        consumble.append(manufacture)
        current_sub.append(consumble)

    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry


class DRUG_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Данные поля медикаментозного лечения
        здесь храним формат ячейки добавления и коды для записи/добавления
        так же храним формат ячейка entry
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')
        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.11.1367',
            'codeSystemVersion': '5.8',
            'codeSystemName': 'Действующие вещества лекарственных препаратов для медицинского применения, в том числе необходимых для льготного обеспечения граждан лекарственными средствами'
        }
        self.code['code_path'] = os.path.join(path_to_codes,
                                              f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.code['code_table'] = open_code(self.code['code_path'])
        self.codes_table = None

    def change_form(self, i, max_width):
        """cheate form for change vit params
        действующее вещество: выбираем из каталога
        схема лечения: пишем так
        период лечения: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.selectbox('Действующее вещество', self.parse_code(), key=0)
            st.text_input('Схема лечения', value='', key=1)
            st.text_input('Период лечения', value='', key=2)

    def parse_code(self):
        code_dtf = self.code['code_table']
        return [''] + [name for name in code_dtf['NAME_RUS']]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        changes = [st.session_state[f'{i}'] for i in range(max_width + 1)]
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        table = self.code['code_table']
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for k, cell in enumerate(changes):
            new_cell = self.content.new_tag(tag)
            if k == 0:
                new_content = self.content.new_tag('content')
                code_row = table[table['NAME_RUS'] == cell][['ID', 'NAME_RUS']]
                new_content.string = cell
                new_cell.append(new_content)
            else:
                new_cell.string = cell
            row.append(new_cell)
        print('--->', code_row)
        self.change_entry(i, code_row, max_height)

    def change_entry(self, i, row, max_height):
        """Изменяем существующие поля"""

        print(row)
        ID, NAME = [x for x in row.values[0, :]]
        print(row.values)

        if i <= max_height:
            current_entry = self.entry[i - 1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_sub = current_entry.find('substanceAdministration')

        consumble = self.content.new_tag('consumable')
        manufacture = self.content.new_tag('manufacturedProduct')
        product = self.content.new_tag('manufacturedLabeledDrug')

        current_code = self.content.new_tag('code')
        current_code['code'] = ID
        current_code['codeSystem'] = self.code['codeSystem']
        current_code['codeSystemVersion'] = self.code['codeSystemVersion']
        current_code['codeSystemName'] = self.code['codeSystemName']
        current_code['displayName'] = NAME

        product.append(current_code)
        manufacture.append(product)
        consumble.append(manufacture)
        current_sub.append(consumble)

    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry


class NODRUG_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Данные поля медикаментозного лечения
        здесь храним формат ячейки добавления и коды для записи/добавления
        так же храним формат ячейка entry
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')
        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.11.1367',
            'codeSystemVersion': '5.8',
            'codeSystemName': 'Действующие вещества лекарственных препаратов для медицинского применения, в том числе необходимых для льготного обеспечения граждан лекарственными средствами'
        }
        self.code['code_path'] = os.path.join(path_to_codes,
                                              f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.code['code_table'] = open_code(self.code['code_path'])
        self.codes_table = None

    def change_form(self, i, max_width):
        """cheate form for change vit params
        действующее вещество: выбираем из каталога
        схема лечения: пишем так
        период лечения: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Название', value='', key=0)
            st.text_input('Схема лечения', value='', key=1)
            st.text_input('Период лечения', value='', key=2)

    def parse_code(self):
        code_dtf = self.code['code_table']
        return [''] + [name for name in code_dtf['NAME_RUS']]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        changes = [st.session_state[f'{i}'] for i in range(max_width + 1)]
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        # table = pd.read_excel(self.code['code_path'])
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for k, cell in enumerate(changes):
            new_cell = self.content.new_tag(tag)
            if k == 0:
                new_content = self.content.new_tag('content')
                # code_row = table[table['NAME_RUS'] == cell][['ID', 'NAME_RUS']]
                new_content.string = cell
                new_cell.append(new_content)
            else:
                new_cell.string = cell
            row.append(new_cell)
        # self.change_entry(i, code_row, max_height)

    def change_entry(self, i, row, max_height):
        """Изменяем существующие поля"""

        print(row)
        ID, NAME = [x for x in row.values[0, :]]
        print(row.values)

        if i <= max_height:
            current_entry = self.entry[i - 1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_sub = current_entry.find('substanceAdministration')

        consumble = self.content.new_tag('consumable')
        manufacture = self.content.new_tag('manufacturedProduct')
        product = self.content.new_tag('manufacturedLabeledDrug')

        current_code = self.content.new_tag('code')
        current_code['code'] = ID
        current_code['codeSystem'] = self.code['codeSystem']
        current_code['codeSystemVersion'] = self.code['codeSystemVersion']
        current_code['codeSystemName'] = self.code['codeSystemName']
        current_code['displayName'] = NAME

        product.append(current_code)
        manufacture.append(product)
        consumble.append(manufacture)
        current_sub.append(consumble)

    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry


class SURG_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Поля хранящиеся в кодах
        дата: понятно с ней
        код операции: пишем
        название: понятно
        вид анестезии: коды анестезий
        хирург: не сохраняем в поля но выводим как данные"""
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')

        self.scode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1070',
            'codeSystemVersion': '2.10',
            'codeSystemName': 'Номенклатура медицинских услуг'
        }

        self.icode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1079',
            'codeSystemVersion': '4.1',
            'codeSystemName': 'Виды имплантируемых медицинских изделий и вспомогательных устройств для пациентов с ограниченными возможностями'
        }

        self.acode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1033',
            'codeSystemVersion': '4.1',
            'codeSystemName': 'Виды анестезии'
        }

        self.tcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1048',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Учетные группы аппаратуры, используемой при операциях'
        }

        self.scode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.scode["codeSystem"]}_{self.scode["codeSystemVersion"]}.xlsx')
        self.icode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.icode["codeSystem"]}_{self.icode["codeSystemVersion"]}.xlsx')
        self.acode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.acode["codeSystem"]}_{self.acode["codeSystemVersion"]}.xlsx')
        self.tcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.tcode["codeSystem"]}_{self.tcode["codeSystemVersion"]}.xlsx')
        self.scode['code_table'] = open_code(self.scode['code_path'])
        self.icode['code_table'] = open_code(self.icode['code_path'])
        self.acode['code_table'] = open_code(self.acode['code_path'])
        self.tcode['code_table'] = open_code(self.tcode['code_path'])

        self.codes_table = None

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Дата', value='', key=0)
            st.text_input('Код операции', value='', key=1)
            st.text_input('Название', value='', key=2)
            st.selectbox('Анастезия', self.parse_code(self.acode, 'Name'), key=3)
            st.text_input('Врач хирург', value='', key=4)
            st.selectbox('Услуга', self.parse_code(self.scode, 'NAME'), key=5)
            st.selectbox('использование устройств и имплантов', self.parse_code(self.icode, 'NAME'), key=6)
            st.selectbox('используемая аппаратура', self.parse_code(self.tcode, 'NAME'), key=7)

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            changes = [st.session_state[f'{i}'] for i in range(max_width)]
        else:
            changes = [st.session_state[f'{i}'] for i in range(8)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        if i == 0:
            for cell in changes:
                new_cell = self.content.new_tag(tag)
                new_cell.string = cell
                row.append(new_cell)
        else:
            for j, cell in enumerate(changes[:5]):
                new_cell = self.content.new_tag(tag)
                new_cell.string = cell
                if j == 2 and changes[6] != '':
                    new_implant = self.content.new_tag('content', styleCode="Italics")
                    new_implant.string = changes[6]
                    new_cell.append(new_implant)
                row.append(new_cell)
            self.change_entry(i, max_height, st.session_state['0'])

    def get_row(self, val, col, table_path, name):
        if val == '':
            return pd.DataFrame({'A': []})
        table = table_path['code_table']
        print(table.columns)
        if name:
            row = table[table[col] == val][['S_CODE', col]]
        else:
            row = table[table[col] == val][['ID', col]]
        return row

    def change_entry(self, i, max_height, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        if i <= max_height:
            current_entry = self.entry[i-1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('procedure', classCode="PROC", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_observation = current_entry.find('procedure')

        service_code = self.content.new_tag('code')
        fill_code(service_code, self.get_row(st.session_state['5'], 'NAME', self.scode, True),
                  self.scode['codeSystem'], self.scode['codeSystemVersion'], self.scode['codeSystemName'])
        current_observation.append(service_code)

        text = self.content.new_tag('text')
        text.string = st.session_state['2']
        current_observation.append(text)

        status_code = self.content.new_tag('statusCode', code='completed')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        current_observation.append(status_code)
        current_observation.append(ef_time)

        if st.session_state['7'] != '':
            participantMNT = self.append_participant('MNT')
            codeMNT = participantMNT.find('code')
            fill_code(codeMNT, self.get_row(st.session_state['7'], 'NAME', self.tcode, False),
                      self.tcode['codeSystem'], self.tcode['codeSystemVersion'], self.tcode['codeSystemName'])
            current_observation.append(participantMNT)

        if st.session_state['6'] != '':
            participantMANU = self.append_participant('MANU')
            codeMANU = participantMANU.find('code')
            fill_code(codeMANU, self.get_row(st.session_state['6'], 'NAME', self.icode, False),
                      self.icode['codeSystem'], self.icode['codeSystemVersion'], self.icode['codeSystemName'])
            current_observation.append(participantMANU)

        if st.session_state['3'] != '':
            entryRel = self.append_medservice()
            entry_code = entryRel.find('code')
            fill_code(entry_code, self.get_row(st.session_state['3'], 'Name', self.acode, False),
                      self.acode['codeSystem'], self.acode['codeSystemVersion'], self.acode['codeSystemName'])
            current_observation.append(entryRel)


    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('procedure', classCode="PROC", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry

    def append_medservice(self):
        entryRel = self.content.new_tag('entryRelationship', typeCode="COMP")

        current_sub = self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN")
        consumble = self.content.new_tag('consumable', typeCode="CSM")
        manufacture = self.content.new_tag('manufacturedProduct', classCode="MANU")
        product = self.content.new_tag('manufacturedLabeledDrug')
        current_code = self.content.new_tag('code')

        product.append(current_code)
        manufacture.append(product)
        consumble.append(manufacture)
        current_sub.append(consumble)
        entryRel.append(current_sub)
        return entryRel

    def append_participant(self, CODE1):
        participant = self.content.new_tag('participant', typeCode="DEV")
        role = self.content.new_tag('participantRole', classCode=CODE1)
        playing_device = self.content.new_tag('playingDevice')
        code = self.content.new_tag('code')
        playing_device.append(code)
        role.append(playing_device)
        participant.append(role)
        return participant


class PROC_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Поля хранящиеся в кодах
        дата: понятно с ней
        код операции: пишем
        название: понятно
        вид анестезии: коды анестезий
        хирург: не сохраняем в поля но выводим как данные"""
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')

        self.scode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1070',
            'codeSystemVersion': '2.10',
            'codeSystemName': 'Номенклатура медицинских услуг'
        }

        self.icode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1079',
            'codeSystemVersion': '4.1',
            'codeSystemName': 'Виды имплантируемых медицинских изделий и вспомогательных устройств для пациентов с ограниченными возможностями'
        }

        self.acode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1033',
            'codeSystemVersion': '4.1',
            'codeSystemName': 'Виды анестезии'
        }
        self.scode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.scode["codeSystem"]}_{self.scode["codeSystemVersion"]}.xlsx')
        self.icode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.icode["codeSystem"]}_{self.icode["codeSystemVersion"]}.xlsx')
        self.acode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.acode["codeSystem"]}_{self.acode["codeSystemVersion"]}.xlsx')
        self.scode['code_table'] = open_code(self.scode['code_path'])
        self.icode['code_table'] = open_code(self.icode['code_path'])
        self.acode['code_table'] = open_code(self.acode['code_path'])

        self.codes_table = None

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Дата', value='', key=0)
            st.text_input('Код операции', value='', key=1)
            st.text_input('Название', value='', key=2)
            st.selectbox('Анастезия', self.parse_code(self.acode, 'Name'), key=3)
            st.text_input('Врач хирург', value='', key=4)
            st.selectbox('Услуга', self.parse_code(self.scode, 'NAME'), key=5)
            st.selectbox('использование устройств и имплантов', self.parse_code(self.icode, 'NAME'), key=6)

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            changes = [st.session_state[f'{i}'] for i in range(max_width)]
        else:
            changes = [st.session_state[f'{i}'] for i in range(7)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        if i == 0:
            for cell in changes:
                new_cell = self.content.new_tag(tag)
                new_cell.string = cell
                row.append(new_cell)
        else:
            for j, cell in enumerate(changes[:5]):
                new_cell = self.content.new_tag(tag)
                new_cell.string = cell
                if j == 2 and changes[6] != '':
                    new_implant = self.content.new_tag('content', styleCode="Italics")
                    new_implant.string = changes[6]
                    new_cell.append(new_implant)
                row.append(new_cell)
            self.change_entry(i, max_height, st.session_state['0'])

    def get_row(self, val, col, table_path, name):
        if val == '':
            return pd.DataFrame({'A': []})
        table = table_path['code_table']
        print(table.columns)
        if name:
            row = table[table[col] == val][['S_CODE', col]]
        else:
            row = table[table[col] == val][['ID', col]]
        return row

    def change_entry(self, i, max_height, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        if i <= max_height:
            current_entry = self.entry[i - 1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('procedure', classCode="PROC", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_observation = current_entry.find('procedure')

        service_code = self.content.new_tag('code')
        fill_code(service_code, self.get_row(st.session_state['5'], 'NAME', self.scode, True),
                  self.scode['codeSystem'], self.scode['codeSystemVersion'], self.scode['codeSystemName'])
        current_observation.append(service_code)

        text = self.content.new_tag('text')
        text.string = st.session_state['2']
        current_observation.append(text)

        status_code = self.content.new_tag('statusCode', code='completed')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        current_observation.append(status_code)
        current_observation.append(ef_time)

        if st.session_state['6'] != '':
            participantMANU = self.append_participant('MANU')
            codeMANU = participantMANU.find('code')
            fill_code(codeMANU, self.get_row(st.session_state['6'], 'NAME', self.icode, False),
                      self.icode['codeSystem'], self.icode['codeSystemVersion'], self.icode['codeSystemName'])
            current_observation.append(participantMANU)

        if st.session_state['3'] != '':
            entryRel = self.append_medservice()
            entry_code = entryRel.find('code')
            fill_code(entry_code, self.get_row(st.session_state['3'], 'Name', self.acode, False),
                      self.acode['codeSystem'], self.acode['codeSystemVersion'], self.acode['codeSystemName'])
            current_observation.append(entryRel)


    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('procedure', classCode="PROC", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry

    def append_medservice(self):
        entryRel = self.content.new_tag('entryRelationship', typeCode="COMP")

        current_sub = self.content.new_tag('substanceAdministration', classCode="SBADM", moodCode="EVN")
        consumble = self.content.new_tag('consumable')
        manufacture = self.content.new_tag('manufacturedProduct')
        product = self.content.new_tag('manufacturedLabeledDrug')
        current_code = self.content.new_tag('code')

        product.append(current_code)
        manufacture.append(product)
        consumble.append(manufacture)
        current_sub.append(consumble)
        entryRel.append(current_sub)
        return entryRel

    def append_participant(self, CODE1):
        participant = self.content.new_tag('participant', typeCode="DEV")
        role = self.content.new_tag('participantRole', classCode=CODE1)
        playing_device = self.content.new_tag('playingDevice')
        code = self.content.new_tag('code')
        playing_device.append(code)
        role.append(playing_device)
        participant.append(role)
        return participant


class REACT_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Поля хранящиеся в кодах
        Тип агента: медикамент или немедикамент
        действующее вещество: из кодов
        тип реакции: из кодов
        комментарий: понятно
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')

        self.tcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1064',
            'codeSystemVersion': '2.2',
            'codeSystemName': 'Тип патологической реакции для сбора аллергоанамнеза'
        }

        self.rcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1063',
            'codeSystemVersion': '1.2',
            'codeSystemName': 'Основные клинические проявления патологических реакций для сбора аллергоанамнеза'
        }

        self.ccode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1367',
            'codeSystemVersion': '5.8',
            'codeSystemName': 'Действующие вещества лекарственных препаратов для медицинского применения, в том числе необходимых для льготного обеспечения граждан лекарственными средствами'

        }
        self.ccode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.ccode["codeSystem"]}_{self.ccode["codeSystemVersion"]}.xlsx')
        self.rcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.rcode["codeSystem"]}_{self.rcode["codeSystemVersion"]}.xlsx')
        self.tcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.tcode["codeSystem"]}_{self.tcode["codeSystemVersion"]}.xlsx')
        self.ccode['code_table'] = open_code(self.ccode['code_path'])
        self.rcode['code_table'] = open_code(self.rcode['code_path'])
        self.tcode['code_table'] = open_code(self.tcode['code_path'])

        self.codes_table = None

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('Дата', value='', key=0)
            st.selectbox('Тип агента', ['', 'медикамент', 'не медикамент'], key=1)
            st.selectbox('Действующее вещество', self.parse_code(self.ccode, 'NAME_RUS'), key=2)
            st.selectbox('Основные клинические проявления патологических реакций', self.parse_code(self.rcode, 'NAME'), key=5)
            st.selectbox('Тип патологической реакции', self.parse_code(self.tcode, 'NAME'), key=3)
            st.text_input('Комментарий', value='', key=4)

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            changes = [st.session_state[f'{i}'] for i in range(max_width)]
        else:
            changes = [st.session_state[f'{i}'] for i in range(6)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        if i == 0:
            for cell in changes:
                new_cell = self.content.new_tag(tag)
                new_cell.string = cell
                row.append(new_cell)
        else:
            for j, cell in enumerate(changes[:5]):
                new_cell = self.content.new_tag(tag)
                if j == 2:
                    new_content = self.content.new_tag('content', ID=f'attc{i}')
                    new_content.string = cell
                    new_cell.append(new_content)
                else:
                    new_cell.string = cell
                if j == 3 and changes[5] != '':
                    new_implant = self.content.new_tag('content', ID=f'attr{i}')
                    new_implant.string = changes[5]
                    new_cell.append(new_implant)
                row.append(new_cell)
            self.change_entry(i, max_height, st.session_state['0'])

    def get_row(self, val, col, table_path, name):
        if val == '':
            return pd.DataFrame({'A': []})
        table = table_path['code_table']
        print(table.columns)
        if name:
            row = table[table[col] == val][['S_CODE', col]]
        else:
            row = table[table[col] == val][['ID', col]]
        return row


    def change_entry(self, i, max_height, time):
        """Изменяем существующие поля"""

        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)

        reaglink, reactlink = f'#attc{i}', f'#attr{i}'

        if i <= max_height:
            current_entry = self.entry[i - 1]
            current_entry.clear()
            current_entry.append(self.content.new_tag('observation', classCode="OBS", moodCode="EVN"))
        else:
            current_entry = self.create_entry()

        current_observation = current_entry.find('observation')

        service_code = self.content.new_tag('code')
        fill_code(service_code, self.get_row(st.session_state['3'], 'NAME', self.tcode, False),
                  self.tcode['codeSystem'], self.tcode['codeSystemVersion'], self.tcode['codeSystemName'])
        current_observation.append(service_code)

        text = self.content.new_tag('text')
        text.string = st.session_state['4']
        current_observation.append(text)

        status_code = self.content.new_tag('statusCode', code='completed')
        ef_time = self.content.new_tag('effectiveTime', value=time)
        current_observation.append(status_code)
        current_observation.append(ef_time)

        if st.session_state['1'] == 'не медикамент':
            participant = self.append_participant('SPEC', 'MAT')
        else:
            participant = self.append_participant('MANU', 'MMAT')
        current_observation.append(participant)

        agent_code = participant.find('code')
        fill_code(agent_code, self.get_row(st.session_state['2'], 'NAME_RUS', self.ccode, False),
                  self.ccode['codeSystem'], self.ccode['codeSystemVersion'], self.ccode['codeSystemName'])
        code_text = self.content.new_tag('originalText')
        ref = self.content.new_tag('reference', value=reaglink)
        code_text.append(ref)
        agent_code.append(code_text)

        entry_rel = self.append_react(reactlink)
        entry_code = entry_rel.find('code')
        fill_code(entry_code, self.get_row(st.session_state['5'], 'NAME', self.rcode, False),
                  self.rcode['codeSystem'], self.rcode['codeSystemVersion'], self.rcode['codeSystemName'])
        current_observation.append(entry_rel)



    def create_entry(self):
        entry = self.content.new_tag('entry')
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")

        entry.append(observation)
        self.table.parent.parent.append(entry)
        return entry

    def append_participant(self, CODE1, CODE2):
        participant = self.content.new_tag('participant', typeCode="IND")
        role = self.content.new_tag('participantRole', classCode=CODE1)
        playing_device = self.content.new_tag('playingEntity', classCode=CODE2)
        code = self.content.new_tag('code')
        playing_device.append(code)
        role.append(playing_device)
        participant.append(role)
        return participant

    def append_react(self, link):
        entryRelationship = self.content.new_tag('entryRelationship', typeCode="MFST")
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        code = self.content.new_tag('code')
        code_text = self.content.new_tag('originalText')
        ref = self.content.new_tag('reference', value=link)
        code_text.append(ref)
        code.append(code_text)
        observation.append(code)
        entryRelationship.append(observation)
        return entryRelationship


class SCORES_PARAMS:
    def __init__(self, _content, _table, _entry=None):
        """Поля хранящиеся в кодах
        Дата:
        Шкала:
        Результаты подсчета:
        """
        self.content = _content
        self.table = _table

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        st.text_area('Оценка', value='', height=300, key=0)

    # def change_cell(self, i, max_height, max_width):
    #     """Change exist cell in current table"""
    #     # if i == 0:
    #     changes = [st.session_state[f'{i}'] for i in range(max_width+1)]
    #     # else:
    #     #     changes = [st.session_state[f'{i}'] for i in range(6)]
    #     print(changes)
    #     empty_changes = True
    #     for change in changes:
    #         if change != '':
    #             empty_changes = False
    #     if empty_changes:
    #         return None
    #     if i != 0:
    #         tag = 'td'
    #     else:
    #         tag = 'th'
    #     if i <= max_height:
    #         row = self.table.find('tbody').find_all('tr')[i]
    #         row.clear()
    #     else:
    #         row = self.content.new_tag('tr')
    #         self.table.find('tbody').append(row)
    #     for cell in changes:
    #         new_cell = self.content.new_tag(tag)
    #         new_cell.string = cell
    #         row.append(new_cell)
    def change_text(self):
        if st.session_state['0'] != '':
            self.table.string = st.session_state['0']


class STATEDIS_PARAMS:
    def __init__(self, _content, _text, _entry=None):
        """Сохраяняем в текстовое поле данные без таблицы
        текст: понятно
        код статуса: из кодов
        """
        self.content = _content
        self.text = _text
        self.entry = _text.parent.parent.find('entry')

        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.11.1006',
            'codeSystemVersion': '2.3',
            'codeSystemName': 'Степень тяжести состояния пациента'
        }
        self.code['code_path'] = os.path.join(path_to_codes,
                                              f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.code['code_table'] = open_code(self.code['code_path'])
        self.codes_table = None

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_form(self, i, max_width):
        st.selectbox('Статус', self.parse_code(self.code, 'NAME'), key=0)
        st.text_area('Описание', '', height=300, key=1)

    def change_text(self):
        changes = [st.session_state[f'{i}'] for i in range(2)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if changes[1] != '' and changes[0] != '':
            new_text = self.content.new_tag('text')
            new_text.string = changes[1]
            self.text.replace_with(new_text)
            self.change_entry()


    def get_row(self, val, col, table_path):
        if val == '':
            return pd.DataFrame({'A': []})
        table = table_path['code_table']
        print(table.columns)

        row = table[table[col] == val][['ID', col]]
        return row

    def change_entry(self):
        """Изменяем существующие поля"""
        entry = self.entry
        if entry is None:
            entry = self.content.new_tag('entry')
        else:
            entry.clear()
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        code = self.content.new_tag('code', code="804", codeSystem="1.2.643.5.1.13.13.11.1380",
                                    codeSystemVersion="1.1", codeSystemName="Кодируемые поля CDA документов",
                                    displayName="Состояние пациента")
        observation.append(code)


        text = self.content.new_tag('value')

        row = self.get_row(st.session_state['0'], 'NAME', self.code)
        fill_code(text, row, self.code['codeSystem'], self.code['codeSystemVersion'], self.code['codeSystemName'])
        text['xsi:type'] = 'CD'
        observation.append(text)

        entry.append(observation)


class BASE_PARAMS:
    def __init__(self, _content, _table):
        """
        вид госпитализации: код
        дата пребывания: вводим
        результаты пребывания: код
        отделение поступления: вводим(возможно удалить поле)
        показания к госпитализации: ввод
        """
        self.content = _content
        self.table = _table
        self.entry_kind = _table.parent.parent.find_all('entry')[0]
        self.entry_res = _table.parent.parent.find_all('entry')[1]

        self.kcode = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.256',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Срочность госпитализации'
        }
        self.kcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.kcode["codeSystem"]}_{self.kcode["codeSystemVersion"]}.xlsx')

        self.rcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1046',
            'codeSystemVersion': '4.1',
            'codeSystemName': 'Результаты обращения (госпитализации)'
        }
        self.rcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.rcode["codeSystem"]}_{self.rcode["codeSystemVersion"]}.xlsx')
        self.kcode['code_table'] = open_code(self.kcode['code_path'])
        self.rcode['code_table'] = open_code(self.rcode['code_path'])

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        if i == 0:
            st.selectbox('Срочность госпитализации', self.parse_code(self.kcode, 'NAME'), key=0)
        elif i == 1:
            st.text_input('Время пребывания( запись в виде "дд/мм/гггг по дд/мм/гггг"', value='', key=0)
        elif i == 2:
            st.selectbox('Результаты пребывания', self.parse_code(self.rcode, 'NAME'), key=0)
        else:
            st.text_input('Другие данные', value='', key=0)

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        change = st.session_state['0']
        if change == '':
            return None
        tag = 'td'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
        else:
            return None
        new_cell = row.find_all(tag)[1]
        new_cell.string = change
        self.change_entry(i, change)


    def get_row(self, val, col, table_path):
        if val == '':
            return pd.DataFrame({'A': []})
        table = table_path['code_table']
        print(table.columns)
        row = table[table[col] == val][['ID', col]]
        return row

    def change_entry(self, i, val):
        """Изменяем существующие поля"""

        if i == 0:
            current_entry = self.entry_kind.find('entryRelationship').find('code')
            row = self.get_row(st.session_state['0'], 'NAME', self.kcode)
            fill_code(current_entry, row, self.kcode['codeSystem'], self.kcode['codeSystemVersion'],
                      self.kcode['codeSystemName'])
        elif i == 1:
            current_entry = self.entry_kind.find('effectiveTime')
            if 'по' in val:
                split_simpol = 'по'
            elif '-' in val:
                split_simpol = '-'
            else:
                split_simpol = ' '
            low_time, high_time = val.split(split_simpol)
            current_entry.find('low')['value'] = self.change_time(low_time)
            current_entry.find('high')['value'] = self.change_time(high_time)
        elif i == 2:
            current_entry = self.entry_res.find('code')
            row = self.get_row(st.session_state['0'], 'NAME', self.rcode)
            fill_code(current_entry, row, self.rcode['codeSystem'], self.rcode['codeSystemVersion'], self.rcode['codeSystemName'])


    def change_time(self, time):
        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)
        return time


class PDIAG_PARAMS:
    def __init__(self, _content, _table):
        """
        вид госпитализации: код
        дата пребывания: вводим
        результаты пребывания: код
        отделение поступления: вводим(возможно удалить поле)
        показания к госпитализации: ввод
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')[2]

        self.tcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1077',
            'codeSystemVersion': '2.1',
            'codeSystemName': 'Виды нозологических единиц диагноза'
        }
        self.tcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.tcode["codeSystem"]}_{self.tcode["codeSystemVersion"]}.xlsx')

        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.11.1005',
            'codeSystemVersion': '2.21',
            'codeSystemName': 'Международная классификация болезней и состояний, связанных со здоровьем 10 пересмотра. Версия 4'
        }
        self.code['code_path'] = os.path.join(path_to_codes,
                                              f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')
        self.tcode['code_table'] = open_code(self.tcode['code_path'])
        self.code['code_table'] = open_code(self.code['code_path'])

    def change_form(self, i, max_width):
        """cheate form for change vit params
        шифр: выбираем из каталога в коде заболевания (будет выбор болезни)
        тип: из кодов
        текст: описание"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.selectbox('Заболевание', self.parse_code(self.code, 'MKB_NAME'), key=0)
            st.selectbox('Тип', self.parse_code(self.tcode, 'FULL_NAME'), key=1)
            st.text_input('Текст', value='', key=2)

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        changes = [st.session_state[f'{i}'] for i in range(max_width+1)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for j, cell in enumerate(changes):
            new_cell = self.content.new_tag(tag)
            if j == 0:
                ID, _ = [x for x in self.get_row(cell, 'MKB_CODE', 'MKB_NAME', self.code).values[0, :]]
                new_cell.string = ID
            else:
                new_cell.string = cell
            row.append(new_cell)
        self.change_entry(i, max_height)

    def get_row(self, val, id_name, col, table_path):
        table = table_path['code_table']
        print(table.columns)
        row = table[table[col] == val][[id_name, col]]
        return row

    def change_entry(self, i, max_height):
        """Изменяем существующие поля"""

        current_entries = self.entry.find_all('entryRelationship', typeCode='COMP')
        if i <= max_height:
            current_entry = current_entries[i - 1]
            current_entry.clear()
        else:
            current_entry = self.content.new_tag('entryRelationship', typeCode="COMP")
            self.entry.act.append(current_entry)

        current_observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        type_code = self.content.new_tag('code')
        fill_code(type_code, self.get_row(st.session_state['1'], 'ID', 'FULL_NAME', self.tcode),
                  self.tcode['codeSystem'], self.tcode['codeSystemVersion'], self.tcode['codeSystemName'])
        current_observation.append(type_code)

        text = self.content.new_tag('text')
        text.string = st.session_state['2']
        current_observation.append(text)

        value_code = self.content.new_tag('value')
        fill_code(value_code, self.get_row(st.session_state['0'], 'MKB_CODE', 'MKB_NAME', self.code),
                  self.code['codeSystem'], self.code['codeSystemVersion'], self.code['codeSystemName'])
        value_code['xsi:type'] = 'CD'
        current_observation.append(value_code)

        current_entry.append(current_observation)


class ZDIAG_PARAMS:
    def __init__(self, _content, _table):
        """
        вид госпитализации: код
        дата пребывания: вводим
        результаты пребывания: код
        отделение поступления: вводим(возможно удалить поле)
        показания к госпитализации: ввод
        """
        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')[3]

        self.tcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1077',
            'codeSystemVersion': '2.1',
            'codeSystemName': 'Виды нозологических единиц диагноза'
        }
        self.tcode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.tcode["codeSystem"]}_{self.tcode["codeSystemVersion"]}.xlsx')

        self.code = {
            'codeSystem': '1.2.643.5.1.13.13.11.1005',
            'codeSystemVersion': '2.21',
            'codeSystemName': 'Международная классификация болезней и состояний, связанных со здоровьем 10 пересмотра. Версия 4'
        }
        self.code['code_path'] = os.path.join(path_to_codes,
                                              f'{self.code["codeSystem"]}_{self.code["codeSystemVersion"]}.xlsx')

        self.ncode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1049',
            'codeSystemVersion': '3.1',
            'codeSystemName': 'Характер заболевания'
        }
        self.ncode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.ncode["codeSystem"]}_{self.ncode["codeSystemVersion"]}.xlsx')
        self.tcode['code_table'] = open_code(self.tcode['code_path'])
        self.code['code_table'] = open_code(self.code['code_path'])
        self.ncode['code_table'] = open_code(self.ncode['code_path'])

    def change_form(self, i, max_width):
        """cheate form for change vit params
        шифр: выбираем из каталога в коде заболевания (будет выбор болезни)
        тип: из кодов
        текст: описание"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.selectbox('Заболевание', self.parse_code(self.code, 'MKB_NAME'), key=0)
            st.selectbox('Тип', self.parse_code(self.tcode, 'FULL_NAME'), key=1)
            st.text_input('Текст', value='', key=2)
            st.selectbox('Характер заболевания', self.parse_code(self.ncode, 'NAME'), key=3)


    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            changes = [st.session_state[f'{i}'] for i in range(max_width+1)] + ['']
        else:
            changes = [st.session_state[f'{i}'] for i in range(max_width + 2)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for j, cell in enumerate(changes[:3]):
            new_cell = self.content.new_tag(tag)
            if j == 0:
                ID, _ = [x for x in self.get_row(cell, 'MKB_CODE', 'MKB_NAME', self.code).values[0, :]]
                new_cell.string = ID
            else:
                new_cell.string = cell
            row.append(new_cell)
        if i != 0:
            self.change_entry(i, max_height)

    def get_row(self, val, id_name, col, table_path):
        table = table_path['code_table']
        print(table.columns)
        row = table[table[col] == val][[id_name, col]]
        return row

    def change_entry(self, i, max_height):
        """Изменяем существующие поля"""

        """Изменяем существующие поля"""

        current_entries = self.entry.find_all('entryRelationship', typeCode="COMP")
        if i <= max_height:
            current_entry = current_entries[i - 1]
            current_entry.clear()
        else:
            current_entry = self.content.new_tag('entryRelationship', typeCode="COMP")
            self.entry.act.append(current_entry)

        current_observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        type_code = self.content.new_tag('code')
        fill_code(type_code, self.get_row(st.session_state['1'], 'ID', 'FULL_NAME', self.tcode),
                  self.tcode['codeSystem'], self.tcode['codeSystemVersion'], self.tcode['codeSystemName'])
        current_observation.append(type_code)

        text = self.content.new_tag('text')
        text.string = st.session_state['2']
        current_observation.append(text)

        value_code = self.content.new_tag('value')
        fill_code(value_code, self.get_row(st.session_state['0'], 'MKB_CODE', 'MKB_NAME', self.code),
                  self.code['codeSystem'], self.code['codeSystemVersion'], self.code['codeSystemName'])
        value_code['xsi:type'] = 'CD'
        current_observation.append(value_code)


        if st.session_state['3'] != '':
            new_ndeasease = self.content.new_tag('entryRelationship', inversionInd="true", typeCode="SUBJ")
            new_act = self.content.new_tag('act', classCode="ACT", moodCode="EVN")
            new_code = self.content.new_tag('code')
            fill_code(new_code,
                      self.get_row(st.session_state['3'], 'ID', 'NAME', self.ncode),
                      self.ncode['codeSystem'], self.ncode['codeSystemVersion'], self.ncode['codeSystemName'])
            new_act.append(new_code)
            new_ndeasease.append(new_act)
            current_observation.append(new_ndeasease)

        current_entry.append(current_observation)


class ANAMNEZ_PARAMS:
    def __init__(self, _content, _text):
        """
        Мы храним его в виде текста так что устанавливать параметры не будем конкретно но меняемые разделы:
        льготная категория, потенциально опасные для здоровья факторы, проффесиональные для здоровья вредности,
        местность регистрации, занятось, вредные привычки и зависимости
        """
        self.content = _content
        self.text = _text
        self.entry = _text.parent

        self.icode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1053',
            'codeSystemVersion': '3.3',
            'codeSystemName': 'Группы инвалидности',
            'current_entry': 1
        }
        self.icode['code_path'] = os.path.join(path_to_codes,
                                              f'{self.icode["codeSystem"]}_{self.icode["codeSystemVersion"]}.xlsx')

        self.lcode = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.43',
            'codeSystemVersion': '3.2',
            'codeSystemName': 'Льготные категории населения',
            'current_entry': 0,
        }
        self.lcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.lcode["codeSystem"]}_{self.lcode["codeSystemVersion"]}.xlsx')

        self.tcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1041',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Порядок установления инвалидности',
            'current_entry': 1,
        }
        self.tcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.tcode["codeSystem"]}_{self.tcode["codeSystemVersion"]}.xlsx')

        self.dfcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1059',
            'codeSystemVersion': '2.1',
            'codeSystemName': 'Потенциально-опасные для здоровья социальные факторы',
            'current_entry': 2,
        }
        self.dfcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.dfcode["codeSystem"]}_{self.dfcode["codeSystemVersion"]}.xlsx')

        self.dpcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1060',
            'codeSystemVersion': '2.1',
            'codeSystemName': 'Профессиональные вредности для учета сигнальной информации о пациенте',
            'current_entry': 3,
        }
        self.dpcode['code_path'] = os.path.join(path_to_codes,
                                                f'{self.dpcode["codeSystem"]}_{self.dpcode["codeSystemVersion"]}.xlsx')

        self.wlcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1042',
            'codeSystemVersion': '3.2',
            'codeSystemName': 'Признак жителя города или села',
            'current_entry': 4,
        }
        self.wlcode['code_path'] = os.path.join(path_to_codes,
                                                f'{self.wlcode["codeSystem"]}_{self.wlcode["codeSystemVersion"]}.xlsx')

        self.zcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1038',
            'codeSystemVersion': '13.2',
            'codeSystemName': 'Занятость (социальные группы) населения',
            'current_entry': 5,
        }
        self.zcode['code_path'] = os.path.join(path_to_codes,
                                                f'{self.zcode["codeSystem"]}_{self.zcode["codeSystemVersion"]}.xlsx')

        self.vpcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1058',
            'codeSystemVersion': '2.2',
            'codeSystemName': 'Вредные привычки и зависимости',
            'current_entry': 6,
        }
        self.vpcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.vpcode["codeSystem"]}_{self.vpcode["codeSystemVersion"]}.xlsx')
        self.lcode['code_table'] = open_code(self.lcode['code_path'])
        self.icode['code_table'] = open_code(self.icode['code_path'])
        self.tcode['code_table'] = open_code(self.tcode['code_path'])
        self.dfcode['code_table'] = open_code(self.dfcode['code_path'])
        self.dpcode['code_table'] = open_code(self.dpcode['code_path'])
        self.wlcode['code_table'] = open_code(self.wlcode['code_path'])
        self.zcode['code_table'] = open_code(self.zcode['code_path'])
        self.vpcode['code_table'] = open_code(self.vpcode['code_path'])

        self.current_socstate = 0
        self.current_addicstate = 0

    def change_form(self, i, max_width):
        """cheate form for change vit params
        шифр: выбираем из каталога в коде заболевания (будет выбор болезни)
        тип: из кодов
        текст: описание"""
        if not st.session_state['rewrite']:
            st.text_input('Заголовок', value='', key=0)
            st.text_area('Описание', '', height=300, key=1)
        else:
            st.selectbox('Занятость', self.parse_code(self.zcode, 'NAME'), key=0)
            st.multiselect('Льготная категория', self.parse_code(self.lcode, 'Полное название категории льготы '), default=None, key=1)
            st.selectbox('Инвалидность', self.parse_code(self.icode, 'NAME'), key=2)
            st.selectbox('Порядок установления инвалидности', self.parse_code(self.tcode, 'NAME'), key=3)
            st.multiselect('Социальные факторы и профессиональные вредности', self.parse_code(self.dpcode, 'NAME'), default=None, key=4)
            st.multiselect('Потенциально-опасные для здоровья социальные факторы', self.parse_code(self.dfcode, 'NAME'), default=None, key=5)
            st.multiselect('Зависимости', self.parse_code(self.vpcode, 'NAME'), default=None, key=6)
            st.selectbox('Местность регистрации', self.parse_code(self.wlcode, 'NAME'), key=7)

    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_text(self):
        """Create new text with lists and paragraphs and fill them data"""

        if not st.session_state['rewrite']:
            self.change_part_text()
            return None

        self.text.clear()
        for entry in self.entry.find_all('entry'):
            entry.extract()

        if st.session_state['0'] != '':
            link = f'socanam{self.current_socstate}'
            self.current_socstate += 1
            list = self.create_new_list('Занятость', listType="unordered")
            self.append_new_item(list, st.session_state['0'], link)
            self.text.append(list)

            entry = self.create_new_entry()
            self.change_entry(entry, st.session_state['0'], 0, link)
            self.entry.append(entry)

        if len(st.session_state['1']) != 0:
            list = self.create_new_list('Льготная категория', listType="unordered", ID="priveleges")
            for current_item in st.session_state['1']:
                entry = self.create_new_entry()
                link = f'socanam{self.current_socstate}'
                self.append_new_item(list, current_item, link)
                self.change_entry(entry, current_item, 1, link)
                self.current_socstate += 1
                self.entry.append(entry)

            self.text.append(list)

        if st.session_state['2'] != '':
            link = f'socanam{self.current_socstate}'
            self.current_socstate += 1
            list = self.create_new_list('Инвалидность', listType="unordered", ID="invalid")
            self.append_new_item(list, st.session_state['2'], link)
            self.text.append(list)

            entry = self.create_new_entry()
            self.change_entry(entry, st.session_state['2'], 2, link)

            self.entry.append(entry)

        if len(st.session_state['4']) != 0 or len(st.session_state['5']) != 0:
            list = self.create_new_list('Социальные факторы и профессиональные вредности', listType="unordered")

            for current_item in st.session_state['4']:
                entry = self.create_new_entry()
                link = f'socanam{self.current_socstate}'
                self.append_new_item(list, current_item, link)
                self.change_entry(entry, current_item, 4, link)
                self.current_socstate += 1
                self.entry.append(entry)

            for current_item in st.session_state['5']:
                entry = self.create_new_entry()
                link = f'socanam{self.current_socstate}'
                self.append_new_item(list, current_item, link)
                self.change_entry(entry, current_item, 5, link)
                self.current_socstate += 1
                self.entry.append(entry)

            self.text.append(list)

        if len(st.session_state['6']) != 0:
            list = self.create_new_list('Зависимости')

            for current_item in st.session_state['6']:
                entry = self.create_new_entry()
                link = f'addic{self.current_addicstate}'
                self.append_new_item(list, current_item, link)
                self.change_entry(entry, current_item, 6, link)
                self.current_addicstate += 1
                self.entry.append(entry)

            self.text.append(list)

        if st.session_state['7'] != '':
            link = f'socanam{self.current_socstate}'
            self.current_socstate += 1

            entry = self.create_new_entry()
            self.change_entry(entry, st.session_state['7'], 7, link)

            self.entry.append(entry)

    def change_part_text(self):
        if st.session_state['0'] != '' and st.session_state['1'] != '':
            paragraph = self.content.new_tag('paragraph')
            caption = self.content.new_tag('caption')
            caption.string = st.session_state['0']
            content = self.content.new_tag('content')
            content.string = st.session_state['1']
            paragraph.append(caption)
            paragraph.append(content)
            self.text.append(paragraph)

    def get_row(self, val, id_name, col, table_path):
        table = table_path['code_table']
        print(table.columns)
        row = table[table[col] == val][[id_name, col]]
        return row

    def change_entry(self, entry, val, state, link=None, text=None):
        """Изменяем существующие поля"""
        if state == 0:
            current_code = self.zcode
            ID = 'ID'
            NAME = 'NAME'
        if state == 1:
            current_code = self.lcode
            ID = 'Код '
            NAME = 'Полное название категории льготы '
        if state == 2:
            current_code = self.icode
            ID = 'ID'
            NAME = 'NAME'
        if state == 4:
            current_code = self.dpcode
            ID = 'ID'
            NAME = 'NAME'
        if state == 5:
            current_code = self.dfcode
            ID = 'ID'
            NAME = 'NAME'
        if state == 6:
            current_code = self.vpcode
            ID = 'ID'
            NAME = 'NAME'
        if state == 7:
            current_code = self.wlcode
            ID = 'ID'
            NAME = 'NAME'

        obs, code = self.append_new_observation(entry, link)
        self.fill_new_observation(obs, code, ID, NAME, val, current_code, text)

        if state == 2 and st.session_state['3'] != '':
            current_code = self.tcode
            ID = 'ID'
            NAME = 'NAME'
            val = st.session_state['3']
            qualifier = self.content.new_tag('qualifier')
            value = self.content.new_tag('value')

            self.fill_new_observation(obs, value, ID, NAME, val, current_code)
            qualifier.append(value)
            code.append(qualifier)

    def create_new_list(self, title, **attrs):
        list = self.content.new_tag('list', **attrs)
        caption = self.content.new_tag('caption')
        caption.string = title
        list.append(caption)
        return list

    def append_new_item(self, list, val, link):
        item = self.content.new_tag('item')
        content = self.content.new_tag('content', ID=link)
        content.string = val
        item.append(content)
        list.append(item)

    def create_new_entry(self):
        entry = self.content.new_tag('entry')
        return entry

    def append_new_observation(self, entry, link=None):
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        code = self.content.new_tag('code')
        observation.append(code)

        if link:
            linktext = self.content.new_tag('originalText')
            linkfield = self.content.new_tag('reference', value=f'#{link}')
            linktext.append(linkfield)
            code.append(linktext)
        entry.append(observation)
        return observation, code

    def fill_new_observation(self, obs, code, ID, NAME, val, current_code, text=None):

        row = self.get_row(val, ID, NAME, current_code)
        fill_code(code, row, current_code['codeSystem'], current_code['codeSystemVersion'],
                  current_code['codeSystemName'])

        if text:
            textfield = self.content.new_tag('text')
            textfield.string = text
            obs.append(textfield)


class LAB_PARAMS:
    def __init__(self, _content=None, _table=None, _number_table=None):
        """Заполняем новую таблицу с данными
        показатель: из кодов
        значение: пишем
        ед. изм.: из кодов
        референтный диапазо: пишем в виде (low - high)
        материал исследования: берем из кодов
        кол-во материала исследования: пишем
        ед. изм. материала исследования: вроде берем из кодов но если что пишем
        оборудование: может уберем
        исполнитель: уберем может"""

        self.content = _content
        self.table = _table
        if _number_table is not None:
            try:
                self.entry = _table.parent.parent.find_all('entry')[_number_table]
            except IndexError:
                self.entry = None

        self.pcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1080',
            'codeSystemVersion': '3.40',
            'codeSystemName': 'Федеральный справочник лабораторных исследований. Справочник лабораторных тестов'
        }

        self.mcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1081',
            'codeSystemVersion': '3.1',
            'codeSystemName': 'Федеральный справочник лабораторных исследований. Справочник лабораторных материалов и образцов'
        }

        self.bcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1061',
            'codeSystemVersion': '2.3',
            'codeSystemName': 'Группы крови для учета сигнальной информации о пациенте'

        }

        self.pcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.pcode["codeSystem"]}_{self.pcode["codeSystemVersion"]}.xlsx')
        self.mcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.mcode["codeSystem"]}_{self.mcode["codeSystemVersion"]}.xlsx')
        self.bcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.bcode["codeSystem"]}_{self.bcode["codeSystemVersion"]}.xlsx')
        self.pcode['code_table'] = open_code(self.pcode['code_path'])
        self.mcode['code_table'] = open_code(self.mcode['code_path'])
        self.bcode['code_table'] = open_code(self.bcode['code_path'])


    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]


    def change_form(self, i, max_width):
        """Форма будет для добавления новой таблицы в xml код добавляем в text и создаем ему нужный entry
        показатель: из кодов
        значение: пишем
        ед. изм.: из кодов
        референтный диапазо: пишем в виде (low - high)
        материал исследования: берем из кодов
        кол-во материала исследования: пишем
        ед. изм. материала исследования: вроде берем из кодов но если что пишем
        дата: пишем так
        оборудование: может уберем
        исполнитель: уберем может"""

        state = st.session_state['state_write_field']

        if state == 'исследование':
            st.selectbox('Показатель', self.parse_code(self.pcode, 'FULLNAME'), key=0)
            st.text_input('Значение', value='', key=1)
            st.text_input('Референтный диапазон вида "low value - high value"', value='', key=2)
            st.selectbox('Материал исследования', self.parse_code(self.mcode, 'SPECIMEN'), key=3)
            st.text_input('Кол-во материала', value='', key=4)
            st.text_input('Единица измерения материала', value='', key=5)
            st.text_input('Дата', value='', key=6)
        if state == 'примечание':
            st.text_input('Примечание', value='', key=0)
            st.text_input('Дата', value='', key=1)
        if state == 'результат':
            st.text_input('Результат', value='', key=0)
            st.text_input('Дата', value='', key=1)

    def get_row(self, val, NAME, table_path, *args):
        table = table_path['code_table']
        print(table.columns)
        row = table[table[NAME] == val][[*args, NAME]]
        return row

    def create_new_table(self, name_table):
        new_table = self.content.new_tag('table', width="100%")
        new_head = self.content.new_tag('thead')
        new_row = self.content.new_tag('tr')
        cols = [28, 20, 18, 21, 13]
        names = ['Показатель', "Значение", "Единицы измерения", "Референтный диапазон", "Дата"]
        for j, name in zip(cols, names):
            new_col = self.content.new_tag('col', width=f'{j}%')
            new_table.append(new_col)

            new_name = self.content.new_tag('th')
            new_name.string = name
            new_row.append(new_name)
        new_head.append(new_row)
        new_table.append(new_head)

        new_body = self.content.new_tag('tbody')
        new_row_title = self.content.new_tag('tr')
        new_title = self.content.new_tag('td', colspan='5')
        new_content = self.content.new_tag('content', styleCode="Bold")
        new_content.string = name_table
        new_title.append(new_content)
        new_row_title.append(new_title)
        new_body.append(new_row_title)
        new_table.append(new_body)

        self.table.append(new_table)
        self.table.parent.append(self.content.new_tag('entry'))

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            return
        state = st.session_state['state_write_field']
        if state == 'исследование':
            changes = [st.session_state[f'{i}'] for i in range(7)]
        else:
            changes = [st.session_state[f'{i}'] for i in range(2)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
            is_new = False
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
            is_new = True
        if state == 'исследование':
            unit_row = self.get_row(st.session_state['0'], 'FULLNAME', self.pcode, 'UNIT', 'GROUP')
            print(unit_row)
            unit, group, _ = [x for x in unit_row.values[0, :]]
            unit = str(unit)
            try:
                unit = unit.split(';')[0].split(' ')
                unit = ''.join(unit)
            except:
                unit = unit.split(' ')
                unit = ''.join(unit)
            views_fields = [changes[0], changes[1], unit, changes[2], changes[6]]
            for cell in views_fields:
                new_cell = self.content.new_tag('td')
                new_cell.string = f'{cell}'
                row.append(new_cell)

            if i != 0:
                self.change_entry(i - 1, changes + [unit, group], is_new)
        if state == 'примечание':
            new_text = self.content.new_tag('td', colspan='4')
            new_content = self.content.new_tag('content', styleCode="Italics")
            new_content.string = "Примечание" + changes[0]
            new_text.append(new_content)
            row.append(new_text)

            new_date = self.content.new_tag('td')
            new_date.string = changes[1]
            row.append(new_date)
            if i != 0:
                self.change_entry(i - 1, changes, is_new)
        if state == 'результат':
            new_text = self.content.new_tag('td', colspan='5')
            new_content = self.content.new_tag('content', styleCode="Bold")
            new_content.string = 'Заключение:'
            new_text.append(new_content)
            new_text.append(changes[0])
            row.append(new_text)
            if i != 0:
                self.change_entry(i - 1, changes, is_new)



    def change_entry(self, i, changes, is_new=False):

        state = st.session_state['state_write_field']

        big_organizer = self.entry.find('organizer')
        if big_organizer is None:
            big_organizer = self.create_big_organizer()
        is_result, is_research = False, False

        try:
            result_component = big_organizer.find('act').find('code', code='901')
            if result_component:
                is_result = True
        except AttributeError:
            result_component = None
        try:
            research_component = big_organizer.find('organizer', classCode="BATTERY", moodCode="EVN").parent
            if research_component:
                is_research = True
        except AttributeError:
            research_component = None


        if state == 'результат':
            if not is_result:
                result_component = self.create_big_component(big_organizer)
                big_organizer.append(result_component)

            result_component.clear()
            new_act = self.create_act(state, *changes)
            result_component.append(new_act)
        else:
            if not is_research:
                research_component = self.create_big_component(big_organizer)
                min_organizer = self.create_min_organizer(GROUP=changes[8])
                research_component.append(min_organizer)


            min_organizer = research_component.find('organizer')
            # if state == 'исследование':
            #     if min_organizer.find('code').find('originalText').string != changes[8]:
            #         st.error(f'''Пожайлуста используйте лабораторные исследования одной группы:
            #                 {min_organizer.find('code').find('originalText').string} не равен  {changes[8]}''')
            #         return None
            if is_new:
                min_component = self.create_min_component()
                min_organizer.append(min_component)
            else:
                min_component = min_organizer.find_all('component')[i]
                min_component.clear()

            if state == 'исследование':
                new_observation = self.create_observation(changes)
                min_component.append(new_observation)
            else:
                new_act = self.create_act(state, *changes)
                min_component.append(new_act)




    def create_big_organizer(self):
        organizer = self.content.new_tag('organizer', classCode="CLUSTER", moodCode="EVN")

        statusCode = self.content.new_tag('statusCode', code='completed')
        reference = self.content.new_tag('reference', typeCode='REFR')

        ex_doc = self.content.new_tag('externalDocument')
        ex_doc_id = self.content.new_tag('id', root="1.2.643.5.1.13.13.12.2.77.8481.100.1.1.51", extension="Данные скрыты")
        ex_doc.append(ex_doc_id)
        reference.append(ex_doc)

        organizer.append(statusCode)
        organizer.append(reference)

        self.entry.append(organizer)
        return organizer

    def create_min_organizer(self, GROUP):
        organizer = self.content.new_tag('organizer', classCode="BATTERY", moodCode="EVN")

        code = self.content.new_tag('code')
        originalText = self.content.new_tag('originalText')
        originalText.string = GROUP
        code.append(originalText)

        statusCode = self.content.new_tag('statusCode', code='completed')
        organizer.append(code)
        organizer.append(statusCode)
        return organizer

    def create_observation(self, changes):
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        code = self.content.new_tag('code')
        pcode_row = self.get_row(changes[0], 'FULLNAME', self.pcode, 'ID')
        fill_code(code, pcode_row, self.pcode['codeSystem'], self.pcode['codeSystemVersion'], self.pcode['codeSystemName'])

        observation.append(code)

        observation.append(self.content.new_tag('statusCode', code='completed'))
        observation.append(self.content.new_tag('effectiveTime', value=self.change_time(changes[6])))
        value = self.content.new_tag('value')
        try:
            float(changes[1])
            value['xsi:type'] = 'PQ'
            value['value'] = changes[1]
            value['unit'] = changes[7]
        except:
            value['xsi:type'] = 'ST'
            value.string = changes[1]

        observation.append(value)

        ref_int = changes[2]
        if ref_int != '':
            interpretationCode = self.content.new_tag('interpretationCode')
            ref_int_mas = [float(val) for val in ref_int.split(' - ')]
            if float(changes[1]) > ref_int_mas[1]:
                interpretationCode['code'] = 'H'
            elif float(changes[1]) < ref_int_mas[0]:
                interpretationCode['code'] = 'L'
            else:
                interpretationCode['code'] = 'N'  # !!!!!!!!!! срочно потом ухнать настоящие коды другие
            observation.append(interpretationCode)

        speciment = self.content.new_tag('specimen')

        specimentRole = self.content.new_tag('specimenRole')
        speciment_id = self.content.new_tag('id', root="1.2.643.5.1.13.13.12.2.77.8481.100.1.1.66", extension="124562156")
        specimentRole.append(speciment_id)

        specimenPlayingEntity = self.content.new_tag('specimenPlayingEntity', classCode="ENT", determinerCode="INSTANCE")
        speciment_code = self.content.new_tag('code')
        mcode_row = self.get_row(changes[3], 'SPECIMEN', self.mcode, 'ID', 'MATTER')
        MATTER = mcode_row['MATTER'].values[0]
        print('MATTER -- > ', MATTER)
        fill_code(speciment_code, mcode_row[['ID', 'SPECIMEN']], self.mcode['codeSystem'], self.mcode['codeSystemVersion'],
                  self.mcode['codeSystemName'])

        specimenPlayingEntity.append(speciment_code)

        if changes[4] != '' and changes[5] != '':
            speciment_quantity = self.content.new_tag('quantity', value=changes[4], unit=changes[5])
            specimenPlayingEntity.append(speciment_quantity)

        speciment_desc = self.content.new_tag('desc')
        speciment_desc.string = MATTER
        specimenPlayingEntity.append(speciment_desc)

        specimentRole.append(specimenPlayingEntity)
        speciment.append(specimentRole)
        observation.append(speciment)

        ref_int = changes[2]
        if ref_int != '':
            referance_range = self.content.new_tag('referenceRange')
            observationRange = self.content.new_tag('observationRange')

            ref_text = self.content.new_tag('text')
            ref_text.string = changes[2]

            ref_vals = self.content.new_tag('value')
            ref_vals['xsi:type'] = 'IVL_PQ'
            low_val = self.content.new_tag('low', value=ref_int_mas[0], unit=changes[7])
            high_val = self.content.new_tag('high', value=ref_int_mas[1], unit=changes[7])
            ref_vals.append(low_val)
            ref_vals.append(high_val)
            observationRange.append(ref_vals)
            observationRange.append(self.content.new_tag('interpretationCode', code="N")) # 1!!!!!!!!
            referance_range.append(observationRange)


            observation.append(referance_range)
        return observation


    def create_act(self, state, text_str, time):
        act = self.content.new_tag('act', classCode="ACT", moodCode="EVN")
        if state == 'примечание':
            code = self.content.new_tag('code', code="900", codeSystem="1.2.643.5.1.13.13.11.1380",
                                        codeSystemVersion="1.1",  codeSystemName="Кодируемые поля CDA документов",
                                        displayName="Текстовое примечание к лабораторному исследованию")
        if state == 'результат':
            code = self.content.new_tag('code', code="901", codeSystem="1.2.643.5.1.13.13.11.1380",
                                        codeSystemVersion="1.1", codeSystemName="Кодируемые поля CDA документов",
                                        displayName="Текстовое заключение по проведенным лабораторным исследованиям")
        act.append(code)
        text = self.content.new_tag('text')
        text.string = text_str
        act.append(text)

        author = self.content.new_tag('author')
        author.append(self.content.new_tag('time', value=self.change_time(time)))
        assignedAuthor = self.content.new_tag('assignedAuthor')
        assignedAuthor.append(self.content.new_tag('id', root='1.2.643.5.1.13.13.12.2.77.8481.100.1.1.51', extension='Данные скрыты'))
        assignedAuthor.append(self.content.new_tag('id', root='1.2.643.5.1.13.13.12.2.77.8481.100.1.1.51', extension='Данные скрыты'))
        assignedAuthor.append(self.content.new_tag('code', code="35", codeSystem="1.2.643.5.1.13.13.11.1002",
                                                   codeSystemVersion="2.2",
                                                   codeSystemName="Должности работников организаций медицинского и фармацевтического профиля",
                                                   displayName="врач клинической лабораторной диагностики"))
        author.append(assignedAuthor)
        act.append(author)
        return act

    def create_big_component(self, observation):
        component = self.content.new_tag('component')
        observation.append(component)
        return component

    def create_min_component(self):
        component = self.content.new_tag('component')
        return component

    def change_time(self, time):
        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)
        return time


class CONSULT_PARAMS:
    def __init__(self, _content, _table):

        self.content = _content
        self.table = _table
        self.entry = _table.parent.parent.find_all('entry')

        self.rcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1066',
            'codeSystemVersion': '5.4',
            'codeSystemName': 'Номенклатура специальностей специалистов со средним, высшим и послевузовским медицинским и фармацевтическим образованием в сфере здравоохранения'
        }
        self.pcode = {
            'codeSystem': '1.2.643.5.1.13.13.99.2.258',
            'codeSystemVersion': '1.1',
            'codeSystemName': 'Справочник приоритетов'
        }
        self.scode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1070',
            'codeSystemVersion': '2.10',
            'codeSystemName': 'Номенклатура медицинских услуг'
        }
        self.spcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1006',
            'codeSystemVersion': '2.3',
            'codeSystemName': 'Степень тяжести состояния пациента'
        }
        self.npcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1005',
            'codeSystemVersion': '2.21',
            'codeSystemName': 'Международная классификация болезней и состояний, связанных со здоровьем 10 пересмотра. Версия 4'
        }
        self.mkbcode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1005',
            'codeSystemVersion': '2.21',
            'codeSystemName': 'Международная классификация болезней и состояний, связанных со здоровьем 10 пересмотра. Версия 4'
        }
        self.rescode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1009',
            'codeSystemVersion': '2.5',
            'codeSystemName': 'Виды медицинских направлений'
        }

        self.rcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.rcode["codeSystem"]}_{self.rcode["codeSystemVersion"]}.xlsx')
        self.pcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.pcode["codeSystem"]}_{self.pcode["codeSystemVersion"]}.xlsx')
        self.scode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.scode["codeSystem"]}_{self.scode["codeSystemVersion"]}.xlsx')
        self.spcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.spcode["codeSystem"]}_{self.spcode["codeSystemVersion"]}.xlsx')
        self.npcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.npcode["codeSystem"]}_{self.npcode["codeSystemVersion"]}.xlsx')
        self.mkbcode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.mkbcode["codeSystem"]}_{self.mkbcode["codeSystemVersion"]}.xlsx')
        self.rescode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.rescode["codeSystem"]}_{self.rescode["codeSystemVersion"]}.xlsx')
        self.rcode['code_table'] = open_code(self.rcode['code_path'])
        self.pcode['code_table'] = open_code(self.pcode['code_path'])
        self.scode['code_table'] = open_code(self.scode['code_path'])
        self.spcode['code_table'] = open_code(self.spcode['code_path'])
        self.npcode['code_table'] = open_code(self.npcode['code_path'])
        self.mkbcode['code_table'] = open_code(self.mkbcode['code_path'])
        self.rescode['code_table'] = open_code(self.rescode['code_path'])

    def change_form(self, i, max_width):
        """Форфма для добавления нового поля в конслуьтации врачей
        дата: вводим
        исследование(врач - направление): коды  1.2.643.5.1.13.13.11.1066
        приоритет: коды 1.2.643.5.1.13.13.11.1377
        результаты: пишем
        оказаная услуга: коды 1.2.643.5.1.13.13.11.1070
        состояние пациента: коды 1.2.643.5.1.13.13.11.1006
        протокол консультации: коды 1.2.643.5.1.13.13.11.1380 но пишем сюда текст
        заключение консультации: коды 1.2.643.5.1.13.13.11.1380 но пишем сюда текст
        рекомендации: коды 1.2.643.5.1.13.13.11.1380 но пишем сюда текст
        выявленные патологии: коды 1.2.643.5.1.13.13.11.1005
        шифр по Шифр по МКБ-10: коды 1.2.643.5.1.13.13.11.1005
        результат консультации: коды 1.2.643.5.1.13.13.11.1009
        """
        if i == 0:
            return None
        st.text_input('Дата', value='', key=0)
        st.selectbox('Исследование', self.parse_code(self.rcode, 'NAME'), key=1)
        st.text_input('Результат полный ', value='', key=2)
        st.selectbox('Приоритет', self.parse_code(self.pcode, 'NAME'), key=3)
        st.selectbox('Оказаная услуга', self.parse_code(self.scode, 'NAME'), key=4)
        st.selectbox('Состояние пациента', self.parse_code(self.spcode, 'NAME'), key=5)
        st.text_input('Протокол консультации', value='', key=6)
        st.text_input('Заключение консультации', value='', key=7)
        st.text_input('Рекомендации', value='', key=8)
        st.selectbox('Выявленные патологии', self.parse_code(self.npcode, 'MKB_NAME'), key=9)
        st.selectbox('Шифр по МКБ(выберите конкретную патологию)', self.parse_code(self.mkbcode, 'MKB_NAME'), key=10)
        st.selectbox('Результат консультации', self.parse_code(self.rescode, 'NAME'), key=11)

    def get_row(self, val, NAME, table_path, *args):
        table = table_path['code_table']
        print(table.columns)
        row = table[table[NAME] == val][[*args, NAME]]
        return row

    def parse_code(self, code, col):
        """Parse code like pandas dataframe"""
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            return None
        changes = [st.session_state[f'{i}'] for i in range(12)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        tag = 'td'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
            is_new = False
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
            is_new = True
        for j, cell in enumerate(changes[:3]):
            new_cell = self.content.new_tag(tag)
            new_cell.string = cell
            row.append(new_cell)
        self.change_entry(i, changes, is_new)

    def change_entry(self, i, changes, is_new):
        if is_new:
            entry = self.content.new_tag('entry')
            self.table.parent.parent.append(entry)
        else:
            entry = self.entry[i-1]

        entry.clear()
        observation = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        entry.append(observation)

        code = self.append_code('code', changes[1], 'ID', 'NAME', self.rcode)
        observation.append(code)
        observation.append(self.content.new_tag('statusCode', code="completed"))
        observation.append(self.content.new_tag('effectiveTime', value=self.change_time(changes[0])))
        res_value = self.content.new_tag('value')
        res_value['xsi:type'] = 'ST'
        res_value.string = changes[2]
        observation.append(res_value)

        med_service = self.append_entryRelationship(observation, True, typeCode="REFR", inversionInd="false")
        med_service_code = self.append_code('code', changes[4], 'ID', 'NAME', self.scode)
        med_service.append(med_service_code)
        med_service.append(self.content.new_tag('effectiveTime', value=self.change_time(changes[0])))

        if changes[5] != '':
            state_patient = self.append_entryRelationship(observation, False, typeCode="COMP")
            state_patient_code = self.append_code('code', changes[5], 'ID', 'NAME', self.spcode)
            state_patient_text = self.content.new_tag('originalText')
            state_patient_text.string = '-'
            state_patient_code.append(state_patient_text)
            state_patient.append(state_patient_code)

        if changes[6] != '':
            protocol_consultation = self.append_entryRelationship(observation, False, typeCode="COMP")
            protocol_consultation_code = self.append_code2("806", "Заключение консультации")
            protocol_consultation.append(protocol_consultation_code)
            protocol_consultation_text = self.content.new_tag('text')
            protocol_consultation_text.string = '-'
            protocol_consultation.append(protocol_consultation_text)
            protocol_consultation_value = self.content.new_tag('value')
            protocol_consultation_value['xsi:type'] = "ST"
            protocol_consultation_value.string = changes[6]
            protocol_consultation.append(protocol_consultation_value)

        if changes[7] != '':
            result_consultation = self.append_entryRelationship(observation, False, typeCode="COMP")
            result_consultation_code = self.append_code2("805", "Протокол консультации")
            result_consultation.append(result_consultation_code)
            result_consultation_text = self.content.new_tag('text')
            result_consultation_text.string = '-'
            result_consultation.append(result_consultation_text)
            result_consultation_value = self.content.new_tag('value')
            result_consultation_value['xsi:type'] = "ST"
            result_consultation_value.string = changes[7]
            result_consultation.append(result_consultation_value)

        if changes[8] != '':
            recomendations = self.append_entryRelationship(observation, False, typeCode="COMP")
            recomendations_code = self.append_code2("807", "Рекомендации")
            recomendations.append(recomendations_code)
            recomendations_text = self.content.new_tag('text')
            recomendations_text.string = '-'
            recomendations.append(recomendations_text)
            recomendations_value = self.content.new_tag('value')
            recomendations_value['xsi:type'] = "ST"
            recomendations_value.string = changes[8]
            recomendations.append(recomendations_value)

        if changes[9] != '':
            patologies = self.append_entryRelationship(observation, False, typeCode="COMP")
            patologies_code = self.append_code2("808", "Выявленные патологии")
            patologies.append(patologies_code)

            patologies_value = self.append_code('value', changes[9], 'MKB_CODE', 'MKB_NAME', self.npcode)
            patologies_value['xsi:type'] = "CD"
            patologies_text = self.content.new_tag('originalText')
            patologies_text.string = '-'
            patologies_value.append(patologies_text)
            patologies.append(patologies_value)

        if changes[10] != '':
            cyphers = self.append_entryRelationship(observation, False, typeCode="COMP")
            cyphers_code = self.append_code2("809", "Шифр по МКБ-10")
            cyphers.append(cyphers_code)

            cyphers_value = self.append_code('value', changes[10], 'MKB_CODE', 'MKB_NAME', self.mkbcode)
            cyphers_value['xsi:type'] = "CD"
            cyphers_text = self.content.new_tag('originalText')
            cyphers_text.string = '-'
            cyphers_value.append(cyphers_text)
            cyphers.append(cyphers_value)

        if changes[11] != '':
            results = self.append_entryRelationship(observation, False, typeCode="COMP")
            results_code = self.append_code2("810", "Результат консультации")
            results.append(results_code)

            results_value = self.append_code('value', changes[11], 'ID', 'NAME', self.rescode)
            results_value['xsi:type'] = "CD"
            results_text = self.content.new_tag('originalText')
            results_text.string = '-'
            results_value.append(results_text)
            results.append(results_value)

    def append_code(self, tag, val, ID, NAME, current_code):
        code = self.content.new_tag(tag)
        row = self.get_row(val, NAME, current_code, ID)

        fill_code(code, row, current_code['codeSystem'], current_code['codeSystemVersion'], current_code['codeSystemName'])
        return code

    def append_code2(self, ID, NAME):
        code = self.content.new_tag('code')
        code['code'] = ID
        code['displayName'] = NAME
        code['codeSystem'] = "1.2.643.5.1.13.13.11.1380"
        code['codeSystemVersion'] = "1.1"
        code['codeSystemName'] = "Кодируемые поля CDA документов"
        return code

    def append_entryRelationship(self, observation, act_or_obs, **kwargs):
        entryRelationship = self.content.new_tag('entryRelationship', **kwargs)
        if act_or_obs:
            content = self.content.new_tag('act', classCode="ACT", moodCode="EVN")
        else:
            content = self.content.new_tag('observation', classCode="OBS", moodCode="EVN")
        entryRelationship.append(content)
        observation.append(entryRelationship)
        return content

    def change_time(self, time):
        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)
        return time


class RECOM_PARAMS:
    def __init__(self, _content, _text, _entry=None):
        """Поля хранящиеся в кодах
        Дата:
        Шкала:
        Результаты подсчета:
        """
        self.content = _content
        self.text = _text
        self.codes_table = None

    def change_form(self, i, max_width):
        """cheate form for change vit params
        параметр: выбираем из каталога
        ед. измерения: пишем так
        даты: в них храняться значения"""
        st.text_input('Рекомендации', value='', key=0)

    def change_text(self):
        changes = st.session_state['0']
        print(changes)

        if changes == '':
            return None
        new_text = self.content.new_tag('text')
        new_text.string = changes
        self.text.replace_with(new_text)


class SERVICE_PARAM:
    def __init__(self, content, table):
        self.content = content
        self.table = table
        self.entry = table.parent.parent.find_all('entry')

        self.scode = {
            'codeSystem': '1.2.643.5.1.13.13.11.1070',
            'codeSystemVersion': '2.10',
            'codeSystemName': 'Номенклатура медицинских услуг'
        }
        self.scode['code_path'] = os.path.join(path_to_codes,
                                               f'{self.scode["codeSystem"]}_{self.scode["codeSystemVersion"]}.xlsx')
        self.scode['code_table'] = open_code(self.scode['code_path'])

    def change_form(self, i, max_width):
        """cheate form for change vit params
        шифр: выбираем из каталога в коде заболевания (будет выбор болезни)
        тип: из кодов
        текст: описание"""
        if i == 0:
            for j in range(max_width + 1):
                st.text_input(label=f'cell {j}', value='', key=f'{j}')
        else:
            st.text_input('дата', value='', key=0)
            st.selectbox('услуга', self.parse_code(self.scode, 'NAME'), key=1)


    def parse_code(self, code, col):
        code_dtf = code['code_table']
        print('-->', code_dtf.columns)
        return [''] + [name for name in code_dtf[col]]

    def change_cell(self, i, max_height, max_width):
        """Change exist cell in current table"""
        if i == 0:
            return None
        else:
            changes = [st.session_state[f'{i}'] for i in range(2)]
        print(changes)
        empty_changes = True
        for change in changes:
            if change != '':
                empty_changes = False
        if empty_changes:
            return None
        S_CODE, _ = [x for x in self.get_row(changes[1], 'S_CODE', 'NAME', self.scode).values[0, :]]
        changes.append(S_CODE)
        if i != 0:
            tag = 'td'
        else:
            tag = 'th'
        if i <= max_height:
            row = self.table.find('tbody').find_all('tr')[i]
            row.clear()
        else:
            row = self.content.new_tag('tr')
            self.table.find('tbody').append(row)
        for j, cell in enumerate(changes[:3]):
            new_cell = self.content.new_tag(tag)
            new_cell.string = cell
            row.append(new_cell)
        if i != 0:
            self.change_entry(i, max_height)

    def get_row(self, val, id_name, col, table_path):
        table = table_path['code_table']
        print(table.columns)
        row = table[table[col] == val][[id_name, col]]
        return row

    def change_entry(self, i, max_height):
        """Изменяем существующие поля"""

        """Изменяем существующие поля"""

        try:
            entry = self.entry[i-1]
            entry.clear()
        except:
            entry = self.content.new_tag('entry')
            self.table.parent.parent.append(entry)

        act = self.content.new_tag('act', classCode="ACT", moodCode="EVN")
        entry_code = self.content.new_tag('code')
        fill_code(entry_code, self.get_row(st.session_state['1'], 'S_CODE', 'NAME', self.scode),
                  self.scode['codeSystem'], self.scode['codeSystemVersion'], self.scode['codeSystemName'])
        ef_time = self.content.new_tag('effectiveTime', value=self.change_time(st.session_state['0']))
        act.append(entry_code)
        act.append(ef_time)
        entry.append(act)

    def change_time(self, time):
        time = ''.join([word for word in time.replace('\n', '').split(' ') if word != ''])
        time = time.split('.')[::-1]
        time = ''.join(time) + '1010+0000'
        print(time)
        return time

