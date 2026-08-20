import re
import requests
import streamlit as st
import pandas as pd
import numpy as np  # 👈 ここにこの行が新しく入っていれば大正解です！
import plotly.graph_objects as go

st.set_page_config(page_title="パチスロ 差枚チェッカー", page_icon="🎰", layout="wide")
st.title("🎰 パチスロ：差枚チェッカー")
st.markdown('直近の差枚数確認用、高設定が据えてあるわけじゃないよ！<span style="color:red;">※8月20日 更新</span>🐰', unsafe_allow_html=True)

# ⚙️ 設定
GITHUB_USER = "akihololive"
GITHUB_REPO = "pachislot-analysis"
GITHUB_BRANCH = "main"

# 💡 英語に変更したフォルダ名の対応表（秋葉原・上野ジャグラー完全包囲網！）
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

# 💡 1店舗個別か、全店舗一括かを選ぶトグルを安全に追加
st.write("---")
view_mode = st.radio("mode", ["single", "all"], horizontal=True)

if view_mode == "single":
    selected_shop = st.selectbox("SHOP", list(shop_map.keys()))
    shops_to_scan = [selected_shop]
    current_shop_key = f"web_data_{selected_shop}"
else:
    shops_to_scan = list(shop_map.keys())
    current_shop_key = "web_data_ALL_SHOPS"

st.write("---")
col1, col2 = st.columns(2)
with col1:
    min_coin = st.selectbox("💰 最低差枚数（最新日ベース）", ["all", -1000, -500, 0, 500, 1000, 2000, 3000, 5000], index=0, format_func=lambda x: "✨ すべての台（制限なし）" if x == "all" else ("前日プラス台" if x == 0 else f"{x:+,}枚以上"))
with col2:
    analysis_mode = st.radio("🔍 分析フォーカス", ["据え置き狙い（連続プラス台）", "設定上げ狙い（連続凹み台）"], horizontal=True)

st.write("---")
button_label = f"🔄 【{selected_shop}】の最新10日分データをスキャン" if view_mode == "single" else "🔥 全8店舗の最新10日分データを一括ロード（まとめて表示）"

if st.button(button_label, type="primary"):
    with st.spinner("⏳ GitHubから最新の10日分データをロード中..."):
        try:
            json_url = f"https://githubusercontent.com{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/all_shops_10days.json"
            res = requests.get(json_url)
            
            if res.status_code != 200:
                st.error("❌ 合算データファイル（all_shops_10days.json）の読み込みに失敗しました。GitHubのActionsでファイルが正しく作られているか確認してください。")
                st.stop()
                
            raw_json_data = res.json()
            all_combined_data = dict()
            unique_machines = set()
            
            for u_key, info in raw_json_data.items():
                s_name = info.get("shop_name")
                if s_name in shops_to_scan:
                    t_num = info.get("table_num")
                    dict_key = t_num if view_mode == "single" else u_key
                    
                    all_combined_data[dict_key] = {
                        "name": info.get("name"),
                        "shop_name": s_name,
                        "history": info.get("history")
                    }
                    unique_machines.add(info.get("name"))
            
            if not all_combined_data:
                st.error("❌ 条件に該当するデータがありませんでした。")
                st.stop()
                
            st.session_state[current_shop_key] = all_combined_data
            st.session_state[f"web_machines_{current_shop_key}"] = sorted(list(unique_machines))
            
            dummy_files = list()
            dummy_mapping = dict()
            for i in range(1, 11):
                dummy_files.append(str(i))
                dummy_mapping[str(i)] = i
            st.session_state[f"web_files_{current_shop_key}"] = dummy_files
            st.session_state[f"web_mapping_{current_shop_key}"] = dummy_mapping
            
            st.success(f"✅ ロード成功！ 合計 {len(all_combined_data)} 台のフルデータを一瞬で読み込みました。")
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")

if current_shop_key in st.session_state and st.session_state.get(current_shop_key):
        all_data = st.session_state.get(current_shop_key)
    unique_machines = st.session_state.get(f"web_machines_{current_shop_key}")
    target_files = st.session_state.get(f"web_files_{current_shop_key}")
    day_mapping = st.session_state.get(f"web_mapping_{current_shop_key}")
    
    selected_machine = st.selectbox("🎯 機種名でピンポイント絞り込み", ["✨ すべての機種"] + unique_machines)
    st.write(f"## 🏆 分析結果（直近10日間データ）")
    
    table_rows = []
    for unique_key, info in all_data.items():
        if selected_machine != "✨ すべての機種" and info.get("name") != selected_machine: continue
        history = info.get("history")
0:+.1f}k".replace(".0k", "k"))
    history_flow_short = "[" + ", ".join(history_k_list) + "]"
    
    show_this_table, star, rank_score = False, "", 0
    if min_coin == "all":
        show_this_table = True
        plus_streak = 0
        if latest_coin > 0:
            plus_streak = 1
            for idx in range(2, 11):
                v = history.get(str(idx), history.get(idx, 0))
                if v > 0: plus_streak += 1
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
                        v = history.get(str(idx), history.get(idx, 0))
                        if v > 0: plus_streak += 1
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
                        v = history.get(str(idx), history.get(idx, 0))
                        if v < 0: minus_streak += 1
                        else: break
                
                if minus_streak >= 3: star, rank_score = f"💎 {minus_streak}日連続凹み", minus_streak
                elif minus_streak == 2: star, rank_score = "🔷 2日連続凹み", 2
                else: star, rank_score = "🔹 前日のみ凹み", 1

    if show_this_table:
        total_days = plus_days + minus_days
        avg_coin = int(total_coin / total_days) if total_days > 0 else 0
        
        # 💡 各列のデータを大かっこを使わない安全な辞書形式で定義
        t_num_val = info.get("table_num")
        row_dict = {
            "rank_score": rank_score, 
            "unique_key": unique_key, 
            "table_num_raw": t_num_val, 
            "col_table_num": f"📈 {t_num_val}番", 
            "col_machine_name": info.get("name"),
            "col_status": star, 
            "col_latest_coin": latest_coin, 
            "col_total_coin": total_coin, 
            "col_win_loss": f"{plus_days}勝/{minus_days}敗", 
            "col_avg_coin": avg_coin, 
            "col_history_flow": history_flow_short,
            "col_shop_name": info.get("shop_name")
        }
        table_rows.append(row_dict)
        
if table_rows:
    if analysis_mode == "据え置き狙い（連続プラス台）" or min_coin == "all":
        table_rows.sort(key=lambda x: (-x.get("rank_score"), -x.get("col_total_coin"), x.get("table_num_raw")))
    else:
        table_rows.sort(key=lambda x: (-x.get("rank_score"), x.get("col_total_coin"), x.get("table_num_raw")))

    df_display = pd.DataFrame(table_rows)

    # 💡 モードに応じて「店舗名」の列を一番左側に綺麗に回り込ませる処理
    if view_mode == "all":
        cols_order = ["col_shop_name", "col_table_num", "col_machine_name", "col_status", "col_latest_coin", "col_total_coin", "col_win_loss", "col_avg_coin", "col_history_flow", "rank_score", "unique_key", "table_num_raw"]
    else:
        cols_order = ["col_table_num", "col_machine_name", "col_status", "col_latest_coin", "col_total_coin", "col_win_loss", "col_avg_coin", "col_history_flow", "rank_score", "unique_key", "table_num_raw"]
    
    df_display = df_display[cols_order]

    selected_rows = st.dataframe(
            df_display, use_container_width=True, height=400, on_select="rerun", selection_mode="single-row",
            column_config={
                "rank_score": None,
                "台番号_num": None,
                "前日差枚": st.column_config.NumberColumn(format="%+,d枚", alignment="left"), 
                "10日間累計": st.column_config.NumberColumn(format="%+,d枚", alignment="left"),
                "10日平均差枚": st.column_config.NumberColumn(format="%+,d枚", alignment="left"),
            }
        )
        
if selected_rows and "rows" in selected_rows.get("selection", {}) and selected_rows.get("selection", {}).get("rows"):
    row_idx_list = selected_rows.get("selection", {}).get("rows")
    if isinstance(row_idx_list, list) and len(row_idx_list) > 0:
        row_idx = row_idx_list[0]
    else:
        row_idx = 0
else:
    row_idx = 0

target_key = df_display.iloc[row_idx].get("unique_key")
target_table_num = df_display.iloc[row_idx].get("table_num_raw")
target_machine_name = str(df_display.iloc[row_idx].get("col_machine_name"))
target_shop_name = df_display.iloc[row_idx].get("col_shop_name")

if target_key:
    st.write("---")
    st.write(f"### 📊 【{target_shop_name}】{target_table_num}番台（{target_machine_name}）の10日間差枚数データ（日別）")
    target_history = all_data.get(target_key, {}).get("history", {})
    graph_data = []
    
    for idx in reversed(range(1, 11)):
        v = target_history.get(str(idx), target_history.get(idx, None))
        if v is not None:
            graph_data.append({"index_num": idx, "value_coin": v})
        
    if graph_data:
        df_chart = pd.DataFrame(graph_data)
        cum_sum_data = np.cumsum(df_chart.get("value_coin"))
        
        y_values = []
        for val in cum_sum_data:
            y_values.append(int(val))
            
        x_labels = ["スタート"]
        for row_item in graph_data:
            x_labels.append(f"{row_item.get('index_num')}日前")
        
        fig = go.Figure()
        zero_y = np.zeros(len(x_labels)).tolist()
            
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
            margin=dict(l=20, r=20, t=10, b=10), height=500, showlegend=False, template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20,20,20,0.8)",
            yaxis=dict(zeroline=True, zerolinewidth=1.5, zerolinecolor="white", tickformat="+,d", gridcolor="rgba(255, 255, 255, 0.1)"),
            xaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)")
        )
        
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        
        summary_cols = []
        summary_vals = []
        for row_item in graph_data:
            summary_cols.append(f"{row_item.get('index_num')}日前")
            v = row_item.get("value_coin")
            summary_vals.append(f"{v:+,}" if v != 0 else "0")
        
        df_summary = pd.DataFrame([summary_vals], columns=summary_cols, index=["当日の差枚数"])
        st.dataframe(df_summary, use_container_width=True)
else:
    st.info("☝️ 上のボタンを押すと、最新の合算データをロードします！")

