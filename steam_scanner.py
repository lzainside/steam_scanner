import requests
import json
import time
from datetime import datetime

class SteamGameScanner:
    def __init__(self, api_key, steam_id):
        self.api_key = api_key
        self.steam_id = steam_id
        self.base_url = "http://api.steampowered.com"
        
    def get_owned_games(self):
        """獲取擁有的遊戲列表"""
        url = f"{self.base_url}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            'key': self.api_key,
            'steamid': self.steam_id,
            'format': 'json',
            'include_appinfo': True,
            'include_played_free_games': True
        }
        
        # 重試機制
        for attempt in range(3):
            try:
                print(f"正在獲取遊戲列表... (嘗試 {attempt + 1}/3)")
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = 60 * (attempt + 1)  # 60秒, 120秒, 180秒
                    print(f"API請求過於頻繁，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if 'response' in data and 'games' in data['response']:
                    print(f"✅ 成功獲取 {len(data['response']['games'])} 個遊戲")
                    return data['response']['games']
                else:
                    print("無法獲取遊戲資料，請檢查API key和Steam ID是否正確")
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"API請求失敗 (嘗試 {attempt + 1}/3): {e}")
                if attempt < 2:  # 不是最後一次嘗試
                    wait_time = 30 * (attempt + 1)
                    print(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    print("所有重試都失敗了")
                    return []
    
    def get_player_summary(self):
        """獲取玩家基本資訊"""
        url = f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            'key': self.api_key,
            'steamids': self.steam_id
        }
        
        # 重試機制
        for attempt in range(3):
            try:
                print(f"正在獲取玩家資訊... (嘗試 {attempt + 1}/3)")
                
                # 添加延遲避免API限制
                if attempt > 0:
                    time.sleep(2)
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = 60 * (attempt + 1)  # 60秒, 120秒, 180秒
                    print(f"API請求過於頻繁，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if 'response' in data and 'players' in data['response'] and len(data['response']['players']) > 0:
                    print("✅ 成功獲取玩家資訊")
                    return data['response']['players'][0]
                else:
                    print("⚠️ 無法獲取玩家資訊，但會繼續處理遊戲列表")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"獲取玩家資訊失敗 (嘗試 {attempt + 1}/3): {e}")
                if attempt < 2:  # 不是最後一次嘗試
                    wait_time = 30 * (attempt + 1)
                    print(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    print("⚠️ 無法獲取玩家資訊，但會繼續處理遊戲列表")
                    return None
    
    def minutes_to_hours(self, minutes):
        """將分鐘轉換為小時"""
        if minutes == 0:
            return "0 小時"
        
        hours = minutes / 60
        if hours < 1:
            return f"{minutes} 分鐘"
        elif hours == int(hours):
            return f"{int(hours)} 小時"
        else:
            return f"{hours:.1f} 小時"
    
    def generate_markdown_report(self, output_file="steam_games_report.md"):
        """生成Markdown報告"""
        print("=== 開始掃描Steam遊戲庫 ===")
        print("提示：如果遇到API限制，程式會自動等待並重試")
        print()
        
        # 先獲取遊戲列表（這是主要資料）
        games = self.get_owned_games()
        
        if not games:
            print("❌ 無法獲取遊戲資料，請檢查:")
            print("1. API Key是否正確")
            print("2. Steam ID是否正確") 
            print("3. Steam個人檔案是否設為公開")
            print("4. 網路連線是否正常")
            return
        
        print(f"⏳ 等待5秒後獲取玩家資訊...")
        time.sleep(5)  # 在兩個API請求之間等待
        
        # 獲取玩家資訊（次要資料，失敗也能繼續）
        player_info = self.get_player_summary()
        
        # 按遊戲時間排序（從高到低）
        games.sort(key=lambda x: x.get('playtime_forever', 0), reverse=True)
        
        # 生成Markdown內容
        markdown_content = []
        
        # 標題和基本資訊
        markdown_content.append("# Steam 遊戲庫報告")
        markdown_content.append("")
        markdown_content.append(f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if player_info:
            markdown_content.append(f"**玩家名稱**: {player_info.get('personaname', 'Unknown')}")
            markdown_content.append(f"**Steam ID**: {self.steam_id}")
        
        markdown_content.append(f"**遊戲總數**: {len(games)}")
        
        # 計算總遊戲時間
        total_minutes = sum(game.get('playtime_forever', 0) for game in games)
        markdown_content.append(f"**總遊戲時間**: {self.minutes_to_hours(total_minutes)}")
        markdown_content.append("")
        
        # 統計資訊
        played_games = [game for game in games if game.get('playtime_forever', 0) > 0]
        unplayed_games = [game for game in games if game.get('playtime_forever', 0) == 0]
        
        markdown_content.append("## 📊 統計資訊")
        markdown_content.append("")
        markdown_content.append(f"- **已遊玩遊戲**: {len(played_games)} 款")
        markdown_content.append(f"- **未遊玩遊戲**: {len(unplayed_games)} 款")
        
        if played_games:
            avg_playtime = total_minutes / len(played_games)
            markdown_content.append(f"- **平均遊戲時間**: {self.minutes_to_hours(avg_playtime)}")
        
        markdown_content.append("")
        
        # 最多遊戲時間的前10名
        top_games = games[:10]
        if top_games and top_games[0].get('playtime_forever', 0) > 0:
            markdown_content.append("## 🏆 遊戲時間排行榜 (前10名)")
            markdown_content.append("")
            
            for i, game in enumerate(top_games, 1):
                playtime = game.get('playtime_forever', 0)
                if playtime > 0:
                    game_name = game.get('name', 'Unknown Game')
                    playtime_str = self.minutes_to_hours(playtime)
                    markdown_content.append(f"{i}. **{game_name}** - {playtime_str}")
            
            markdown_content.append("")
        
        # 完整遊戲列表
        markdown_content.append("## 🎮 完整遊戲列表")
        markdown_content.append("")
        
        # 已遊玩的遊戲
        if played_games:
            markdown_content.append("### 已遊玩遊戲")
            markdown_content.append("")
            markdown_content.append("| 遊戲名稱 | 遊戲時間 | App ID |")
            markdown_content.append("|----------|----------|--------|")
            
            for game in played_games:
                name = game.get('name', 'Unknown Game')
                playtime = self.minutes_to_hours(game.get('playtime_forever', 0))
                app_id = game.get('appid', 'N/A')
                markdown_content.append(f"| {name} | {playtime} | {app_id} |")
            
            markdown_content.append("")
        
        # 未遊玩的遊戲
        if unplayed_games:
            markdown_content.append("### 未遊玩遊戲")
            markdown_content.append("")
            markdown_content.append("| 遊戲名稱 | App ID |")
            markdown_content.append("|----------|--------|")
            
            for game in unplayed_games:
                name = game.get('name', 'Unknown Game')
                app_id = game.get('appid', 'N/A')
                markdown_content.append(f"| {name} | {app_id} |")
        
        # 寫入檔案
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(markdown_content))
            
            print(f"✅ 報告已生成: {output_file}")
            print(f"📊 總共掃描了 {len(games)} 款遊戲")
            print(f"⏱️ 總遊戲時間: {self.minutes_to_hours(total_minutes)}")
            
        except Exception as e:
            print(f"❌ 寫入檔案時發生錯誤: {e}")

def main():
    print("=== Steam 遊戲庫掃描器 ===")
    print()
    
    # 提示用戶輸入必要資訊
    print("請先準備以下資訊:")
    print("1. Steam Web API Key (從 https://steamcommunity.com/dev/apikey 獲取)")
    print("2. 你的 Steam ID (可以從 https://steamid.io/ 查詢)")
    print()
    
    api_key = input("請輸入你的 Steam API Key: ").strip()
    steam_id = input("請輸入你的 Steam ID: ").strip()
    
    if not api_key or not steam_id:
        print("❌ API Key 和 Steam ID 都不能為空")
        return
    
    output_file = input("請輸入輸出檔案名稱 (預設: steam_games_report.md): ").strip()
    if not output_file:
        output_file = "steam_games_report.md"
    
    # 創建掃描器並生成報告
    scanner = SteamGameScanner(api_key, steam_id)
    scanner.generate_markdown_report(output_file)

if __name__ == "__main__":
    main()