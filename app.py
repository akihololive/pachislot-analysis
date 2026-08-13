import re, requests
import streamlit as st
import pandas as pd
from urllib.parse import quote

st.set_page_config(page_title="パチスロ 10日間データ一括分析ツール", page_icon="🎰", layout="wide")
st.title("🎰 パチスロ：複数店舗対応 10日間一括分析ツール（Web全自動版）")
st.markdown("GitHub内の各店舗フォルダから最新10日分のデータを自動で取得し、一括クロス分析を行います！")

# 💡 【究極の修正】計算や組み合わせを一切挟まず、正しいURLを1文字も漏らさず100%固定で記述しました！
BASE_API_URL = "https://github.com"
RAW_URL_BASE = "https://githubusercontent.com"

def to_k_notation(val):
    return "0" if val == 0 else f"{val/1000:+.1f}k".replace(".0k", "k")

shop_list = ["アイランド秋葉原店", "エクサファースト", "エスパス秋葉原店"]
selected_shop = st.selectbox("🏢 分析する店舗を選択してください", shop_list)

st.write("---")
col1, col2 = st.columns(2)
with col1:
    min_coin = st.selectbox("💰 最低差枚数（最新日ベース）", ["all", -1000, -500, 0, 500, 1000, 2000, 3000, 5000], index=3, format_func=lambda x: "✨ すべての台（制限なし）" if x == "all" else ("前日プラス台" if x == 0 else f"{x:+,}枚以上"))
with col2:
    analysis_mode = st.radio("🔍 分析フォーカス", ["据え置き狙い（連続プラス台）", "設定上げ狙い（連続凹み台）"], horizontal=True)

st.write("---")
current_shop_key = f'web_data_{selected_shop}'

if st.button(f"🔄 【{selected_shop}】の最新データを一括自動スキャン", type="primary"):
    with st.spinner(f"⏳ ネット上の【{selected_shop}】フォルダから最新10日分のデータを取得中..."):
        try:
            encoded_shop = quote(selected_shop)
            list_url = BASE_API_URL + "/" + encoded_shop
            res = requests.get(list_url)
            
            target_files = []
            if res.status_code == 200:
                files_data = res.json()
                txt_files = [f["name"] for f in files_data if f["name"].endswith(".txt")]
                txt_files.sort(reverse=True)
                target_files = txt_files[:10]
            else:
                base_dates = [f"202608{str(i).zfill(2)}.txt" for i in range(3, 13)]
                target_files = sorted(base_dates, reverse=True)

            day_mapping = {fname: (index + 1) for index, fname in enumerate(target_files)}
            all_data, unique_machines = {}, set()
            success_count = 0
            
            for fname in target_files:
                day_num = day_mapping[fname]
                encoded_fname = quote(fname)
                file_raw_url = RAW_URL_BASE + "/" + encoded_shop + "/" + encoded_fname
                
                file_res = requests.get(file_raw_url)
                if file_res.status_code == 200:
                    success_count += 1
                    lines = file_res.text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line or "機種" in line or "台番" in line: continue
                        parts = re.split(r'\t+|\s{2,}', line)
                        if len(parts) >= 3:
                            name, table_text, coin_text = parts.strip(), parts.strip(), parts.strip()
                            clean_coin = coin_text.replace("枚", "").replace(",", "").replace("+", "").strip()
                            try:
                                coin, table_num = int(clean_coin), int(table_text)
                                if table_num not in all_data: all_data[table_num] = {"name": name, "history": {}}
                                all_data[table_num]["history"][day_num] = coin
                                unique_machines.add(name)
                            except ValueError: continue

            if success_count == 0:
                st.error(f"❌ {selected_shop} のデータファイルを1つも読み込めませんでした。")
                st.stop()
            
            st.session_state[current_shop_key] = all_data
            st.session_state[f"web_machines_{selected_shop}"] = sorted(list(unique_machines))
            st.session_state[f"web_files_{selected_shop}"] = target_files
            st.session_state[f"web_mapping_{selected_shop}"] = day_mapping
            st.success(f"✅ 【{selected_shop}】のデータスキャンに成功しました！（読み込み完了: {success_count}日分）")
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")

if current_shop_key in st.session_state:
    all_data = st.session_state[current_shop_key]
    unique_machines = st.session_state[f"web_machines_{selected_shop}"]
    target_files = st.session_state[f"web_files_{selected_shop}"]
    day_mapping = st.session_state[f"web_mapping_{selected_shop}"]
    
    selected_machine = st.selectbox("🎯 機種名でピンポイント絞り込み", ["✨ すべての機種"] + unique_machines)
    st.write(f"## 🏆 【{selected_shop}】分析結果")
    
    table_rows = []
    for table_num, info in all_data.items():
        if selected_machine != "✨ すべての機種" and info["name"] != selected_machine: continue
        history = info["history"]
        latest_coin = history.get(1, None)
        if latest_coin is None: continue
        
        plus_days = sum(1 for v in history.values() if v > 0)
        minus_days = sum(1 for v in history.values() if v <= 0)
        total_coin = sum(history.values())
        history_k_list = [to_k_notation(history[day_mapping[fname]]) for fname in target_files if day_mapping[fname] in history]
        history_flow_short = "[" + ", ".join(history_k_list) + "]"
        
        show_this_table, star, rank_score = False, "", 0
        if min_coin == "all":
            show_this_table = True
            if history.get(2, 0) > 0 and history.get(3, 0) > 0: star, rank_score = "🔥🔥🔥 高頻度", 3
            elif history.get(2, 0) > 0: star, rank_score = "🔥🔥 中頻度", 2
            else: star, rank_score = "🔥 低頻度", 1
        else:
            if analysis_mode == "据え置き狙い（連続プラス台）":
                if latest_coin >= min_coin:
                    show_this_table = True
                    if history.get(2, 0) > 0 and history.get(3, 0) > 0: star, rank_score = "🔥🔥🔥 高頻度", 3
                    elif history.get(2, 0) > 0: star, rank_score = "🔥🔥 中頻度", 2
                    else: star, rank_score = "🔥 低頻度", 1
            elif analysis_mode == "設定上げ狙い（連続凹み台）":
                if latest_coin < 0:
                    if history.get(2, 0) < 0 and history.get(3, 0) < 0: show_this_table, star, rank_score = True, "💎💎💎 極・変更上げ", 3
                    elif history.get(2, 0) < 0: show_this_table, star, rank_score = True, "💎💎 上げ準備", 2

        if show_this_table:
            total_days = plus_days + minus_days
            avg_coin = int(total_coin / total_days) if total_days > 0 else 0
            table_rows.append({
                "rank_score": rank_score, "台番号_num": table_num, "台番号": f"{table_num}番", "機種名": info["name"],
                "ステータス": star, "前日差枚": latest_coin, "10日間累計": total_coin, "勝率履歴_勝数": int(plus_days),
                "勝率履歴": f"{plus_days}勝/{minus_days}敗", "10日平均差枚": avg_coin, "10日間のデータ推移(新しい順)": history_flow_short
            })
            
    if table_rows:
        table_rows.sort(key=lambda x: (-x["勝率履歴_勝数"], -x["10日間累計"], x["台番号_num"]))
        df_display = pd.DataFrame(table_rows)
        df_clean = df_display.drop(columns=["rank_score", "勝率履歴_勝数"])
        
        selected_rows = st.dataframe(
            df_clean, use_container_width=True, height=400, on_select="rerun", selection_mode="single-row",
            column_config={
                "前日差枚": st.column_config.NumberColumn(format="%+,d枚", alignment="left"), 
                "10日間累計": st.column_config.NumberColumn(format="%+,d枚", alignment="left"),
                "10日平均差枚": st.column_config.NumberColumn(format="%+,d枚", alignment="left"),
            }
        )
        
        try:
            row_idx = selected_rows["selection"]["rows"] if selected_rows and "rows" in selected_rows["selection"] and selected_rows["selection"]["rows"] else 0
            target_table_num = int(df_clean.iloc[row_idx]["台番号_num"])
            target_machine_name = str(df_clean.iloc[row_idx]["機種名"])
        except Exception:
            target_table_num = int(df_clean.iloc["台番号_num"])
            target_machine_name = str(df_clean.iloc["機種名"])
        
        if target_table_num:
            st.write("---")
            st.write(f"### 📊 {target_table_num}番台（{target_machine_name}）の10日間差枚数データ（日別）")
            target_history = all_data[target_table_num]["history"]
            graph_data = []
            
            for fname in reversed(target_files):
                day_num = day_mapping[fname]
                if day_num in target_history: graph_data.append({"index_num": day_num, "当日の差枚数": target_history[day_num]})
                
            if graph_data:
                df_chart = pd.DataFrame(graph_data)
                df_chart_fixed = df_chart.set_index("index_num").reindex(range(1, 11)).dropna()
                st.bar_chart(df_chart_fixed["当日の差枚数"], use_container_width=True)
                
                df_table_formatted = df_chart_fixed.copy()
                df_table_formatted["当日の差枚数"] = df_table_formatted["当日の差枚数"].map(lambda x: f"{x:+,}" if x != 0 else "0")
                df_summary = df_table_formatted.T
                df_summary.columns = [f"{col}日前" for col in df_summary.columns]
                st.dataframe(df_summary, use_container_width=True)
    else:
        st.info("😭 条件に合う台は見つかりませんでした。")
else:
    st.info(f"☝️ 上の「【{selected_shop}】の最新データを一括自動スキャン」ボタンを押すと、自動的に分析が始まります！")
