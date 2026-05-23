import pandas as pd
from datetime import datetime
import ipywidgets as widgets
from IPython.display import display, clear_output

# =========================
# 入力者リスト (新機能: 負担者ごとの金額計算のため、dfの初期化前に定義)
# =========================
input_persons = ['あなた', 'パートナー', 'その他'] # ここで入力者の選択肢を定義

# =========================
# データ読込
# =========================

# 新しい負担額カラムを動的に生成
# 例: 'あなた_負担額', 'パートナー_負担額', 'その他_負担額'
dynamic_burden_cols = [f"{person}_負担額" for person in input_persons]
base_cols = [
    "日付",
    "カテゴリ",
    "金額",
    "メモ",
    "入力者",
]
all_df_cols = base_cols + dynamic_burden_cols

try:
    df = pd.read_csv("kakeibo.csv")
    # 既存のDFに新しい負担額カラムがない場合、追加して0.0で初期化
    for col in dynamic_burden_cols:
        if col not in df.columns:
            df[col] = 0.0
    # 既存の「負担者」カラムは不要になるため削除（もしあれば）
    if '負担者' in df.columns:
        df = df.drop(columns=['負担者'])

except:
    # ファイルが存在しない場合、新しいカラム構成でDataFrameを作成
    df = pd.DataFrame(columns=all_df_cols)
    # 新しく作成する場合もfloat型で初期化
    for col in dynamic_burden_cols:
        df[col] = df[col].astype(float)

try:
    button_df = pd.read_csv("quick_buttons.csv")
    # NaNや空の名前のボタンを除外してDataFrameをクリーンアップ
    button_df = button_df.dropna(subset=['名前'])
    button_df = button_df[button_df['名前'].str.strip() != '']
except:
    button_df = pd.DataFrame(columns=[
        "名前",
        "金額"
    ])

# =========================
# 保存関数
# =========================

def save_kakeibo():
    df.to_csv("kakeibo.csv", index=False)

def save_buttons():
    button_df.to_csv("quick_buttons.csv", index=False)

# =========================
# 出力エリア
# =========================

main_output = widgets.Output()
buttons_output = widgets.Output()
table_output = widgets.Output()

# =========================
# 支出入力UI
# =========================

person_selector = widgets.Dropdown(
    options=input_persons,
    value=input_persons[0],
    description='入力者:',
    disabled=False,
)

# 負担者リスト（入力者リストに「割り勘」を追加）
cost_bearer_options = [p for p in input_persons if p != 'その他'] + ['割り勘'] # 'その他'は個人ではないので除外

cost_bearer_selector = widgets.SelectMultiple(
    options=cost_bearer_options,
    value=[cost_bearer_options[0]], # SelectMultipleは初期値としてリストを期待
    description='負担者:',
    disabled=False,
)

category_input = widgets.Text(
    description="カテゴリ"
)

amount_input = widgets.IntText(
    description="金額"
)

memo_input = widgets.Text(
    description="メモ"
)

save_button = widgets.Button(
    description="支出登録",
    button_style="success"
)

# =========================
# ワンタップ設定UI
# =========================

quick_name = widgets.Text(
    description="名前"
)

quick_amount = widgets.IntText(
    description="金額"
)

quick_add_button = widgets.Button(
    description="ボタン追加",
    button_style="info"
)

# =========================
# 負担額計算ヘルパー関数
# =========================
def calculate_burden(total_amount, selected_bearers):
    """
    指定された金額と負担者選択に基づいて、各個人の負担額を計算します。
    :param total_amount: 支出の合計金額 (int)
    :param selected_bearers: cost_bearer_selectorで選択された負担者のリスト (list of str)
    :return: (負担額を格納した辞書, エラーメッセージ文字列) のタプル。エラーがない場合はNone
    """
    print(f"DEBUG: calculate_burden called with total_amount={total_amount}, selected_bearers={selected_bearers}")
    burden_values = {f"{person}_負担額": 0.0 for person in input_persons}

    has_split = '割り勘' in selected_bearers
    individuals_selected = [p for p in selected_bearers if p in input_persons]

    if has_split:
        print(f"DEBUG: '割り勘' is selected. Individuals selected alongside: {individuals_selected}")
        # Case 1: '割り勘' is selected
        # If '割り勘' is selected, it's always split between 'あなた' and 'パートナー'
        # Check for invalid combinations with '割り勘'
        invalid_selection_with_split = False
        # If any individual OTHER THAN 'あなた' or 'パートナー' is selected when '割り勘' is also selected.
        if len([p for p in individuals_selected if p not in ['あなた', 'パートナー']]) > 0:
            invalid_selection_with_split = True

        if invalid_selection_with_split:
            print(f"DEBUG: Invalid selection with '割り勘' detected.")
            return None, "「割り勘」を選択した場合、原則として「あなた」と「パートナー」が均等に負担します。他の個人を同時に負担者に指定することはできません。"

        share = float(total_amount) / 2
        burden_values["あなた_負担額"] = share
        burden_values["パートナー_負担額"] = share
        # Ensure 'その他_負担額' remains 0.0 if 'その他' was in input_persons
        if 'その他' in input_persons:
            burden_values["その他_負担額"] = 0.0
        print(f"DEBUG: '割り勘' split calculated: {burden_values}")
        return burden_values, None

    else:
        print(f"DEBUG: '割り勘' is NOT selected. Individuals selected: {individuals_selected}")
        # Case 2: '割り勘' is NOT selected
        if len(individuals_selected) == 1:
            # One individual selected, they bear the full cost
            individual = individuals_selected[0]
            burden_values[f"{individual}_負担額"] = float(total_amount)
            print(f"DEBUG: Single individual burden calculated: {burden_values}")
            return burden_values, None
        elif len(individuals_selected) > 1:
            # Multiple individuals selected without '割り勘'
            print(f"DEBUG: Error: Multiple individuals selected without '割り勘'.")
            return None, "「割り勘」を選択せずに複数の個人を負担者に指定することはできません。一人のみを選択してください。"
        else:
            # No individuals selected
            print(f"DEBUG: Error: No bearers selected.")
            return None, "負担者が選択されていません。少なくとも一人の個人または「割り勘」を選択してください。"

# =========================
# 支出登録
# =========================

def add_expense(b):
    global df
    # Clear output at the beginning of the function call to show fresh debug info
    with main_output:
        clear_output()
        print("add_expense function called.") # Debugging print for user

    amount = amount_input.value
    selected_bearers = cost_bearer_selector.value
    with main_output: # Ensure this print is also visible to the user
        print(f"Amount: {amount}, Selected Bearers: {selected_bearers}") # Debugging print for user

    calculated_burdens, error_message = calculate_burden(amount, selected_bearers)

    if error_message:
        with main_output:
            print(f"エラー: {error_message}") # This will print after previous prints in main_output
        return # Return immediately after showing error

    new_data_dict = {
        "日付": datetime.now().strftime("%Y-%m-%d"),
        "カテゴリ": category_input.value,
        "金額": float(amount), # 元の金額も保持
        "メモ": memo_input.value,
        "入力者": person_selector.value,
    }
    new_data_dict.update(calculated_burdens) # 負担額を追加

    # 辞書からDataFrameを作成し、既存のDataFrameに追加
    new_df_row = pd.DataFrame([new_data_dict], columns=all_df_cols) # 全てのカラムを明示的に指定
    df = pd.concat([df, new_df_row], ignore_index=True)

    save_kakeibo()

    with main_output:
        print("登録完了") # This will print after previous prints in main_output

    refresh_table()

# =========================
# ワンタップ登録
# =========================

def quick_add(name, amount):
    global df

    selected_bearers = cost_bearer_selector.value

    calculated_burdens, error_message = calculate_burden(amount, selected_bearers)

    if error_message:
        with main_output:
            clear_output()
            print(f"エラー: {error_message}")
        return

    new_data_dict = {
        "日付": datetime.now().strftime("%Y-%m-%d"),
        "カテゴリ": name,
        "金額": float(amount), # 元の金額も保持
        "メモ": "ワンタップ",
        "入力者": person_selector.value,
    }
    new_data_dict.update(calculated_burdens) # 負担額を追加

    # 辞書からDataFrameを作成し、既存のDataFrameに追加
    new_df_row = pd.DataFrame([new_data_dict], columns=all_df_cols) # 全てのカラムを明示的に指定
    df = pd.concat([df, new_df_row], ignore_index=True)

    save_kakeibo()

    with main_output:
        clear_output()
        print(f"{name} 登録完了")

    refresh_table()

# =========================
# ボタン追加
# =========================

def add_quick_button(b):

    global button_df

    if quick_name.value.strip() == '':
        with main_output:
            clear_output()
            print("ボタン名を入力してください。")
        return

    new_data = pd.DataFrame([
        {
            "名前": quick_name.value,
            "金額": quick_amount.value
        }
    ])

    button_df = pd.concat(
        [button_df, new_data],
        ignore_index=True
    )

    save_buttons()

    render_buttons()

    with main_output:
        clear_output()
        print("ボタン追加完了")

# =========================
# ボタン描画
# =========================

def render_buttons():

    with buttons_output:

        clear_output()

        print("=== ワンタップ ===")

        # 無効な行を除外してボタンを描画
        cleaned_button_df = button_df.dropna(subset=['名前'])
        cleaned_button_df = cleaned_button_df[cleaned_button_df['名前'].str.strip() != '']

        for index, row in cleaned_button_df.iterrows():

            btn = widgets.Button(
                description=f"{row['名前']} ¥{row['金額']}"
            )

            # --- DEBUGGING LINE --- ここから
            # with main_output:
            #     print(f"Rendering button: {btn.description}")
            # --- DEBUGGING LINE --- ここまで

            btn.on_click(
                lambda b,
                n=row["名前"],
                a=row["金額"]:
                quick_add(n, a)
            )

            display(btn)

# =========================
# 表表示
# =========================

def refresh_table():

    with table_output:

        clear_output()

        print("=== 最新データ ==")

        display(df.tail(10))

# =========================
# イベント
# =========================

save_button.on_click(add_expense)

quick_add_button.on_click(add_quick_button)

# =========================
# 画面表示
# =========================

display(widgets.HTML("<h2>家計簿アプリ</h2>"))

display(widgets.HTML("<h3>支出入力</h3>"))

display(person_selector) # 入力者セレクターを表示
display(cost_bearer_selector) # 負担者セレクターを表示
display(category_input)
display(amount_input)
display(memo_input)
display(save_button)

display(widgets.HTML("<hr>"))

display(widgets.HTML("<h3>ワンタップ設定</h3>"))

display(quick_name)
display(quick_amount)
display(quick_add_button)

display(widgets.HTML("<hr>"))

# buttons_outputを最後に表示するように変更
# display(buttons_output) # <-- この行をコメントアウト

display(widgets.HTML("<hr>"))

display(main_output)

display(table_output)

render_buttons()

refresh_table()

# render_buttons()が実行された後にbuttons_outputを表示
display(buttons_output)

import streamlit as st
st.title("家計簿アプリ")
st.write("公開成功")

print('quick_buttons.csv の内容:')
quick_buttons_from_csv = pd.read_csv('quick_buttons.csv')
display(quick_buttons_from_csv)
