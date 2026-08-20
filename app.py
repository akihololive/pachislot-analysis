import re
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="パチスロ 差枚チェッカー", page_icon="🎰", layout="wide")
st.title("🎰 パチスロ：差枚チェッカー")
st.markdown('直近の差枚数確認用、高設定が据えてあるわけじゃないよ！<span style="color:red;">※8月20日 更新</span>🐰', unsafe_allow_html=True)

GITHUB_USER = "akihololive"
GITHUB_REPO = "pachislot-analysis"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = "ghp_FlOVwiyWi3noQ1mWIgAV1sahOBykFq1hT21y"

shop_map = {
    "アイランド秋葉原店": "island",
    "エスパス秋橋原店": "espace",
    "マルハン池袋SB": "maruhan_ikebukuro_sb",
    "マルハン東宝新宿": "maruhan_shinjuku",
    "エクサファースト": "exa",
    "マルハン池袋店": "maruhan_ikebukuro",
    "エスパス上野本館": "espace_ueno",
    "楽園アメ横店": "rakuen_ameyoko", 
}

st.write("---")
view_mode = st.radio("🔄 取得モードを選択してください", ["🏢 1店舗ずつじっくり見る", "🌍 全8店舗を一括スキャンして比べる"], horizontal=True)

if view_mode == "🏢 1店舗ずつじっくり見る":
    selected_shop = st.selectbox("🏢 分析する店舗を選択してください", list(shop_map.keys()))
    shops_to_scan = [selected_shop]
    current_data_key = f"web_data_{selected_shop}"
else:
    st.info("💡 全店舗一括スキャンはGitHubからのデータ取得に15〜30秒ほど時間がかかります。")
    shops_to_scan = list(shop_map.keys())
    current_data_key = "web_data_ALL_SHOPS"

st.write("---")
col1, col2 = st.columns(2)
with col1:
    min_coin = st.selectbox("💰 最低差枚数（最新日ベース）", ["all", -1000, -500, 0, 500, 1000, 2000, 3000, 5000], index=0, format_func=lambda x: "✨ すべての台（制限なし）" if x == "all" else ("前日プラス台" if x == 0 else f"{x:+,}枚以上"))
with col2:
    analysis_mode = st.radio("🔍 分析フォーカス", ["据え置き狙い（連続プラス台）", "設定上げ狙い（連続凹み台）"], horizontal=True)

st.write("---")
button_label = f"🔄 【{selected_shop}】の最新データを自動スキャン" if view_mode == "🏢 1店舗ずつじっくり見る" else "🔥 全8店舗の最新データを一括スキャン（まとめて表示）"

if st.button(button_label, type="primary"):
    st.session_state[current_data_key] = {}
    all_combined_data = {}
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    total_shops = len(shops_to_scan)
    headers = {"User-Agent": "Streamlit-App"}
    
    global_target_files = []
    global_day_mapping = {}

    try:
        for idx, shop_name in enumerate(shops_to_scan):
            progress_percent = idx / total_shops
            progress_bar.progress(progress_percent)
            status_text.text(f"⏳ ({idx+1}/{total_shops}) 【{shop_name}】のデータを取得中...")
            
            folder_name = shop_map[shop_name]
            api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/data/{folder_name}"
            
            api_res = requests.get(api_url, headers=headers)
            if api_res.status_code != 200:
                st.warning(f"⚠️ {shop_name}のファイル一覧を取得できませんでした。(Status: {api_res.status_code})")
                continue
                
            api_data = api_res.json()
            all_files = sorted([f["name"] for f in api_data if f["name"].endswith(".txt")], reverse=True)
            target_files = all_files[:10]
            
            if not target_files:
                st.warning(f"⚠️ {shop_name}のフォルダ内に .txt ファイルが見つかりませんでした。")
                continue
            
            day_mapping = {fname: (index + 1) for index, fname in enumerate(target_files)}
            
            if not global_target_files:
                global_target_files = target_files
                global_day_mapping = day_mapping
            
            for fname in target_files:
                day_num = day_mapping[fname]
                file_raw_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/data/{folder_name}/{fname}"
                
                file_res = requests.get(file_raw_url)
                if file_res.status_code == 200:
                    lines = file_res.content.decode("utf-8").split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line or "機種" in line or "台番" in line: continue
                        parts = re.split(r'\t+|\s{2,}', line)
                        
                        if len(parts) >= 3:
                            name = parts[0].strip()
                            table_text = parts[1].strip()
                            coin_text = parts[2].strip()
                            
                            clean_coin = coin_text.replace("枚", "").replace(",", "").replace("+", "").strip()
                            try:
                                coin, table_num = int(clean_coin), int(table_text)
                                unique_key = f"{shop_name}_{table_num}"
                                
                                if unique_key not in all_combined_data: 
                                    all_combined_data[unique_key] = {
                                        "shop_name": shop_name,
                                        "table_num": table_num,
                                        "name": name, 
                                        "history": {}
                                    }
                                all_combined_data[unique_key]["history"][day_num] = coin
                            except ValueError: continue

        progress_bar.progress(1.0)
        status_text.text("✅ すべてのデータ処理が完了しました！")
        
        if not all_combined_data:
            st.error("❌ データを1つも読み込めませんでした。")
            st.stop()
            
        st.session_state[current_data_key] = all_combined_data
        st.session_state[f"web_files_{current_data_key}"] = global_target_files
        st.session_state[f"web_mapping_{current_data_key}"] = global_day_mapping
        st.success(f"🎉 スキャン成功！ 合計 {len(all_combined_data)} 台のデータを読み込みました。")
        
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")

if current_data_key in st.session_state and st.session_state[current_data_key]:
    all_data = st.session_state[current_data_key]
    target_files = st.session_state[f"web_files_{current_data_key}"]
    day_mapping = st.session_state[f"web_mapping_{current_data_key}"]
    
    unique_machines = sorted(list(set(info["name"] for info in all_data.values())))
    selected_machine = st.selectbox("🎯 機種名でピンポイント絞り込み", ["✨ すべての機種"] + unique_machines)
    
    st.write(f"## 🏆 分析結果")
    
    table_rows = []
    for unique_key, info in all_data.items():
        if selected_machine != "✨ すべての機種" and info["name"] != selected_machine: continue
        history = info["history"]
        latest_coin = history.get(1, None)
        if latest_coin is None: continue
        
        plus_days = sum(1 for v in history.values() if v > 0)
        minus_days = sum(1 for v in history.values() if v <= 0)
        total_coin = sum(history.values())
        
        history_k_list = []
        for fname in target_files:
            if day_mapping[fname] in history:
                v = history[day_mapping[fname]]
                history_k_list.append("0" if v == 0 else f"{v/1000:+.1f}k".replace(".0k", "k"))
        history_flow_short = "[" + ", ".join(history_k_list) + "]"
        
        show_this_table, star, rank_score = False, "", 0
        if min_coin == "all":
            show_this_table = True
            plus_streak = 0
            if latest_coin > 0:
                plus_streak = 1
                for idx in range(2, 11):
                    if history.get(idx, 0) > 0: plus_streak += 1
                    else: break
            
            if plus_streak >= 3: star, rank_score = f"🔥 {plus_streak}日連続プラス", plus_streak
            elif plus_streak == 2: star, rank_score = "🔶 2日連続プラス", 2
            elif plus_streak == 1: star, rank_score = "🔸 前日のみプラス", 1
            else: star, rank_score = "💧 凹み台", 0
        else:
            if analysis_mode == "据え置き狙い（連続プラス台）":
                if latest_coin >= min_coin:
                    show_this_table = True
                    plus_streak = 0
                    if latest_coin > 0:
                        plus_streak = 1
                        for idx in range(2, 11):
                            if history.get(idx, 0) > 0: plus_streak += 1
                            else: break
                    
                    if plus_streak >= 3: star, rank_score = f"🔥 {plus_streak}日連続プラス", plus_streak
                    elif plus_streak == 2: star, rank_score = "🔶 2日連続プラス", 2
                    else: star, rank_score = "🔸 前日のみプラス", 1
            elif analysis_mode == "設定上げ狙い（連続凹み台）":
                if latest_coin < 0:
                    show_this_table = True
                    minus_streak = 0
                    if latest_coin < 0:
                        minus_streak = 1
                        for idx in range(2, 11):
                            if history.get(idx, 0) < 0: minus_streak += 1
                            else: break
                    
                    if minus_streak >= 3: star, rank_score = f"💎 {minus_streak}日連続凹み", minus_streak
                    elif minus_streak == 2: star, rank_score = "🔷 2日連続凹み", 2
                    else: star, rank_score = "🔹 前日のみ凹み", 1

        if show_this_table:
            total_days = plus_days + minus_days
            avg_coin = int(total_coin / total_days) if total_days > 0 else 0
            
            table_rows.append({
                "rank_score": rank_score, "unique_key": unique_key, "台番号_num": info["table_num"], 
                "台番号": f"📈 {info['table_num']}番", "機種名": info["name"], "ステータス": star, 
                "前日差枚": latest_coin, "10日間累計": total_coin, "勝率履歴": f"{plus_days}勝/{minus_days}敗", 
                "10日平均差枚": avg_coin, "10日間のデータ推移(新しい順)": history_flow_short,
                "店舗名": info["shop_name"] if view_mode == "🌍 全8店舗を一括スキャンして比べる" else selected_shop
            })
            
    if table_rows:
        if analysis_mode == "据え置き狙い（連続プラス台）" or min_coin == "all":
            table_rows.sort(key=lambda x: (-x["rank_score"], -x["10日間累計"], x["台番号_num"]))
        else:
            table_rows.sort(key=lambda x: (-x["rank_score"], x["10日間累計"], x["台番号_num"]))

        df_display = pd.DataFrame(table_rows)

        if view_mode == "🌍 全8店舗を一括スキャンして比べる":
            cols = ["店舗名", "台番号", "機種名", "ステータス", "前日差枚", "10日間累計", "勝率履歴", "10日平均差枚", "10日間のデータ推移(新しい順)", "rank_score", "unique_key", "台番号_num"]
            df_display = df_display[cols]

        selected_rows = st.dataframe(
            df_display, use_container_width=True, height=400, on_select="rerun", selection_mode="single-row",
            column_config={
                "rank_score": None, "unique_key": None, "台番号_num": None,
                "前日差枚": st.column_config.NumberColumn(format="%+,d枚", alignment="left"), 
                "10日間累計": st.column_config.NumberColumn(format="%+,d枚", alignment="left"),
                "10日平均差枚": st.column_config.NumberColumn(format="%+,d枚", alignment="left"),
            }
        )
        
        if selected_rows and "rows" in selected_rows["selection"] and selected_rows["selection"]["rows"]:
            row_idx = selected_rows["selection"]["rows"][0]
        else:
            row_idx = 0
        
        target_key = df_display.iloc[row_idx]["unique_key"]
        target_table_num = df_display.iloc[row_idx]["台番号_num"]
        target_machine_name = str(df_display.iloc[row_idx]["機種名"])
        target_shop_name = df_display.iloc[row_idx]["店舗名"] if view_mode == "🌍 全8店舗を一括スキャンして比べる" else selected_shop
        
        if target_key:
            st.write("---")
            st.write(f"### 📊 【{target_shop_name}】{target_table_num}番台（{target_machine_name}）の10日間差枚数データ（日別）")
            target_history = all_data[target_key]["history"]
            graph_data = []
            
            for fname in reversed(target_files):
                day_num = day_mapping[fname]
                if day_num in target_history: graph_data.append({"index_num": day_num, "当日の差枚数": target_history[day_num]})
                
            if graph_data:
                df_chart = pd.DataFrame(graph_data)
                df_chart_fixed = df_chart.set_index("index_num").reindex(range(1, 11)).dropna()
                
                df_chronological = df_chart_fixed.sort_index(ascending=False)
                cum_sum_data = np.cumsum(df_chronological["当日の差枚数"])
                
                y_values = [int(val) for val in cum_sum_data]
                x_labels = ["スタート"] + [f"{idx}日前" for idx in df_chronological.index]
                
                fig = go.Figure()
                zero_y = [0] * len(x_labels)
                    
                fig.add_trace(go.Scatter(
                    x=x_labels, y=zero_y, mode="lines", 
                    line=dict(color="rgba(255, 255, 255, 0.3)", width=1, dash="dash"),
                    hoverinfo="skip"
                ))
                
                fig.add_trace(go.Scatter(
                    x=x_labels, y=y_values, mode="lines+markers", 
                    line=dict(color="#ff9900", width=3), marker=dict(color="#ff9900", size=6),
                    hovertemplate="<b>%{x}時点の累計差枚</b><br>差枚数: %{y:+,}枚<extra></extra>"
                ))
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=10, b=10), height=400, showlegend=False, template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20,20,20,0.8)",
                    yaxis=dict(zeroline=True, zerolinewidth=1.5, zerolinecolor="white", tickformat="+,d", gridcolor="rgba(255, 255, 255, 0.1)"),
                    xaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)")
                )
                
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                
                df_table_formatted = df_chronological.copy()
                df_table_formatted["当日の差枚数"] = df_table_formatted["当日の差枚数"].map(lambda x: f"{x:+,}" if x != 0 else "0")
                df_summary = df_table_formatted.T
                df_summary.columns = [f"{col}日前" for col in df_summary.columns]
                st.dataframe(df_summary, use_container_width=True)
    else:
        st.info("😭 条件に合う台は見つかりませんでした。")
else:
    st.info("☝️ 上のボタンを押すと、全自動で各フォルダからデータを読み込みます！")
