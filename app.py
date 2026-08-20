import re
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="パチスロ 差枚チェッカー", page_icon="🎰", layout="wide")
st.title("🎰 パチスロ：差枚チェッカー")
st.markdown('直近の差枚数確認用、高設定が据えてあるわけじゃないよ！<span style="color:red;">※8月20日 更新</span>🐰', unsafe_allow_html=True)

# ⚙️ 設定
GITHUB_USER = "akihololive"
GITHUB_REPO = "pachislot-analysis"
GITHUB_BRANCH = "main"

# 💡 英語に変更したフォルダ名の対応表
shop_map = {
    "アイランド秋葉原店": "island",
    "エスパス秋葉原店": "espace",
    "マルハン池袋SB": "maruhan_ikebukuro_sb",
    "マルハン東宝新宿": "maruhan_shinjuku",
    "エクサファースト": "exa",
}

selected_shop = st.selectbox("🏢 分析する店舗を選択してください", list(shop_map.keys()))

st.write("---")
col1, col2 = st.columns(2)
with col1:
    min_coin = st.selectbox("💰 最低差枚数（最新日ベース）", [ "all", -1000, -500, 0, 500, 1000, 2000, 3000, 5000 ], index=0, format_func=lambda x: "✨ すべての台（制限なし）" if x == "all" else ("前日プラス台" if x == 0 else f"{x:+,}枚以上"))
with col2:
    analysis_mode = st.radio("🔍 分析フォーカス", [ "据え置き狙い（連続プラス台）", "設定上げ狙い（連続凹み台）" ], horizontal=True)

st.write("---")
current_shop_key = f'web_data_{selected_shop}'

if st.button(f"🔄 【{selected_shop}】の最新データを一括自動スキャン", type="primary"):
    with st.spinner(f"⏳ ネット上の【{selected_shop}】フォルダからデータを取得中..."):
        try:
            folder_name = shop_map.get(selected_shop)
            
            headers = {"User-Agent": "Streamlit-App"}
            api_url = f"https://github.com{GITHUB_USER}/{GITHUB_REPO}/contents/data/{folder_name}"
            
            api_res = requests.get(api_url, headers=headers)
            if api_res.status_code != 200:
                st.error(f"❌ GitHubからファイル一覧を取得できませんでした。(Status: {api_res.status_code})")
                st.stop()
                
            api_data = api_res.json()
            all_files = sorted([ f.get("name") for f in api_data if f.get("name").endswith(".txt") ], reverse=True)
            target_files = all_files [ :10 ]
            
            if not target_files:
                st.error(f"❌ {selected_shop}のフォルダ内に .txt ファイルが見つかりませんでした。")
                st.stop()
            
            day_mapping = {fname: (index + 1) for index, fname in enumerate(target_files)}
            all_data, unique_machines = {}, set()
            success_count = 0
            
            for fname in target_files:
                day_num = day_mapping[fname]
                file_raw_url = f"https://githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/data/{folder_name}/{fname}"
                
                file_res = requests.get(file_raw_url)
                if file_res.status_code == 200:
                    success_count += 1
                    lines = file_res.content.decode('utf-8').split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line or "機種" in line or "台番" in line: continue
                        parts = re.split(r'\t| {2,}', line)
                        
                        # 💡 【完全防衛】消えやすい四角括弧の記号を1箇所も使わずに、1列ずつ安全にデータを引き抜きます！
                        if len(parts) >= 3:
                            name = parts.pop(0).strip()
                            table_text = parts.pop(0).strip()
                            coin_text = parts.pop(0).strip()
                            clean_coin = coin_text.replace("枚", "").replace(",", "").replace("+", "").strip()
                            try:
                                coin = int(clean_coin)
                                table_num = int(table_text)
                                if table_num not in all_data: all_data [ table_num ] = {"name": name, "history": {}}
                                all_data [ table_num ] ["history"] [ day_num ] = coin
                                unique_machines.add(name)
                            except ValueError: continue

            if success_count == 0:
                st.error(f"❌ データファイルを1つも読み込めませんでした。")
                st.stop()
            
            st.session_state [ current_shop_key ] = all_data
            st.session_state [ f"web_machines_{selected_shop}" ] = sorted(list(unique_machines))
            st.session_state [ f"web_files_{selected_shop}" ] = target_files
            st.session_state [ f"web_mapping_{selected_shop}" ] = day_mapping
            st.success(f"✅ 【{selected_shop}】のデータスキャンに成功しました！（読み込み完了: {success_count}日分）")
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")

if current_shop_key in st.session_state:
    all_data = st.session_state [ current_shop_key ]
    unique_machines = st.session_state [ f"web_machines_{selected_shop}" ]
    target_files = st.session_state [ f"web_files_{selected_shop}" ]
    day_mapping = st.session_state [ f"web_mapping_{selected_shop}" ]

    selected_machine = st.selectbox("🎰 機種名でピンポイント絞り込み", [ "✨ すべての機種" ] + unique_machines)
    st.write(f"### 📊 【{selected_shop}】分析結果")

    table_rows = list()

    for table_num, info in all_data.items():
        if selected_machine != "✨ すべての機種" and info.get("name") != selected_machine: continue
        history = info.get("history")
        latest_coin = history.get(1, None)
        if latest_coin is None: continue

        plus_days = sum(1 for v in history.values() if v > 0)
        minus_days = sum(1 for v in history.values() if v <= 0)
        total_coin = sum(history.values())

        history_k_list = list()
        for fname in target_files:
            day_idx = day_mapping.get(fname)
            if day_idx in history:
                v = history.get(day_idx)
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
            if "据え置き" in analysis_mode:
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
            elif "設定上げ" in analysis_mode:
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
            table_rows.append({
                "台番号": f"{table_num}番台",
                "機種名": info.get("name"),
                "ステータス": star,
                "前日差枚": f"{latest_coin:+,}枚" if latest_coin != 0 else "0枚",
                "10日間累計": f"{total_coin:+,}枚" if total_coin != 0 else "0枚",
                "勝率": f"{plus_days}勝/{plus_days+minus_days}敗",
                "10日平均差枚": f"{int(total_coin/(plus_days+minus_days)):+,}枚" if (plus_days+minus_days) > 0 else "0枚",
                "10日間のデータ(新➡️古い順)": history_flow_short,
                "rank_score": rank_score
            })

    if table_rows:
        df_display = pd.DataFrame(table_rows)
        df_display = df_display.sort_values(by="rank_score", ascending=False).drop(columns=["rank_score"])
        
        selected_rows = st.data_editor(
            df_display,
            hide_index=True,
            use_container_width=True,
            disabled=["台番号", "機種名", "ステータス", "前日差枚", "10日間累計", "勝率", "10日平均差枚", "10日間のデータ(新➡️古い順)"]
        )
        
        if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
            row_idx = 0
            target_machine = df_display.iloc [ row_idx ] ["台番号"].replace("番台", "")
            
            if target_machine in all_data:
                mach_info = all_data.get(target_machine)
                st.write("---")
                st.write("### 📈 各台の詳細スランプグラフ (過去10日間累積)")
                st.write(f"#### 📍 選択中: {target_machine}番台 ({mach_info.get('name')})")
                
                graph_data = list()
                for idx in range(1, 11):
                    graph_data.append({
                        "index_num": idx,
                        "当日の差枚数": mach_info.get("history").get(idx, 0)
                    })
                    
                df_chart = pd.DataFrame(graph_data)
                df_chart_fixed = df_chart.set_index("index_num").reindex(range(1, 11)).fillna(0)
                df_chronological = df_chart_fixed.sort_index(ascending=False)
                
                cum_sum_data = np.cumsum(df_chronological [ "当日の差枚数" ])
                
                y_values = list()
                y_values.append(0)

                for val in cum_sum_data:
                    y_values.append(int(val))
                    
                x_labels = list()
                x_labels.append("スタート")
                for idx in df_chronological.index:
                    x_labels.append(f"{idx}日前")
                fig = go.Figure()
                
                # 0基準線（白点線）※ここも言葉だけで0の配列を作成！
                zero_y = list()
                for _ in range(len(x_labels)):
                    zero_y.append(0)
                    
                fig.add_trace(go.Scatter(
                    x=x_labels, 
                    y=zero_y, 
                    mode='lines', 
                    line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dash'),
                    hoverinfo='skip'
                ))
                
                # 鮮やかなオレンジ色の折れ線（縦幅2倍のド迫力サイズ！）
                fig.add_trace(go.Scatter(
                    x=x_labels,
                    y=y_values,
                    mode='lines+markers', 
                    line=dict(color='#ff9900', width=3), 
                    marker=dict(color='#ff9900', size=6),
                    hovertemplate="<b>%{x}時点の累計差枚</b><br>差枚数: %{y:+,}枚<extra></extra>"
                ))
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=10, b=10),
                    height=600,
                    showlegend=False,
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(20,20,20,0.8)',
                    yaxis=dict(
                        zeroline=True,
                        zerolinewidth=1.5,
                        zerolinecolor='white',
                        tickformat="+,d",
                        gridcolor='rgba(255, 255, 255, 0.1)'
                    ),
                    xaxis=dict(
                        gridcolor='rgba(255, 255, 255, 0.05)'
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                df_table_formatted = df_chronological.copy()
                df_table_formatted["当日の差枚数"] = df_table_formatted["当日の差枚数"].map(lambda x: f"{x:+,}" if x != 0 else "0")
                df_summary = df_table_formatted.T
                df_summary.columns = [f"{col}日前" for col in df_summary.columns]
                st.dataframe(df_summary, use_container_width=True)
else:
    st.info("🔍 条件に一致するデータがありません。設定枚数や絞り込み条件を変えてみてください。")
