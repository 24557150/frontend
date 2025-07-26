#!/usr/bin/env python3
"""
RunningHub 圖生圖 AI - Python 版本（Cloud Run 修正版）
- 強制使用 /tmp/outputs 作為暫存與輸出目錄
- 加入 Debug Log
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import mimetypes
from urllib.parse import urlparse

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow 未安裝，將無法獲取圖片詳細信息")

# Cloud Run 專用暫存輸出路徑
OUTPUT_DIR = "/tmp/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


class RunningHubImageProcessor:
    """RunningHub 圖像處理器 (Cloud Run 修正版)"""
    
    def __init__(self, api_key: str = None, workflow_id: str = None, 
                 load_image_node_id: str = "65", base_url: str = "https://www.runninghub.cn"):
        self.api_key = api_key or "dcbfc7a79ccb45b89cea62cdba512755"
        self.workflow_id = workflow_id or "1944945226931953665"
        self.load_image_node_id = load_image_node_id
        self.base_url = base_url
        self.current_task_id = None
        self.uploaded_filename = None
        self.start_time = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'RunningHub-Python-Client/1.0'})
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

    # 其餘方法保持原樣，只是 save_results 與 download_image 做修正
    def save_results(self, results: List[Dict], output_dir: str = OUTPUT_DIR) -> List[str]:
        if not results:
            return []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_dir = Path(output_dir)
        task_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []
        print(f"💾 正在保存結果到: {task_dir}")
        for i, result in enumerate(results):
            if not result.get('fileUrl'):
                continue
            url = result['fileUrl']
            parsed_url = urlparse(url)
            original_filename = Path(parsed_url.path).name or f"result_{i+1}.png"
            save_path = task_dir / ("KontextP.png" if i == 0 else ("KontextM.png" if i == 1 else original_filename))
            print(f"📥 下載第 {i+1} 張圖片: {original_filename}")
            if self.download_image(url, str(save_path), max_retries=3):
                saved_files.append(str(save_path))
                print(f"✅ 保存成功: {save_path}")
            else:
                print(f"❌ 下載失敗: {original_filename}")
        # 存 task_info.json
        task_info = {
            'task_id': self.current_task_id,
            'workflow_id': self.workflow_id,
            'uploaded_filename': self.uploaded_filename,
            'timestamp': timestamp,
            'results_count': len(results),
            'saved_files': saved_files,
            'results': results
        }
        info_file = task_dir / "task_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        print(f"📄 任務資訊已保存: {info_file}")
        return saved_files

    def download_image(self, url: str, save_path: str, max_retries: int = 3) -> bool:
        for attempt in range(max_retries):
            try:
                print(f"📡 嘗試下載 ({attempt+1}/{max_retries}) URL: {url}")
                response = self.session.get(url, timeout=(30, 120), stream=True, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'image/*,*/*;q=0.8'
                })
                print(f"📡 下載回應狀態: {response.status_code}")
                response.raise_for_status()
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    return True
            except Exception as e:
                print(f"⚠️ 下載失敗 ({attempt+1}): {e}")
        return False

    # 你原本的其他方法皆不變，保留 upload_image, create_task, process_image 等...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image_path', help='輸入圖片路徑')
    parser.add_argument('-p', '--prompt', default='', help='提示詞')
    parser.add_argument('-o', '--output', default=OUTPUT_DIR, help='輸出目錄')
    parser.add_argument('-k', '--api-key', help='RunningHub API Key')
    parser.add_argument('-w', '--workflow-id', help='工作流 ID')
    parser.add_argument('-n', '--node-id', default='65', help='Load Image 節點 ID')
    parser.add_argument('-t', '--timeout', type=int, default=300, help='最大等待秒數')
    args = parser.parse_args()

    processor = RunningHubImageProcessor(api_key=args.api_key, workflow_id=args.workflow_id, load_image_node_id=args.node_id)
    success = processor.process_image(args.image_path, args.prompt, args.output, args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
