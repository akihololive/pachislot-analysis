import os
import re
import json

# 💡 各店舗のフォルダ名マッピング
shop_map = {
    "アイランド秋葉原店": "island",
    "エスパス秋橋原店": "espace",
    "マルハン池袋SB": "maruhan_ikebukuro_sb",
    "マルハン東宝新宿": "maruhan_shinjuku",
    "エクサファースト": "exa",
    "マルハン池袋店": "maruhan_ikebukuro",
    "エスパス上野本館": "espace_ueno",
    "楽園アメ横店": "rakuen_ameyoko"
}

data_dir = "data"
combined_result = dict()

# 8店舗のフォルダを巡回
for shop_name, folder_name in shop_map.items():
    folder_path = os.path.join(data_dir, folder_name)
    if not os.path.exists(folder_path):
        continue
        
    # フォルダ内の.txtファイルを日付の新しい順に最大10日分取得
    all_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".txt")], reverse=True)
    target_files = all_files[:10]
    
    if not target_files:
        continue
        
    # 最新10ファイルの「何日前」マッピングを作成
    day_mapping = {fname: (idx + 1) for idx, fname in enumerate(target_files)}
    
    # 店舗ごとにデータをパース
    for fname in target_files:
        day_num = day_mapping.get(fname)
        file_path = os.path.join(folder_path, fname)
        
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or "機種" in line or "台番" in line:
                continue
            parts = re.split(r"\t+|\s{2,}", line)
            
            if len(parts) >= 3:
                name = parts.pop(0).strip()
                table_text = parts.pop(0).strip()
                coin_text = parts.pop(0).strip()
                clean_coin = coin_text.replace("枚", "").replace(",", "").replace("+", "").strip()
                
                try:
                    coin, table_num = int(clean_coin), int(table_text)
                    
                    # 💡 一括表示で重複しないよう、店舗名と台番号を組み合わせた一意のキーを作成
                    unique_key = f"{shop_name}_{table_num}"
                    
                    if not combined_result.get(unique_key):
                        combined_result[unique_key] = {
                            "shop_name": shop_name,
                            "table_num": table_num,
                            "name": name,
                            "history": dict()
                        }
                    combined_result.get(unique_key).get("history")[day_num] = coin
                except ValueError:
                    continue

# 💡 全データを1つにまとめた超軽量JSONファイルを書き出す
output_path = "all_shops_10days.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(combined_result, f, ensure_ascii=False, indent=2)

print("🎉 全店舗の直近10日分のデータを all_shops_10days.json に一本化しました！")
