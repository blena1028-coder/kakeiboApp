import streamlit as st
import pandas as pd

st.title("家計簿アプリ")
st.write("公開成功")

# quick_buttons.csv の内容を表示
try:
    quick_buttons_from_csv = pd.read_csv('quick_buttons.csv')
    st.subheader('quick_buttons.csv の内容')
    st.dataframe(quick_buttons_from_csv)
except FileNotFoundError:
    st.warning('quick_buttons.csv が見つかりませんでした。')
    # 空のデータフレームを表示
    empty_df = pd.DataFrame(columns=['名前', '金額'])
    st.dataframe(empty_df)
except Exception as e:
    st.error(f'予期しないエラー: {e}')
