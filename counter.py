import pandas as pd
import os

csv_file = os.path.abspath('codes.csv')

dtf = pd.read_csv(csv_file)
print(dtf)

dtf.to_excel('codes.xlsx')

