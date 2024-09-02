import pandas as pd


# Прочитаем CSV файл в DataFrame
file_path = './reports/df_result_sql.csv'
df_result_sql = pd.read_csv(file_path)


for строка in df_result_sql.iterrows():
    print(f"rsm_obj_to_create_under: {строка[1]['rsm_obj_to_create_under']}")
    print(f"service_group: {строка[1]['service_group']}")
    print(f"name: {строка[1]['name']}")

