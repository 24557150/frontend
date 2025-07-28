#!/usr/bin/env python3
"""
RunningHub 圖生圖 AI - Python 版本
專業圖像處理工具，基於 RunningHub API

功能：
- 圖片上傳和處理 (整合圖片壓縮)
- AI 工作流執行
- 任務狀態監控
- 結果下載和保存

作者：AI Assistant
日期：2025-07-26 (整合更新)
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
import traceback # 導入 traceback 模組，用於打印完整堆棧追溯

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow 未安裝，將無法獲取圖片詳細信息", file=sys.stderr)


class RunningHubImageProcessor:
    """RunningHub 圖像處理器"""
    
    def __init__(self, api_key: str = None, workflow_id: str = None, 
                 load_image_node_id: str = "65", base_url: str = "https://www.runninghub.ai"):
        """
        初始化處理器
        
        Args:
            api_key: RunningHub API Key
            workflow_id: 工作流 ID
            load_image_node_id: Load Image 節點 ID
            base_url: API 基礎 URL
        """
        # 使用傳入的 api_key，如果為 None 則使用預設值 (應從環境變數獲取)
        self.api_key = api_key or "dcbfc7a79ccb45b89cea62cdba512755" 
        self.workflow_id = workflow_id or "1944945226931953665" # 姿勢矯正的預設 workflow ID
        self.load_image_node_id = load_image_node_id
        self.base_url = base_url
        
        self.current_task_id = None
        self.uploaded_filename = None
        self.start_time = None
        
        # 創建 session 以重用連接
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RunningHub-Python-Client/1.1' # 更新 User-Agent
        })
        
        # 支援的圖片格式
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'
        }
        
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        驗證檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            (是否有效, 錯誤訊息)
        """
        if not os.path.exists(file_path):
            return False, f"檔案不存在: {file_path}"
            
        file_size = os.path.getsize(file_path)
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file_size > max_size:
            return False, f"檔案大小超過 10MB: {self.format_file_size(file_size)}"
            
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_formats:
            return False, f"不支援的檔案格式: {file_ext}"
            
        # 嘗試檢查是否為有效圖片
        if PIL_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    img.verify()
            except Exception as e:
                return False, f"無效的圖片檔案: {str(e)}"
                
        return True, ""
        
    def get_image_info(self, file_path: str) -> Dict:
        """
        獲取圖片資訊
        
        Args:
            file_path: 圖片路徑
            
        Returns:
            圖片資訊字典
        """
        info = {
            'filename': Path(file_path).name,
            'file_size': os.path.getsize(file_path),
            'format': Path(file_path).suffix.upper().replace('.', ''),
            'mime_type': mimetypes.guess_type(file_path)[0] or 'unknown'
        }
        
        if PIL_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    info.update({
                        'width': img.width,
                        'height': img.height,
                        'mode': img.mode,
                        'aspect_ratio': self.calculate_aspect_ratio(img.width, img.height)
                    })
            except Exception as e:
                print(f"警告: 無法獲取圖片詳細資訊: {e}", file=sys.stderr)
                
        return info
        
    def calculate_aspect_ratio(self, width: int, height: int) -> str:
        """計算長寬比"""
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
            
        divisor = gcd(width, height)
        ratio_w = width // divisor
        ratio_h = height // divisor
        
        # 常見長寬比對照
        common_ratios = {
            (1, 1): "1:1",
            (4, 3): "4:3",
            (3, 2): "3:2",
            (16, 9): "16:9",
            (16, 10): "16:10",
            (21, 9): "21:9",
            (5, 4): "5:4",
            (3, 4): "3:4",
            (2, 3): "2:3",
            (9, 16): "9:16"
        }
        
        if (ratio_w, ratio_h) in common_ratios:
            return common_ratios[(ratio_w, ratio_h)]
            
        # 如果比例數字太大，簡化顯示
        if ratio_w > 100 or ratio_h > 100:
            decimal = round(width / height, 2)
            return f"{decimal}:1"
            
        return f"{ratio_w}:{ratio_h}"
        
    def format_file_size(self, bytes_size: int) -> str:
        """格式化檔案大小"""
        if bytes_size == 0:
            return "0 Bytes"
            
        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB']
        i = min(len(sizes) - 1, int(bytes_size.bit_length() // 10))
        
        if i == 0:
            return f"{bytes_size} {sizes[i]}"
        else:
            size = bytes_size / (k ** i)
            return f"{size:.2f} {sizes[i]}"
            
    def print_image_info(self, file_path: str):
        """打印圖片資訊"""
        info = self.get_image_info(file_path)
        
        print(f"\n📷 圖片資訊:")
        print(f"   檔案名稱: {info['filename']}")
        print(f"   檔案大小: {self.format_file_size(info['file_size'])}")
        print(f"   檔案格式: {info['format']}")
        print(f"   MIME 類型: {info['mime_type']}")
        
        if 'width' in info:
            print(f"   圖片尺寸: {info['width']} × {info['height']} px")
            print(f"   長寬比: {info['aspect_ratio']}")
            print(f"   顏色模式: {info['mode']}")

    def _compress_image(self, image_path: str, max_size_mb: float = 8.0) -> str:
        """
        自動壓縮圖片，避免超過 API 限制。
        如果圖片大小超過 max_size_mb，則縮小圖片並重新保存為 JPEG。
        
        Args:
            image_path: 原始圖片路徑
            max_size_mb: 最大允許的檔案大小 (MB)
            
        Returns:
            壓縮後圖片的路徑 (如果壓縮發生)，否則為原始路徑。
        """
        if not PIL_AVAILABLE:
            print("警告: PIL/Pillow 未安裝，無法壓縮圖片。請安裝 Pillow 以確保圖片能被處理。", file=sys.stderr)
            return image_path

        original_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if original_size_mb <= max_size_mb:
            print(f"DEBUG: 原始圖片大小 {original_size_mb:.2f}MB, 無需壓縮。", file=sys.stderr)
            return image_path

        try:
            img = Image.open(image_path)
            img = img.convert("RGB") # 確保是 RGB 模式，以便保存為 JPEG

            # 計算目標尺寸，使最大邊不超過 1280px，並保持長寬比
            max_dim = 1280
            if img.width > max_dim or img.height > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS) # 使用高質量縮放

            # 創建一個新的臨時檔名，確保不會覆蓋原始檔案
            compressed_path = os.path.join(
                os.path.dirname(image_path),
                f"{Path(image_path).stem}_compressed.jpg"
            )
            
            # 嘗試不同的質量設置來壓縮到目標大小
            quality = 90
            while True:
                img.save(compressed_path, "JPEG", quality=quality)
                current_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
                print(f"DEBUG: 壓縮圖片至 {current_size_mb:.2f}MB (質量: {quality}).", file=sys.stderr)

                if current_size_mb <= max_size_mb or quality <= 30: # 設置最小質量閾值
                    break
                quality -= 5 # 每次降低 5% 質量

            print(f"DEBUG: 圖片已壓縮並保存到 {compressed_path}，大小為 {current_size_mb:.2f}MB。", file=sys.stderr)
            return compressed_path
        except Exception as e:
            print(f"ERROR: 圖片壓縮失敗: {e}", file=sys.stderr)
            return image_path # 壓縮失敗則返回原始路徑

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        上傳圖片到 RunningHub。
        
        Args:
            image_path: 本地圖片路徑。
            
        Returns:
            上傳後的圖片檔案名稱 (例如: "xxxx.jpg")，如果失敗則為 None。
        """
        print(f"DEBUG: 正在上傳圖片 {image_path} 到 RunningHub...", file=sys.stderr)
        try:
            files = {'file': open(image_path, 'rb')}
            headers = {'x-api-key': self.api_key}
            
            response = self.session.post(f"{self.base_url}/file/upload", files=files, headers=headers, timeout=60)
            response.raise_for_status() # 對於 4xx/5xx 響應拋出異常
            
            result = response.json()
            print(f"DEBUG: 上傳響應: {result}", file=sys.stderr)

            if result.get('code') == 0 and result.get('data') and result['data'].get('filename'):
                self.uploaded_filename = result['data']['filename']
                print(f"✅ 圖片上傳成功，檔案名稱: {self.uploaded_filename}", file=sys.stderr)
                return self.uploaded_filename
            else:
                error_msg = result.get('msg', '未知上傳錯誤')
                print(f"❌ 圖片上傳失敗: {error_msg}", file=sys.stderr)
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 上傳圖片請求失敗: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ 上傳圖片時發生錯誤: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None

    def create_task(self, uploaded_filename: str, prompt_text: str = "") -> Optional[str]:
        """
        創建 RunningHub 任務。
        
        Args:
            uploaded_filename: 已上傳的圖片檔案名稱。
            prompt_text: 提示詞。
            
        Returns:
            任務 ID，如果失敗則為 None。
        """
        print(f"DEBUG: 正在創建 RunningHub 任務，使用圖片: {uploaded_filename}, 提示詞: '{prompt_text}'", file=sys.stderr)
        try:
            payload = {
                "workflowId": self.workflow_id,
                "workflowInput": {
                    self.load_image_node_id: { # Load Image 節點的 ID
                        "filename": uploaded_filename
                    },
                    "13": { # 假設這是 prompt 的節點 ID
                        "text": prompt_text
                    }
                }
            }
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = self.session.post(f"{self.base_url}/task/openapi/create", json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            print(f"DEBUG: 創建任務響應: {result}", file=sys.stderr)

            if result.get('code') == 0 and result.get('data') and result['data'].get('taskId'):
                self.current_task_id = result['data']['taskId']
                print(f"✅ 任務創建成功，任務 ID: {self.current_task_id}", file=sys.stderr)
                return self.current_task_id
            else:
                error_msg = result.get('msg', '未知任務創建錯誤')
                print(f"❌ 任務創建失敗: {error_msg}", file=sys.stderr)
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 創建任務請求失敗: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ 創建任務時發生錯誤: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None

    def check_task_status(self, task_id: str) -> Optional[str]:
        """
        檢查任務狀態。
        
        Args:
            task_id: 任務 ID。
            
        Returns:
            任務狀態 (例如: "success", "failed", "running", "pending")，如果失敗則為 None。
        """
        try:
            params = {'taskId': task_id}
            headers = {'x-api-key': self.api_key}
            
            response = self.session.get(f"{self.base_url}/task/openapi/status", params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            # print(f"DEBUG: 任務狀態響應: {result}", file=sys.stderr) # 避免過於頻繁的日誌

            if result.get('code') == 0 and result.get('data') and result['data'].get('status'):
                status = result['data']['status']
                return status
            else:
                error_msg = result.get('msg', '未知狀態查詢錯誤')
                print(f"❌ 查詢任務狀態失敗: {error_msg}", file=sys.stderr)
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 查詢任務狀態請求失敗: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ 查詢任務狀態時發生錯誤: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None

    def wait_for_completion(self, task_id: str, max_wait_time: int = 300, poll_interval: int = 5) -> bool:
        """
        等待任務完成。
        
        Args:
            task_id: 任務 ID。
            max_wait_time: 最大等待時間 (秒)。
            poll_interval: 輪詢間隔 (秒)。
            
        Returns:
            如果任務成功完成則為 True，否則為 False。
        """
        self.start_time = time.time()
        print(f"DEBUG: 正在等待任務 {task_id} 完成 (最長等待 {max_wait_time} 秒)...", file=sys.stderr)
        
        while time.time() - self.start_time < max_wait_time:
            status = self.check_task_status(task_id)
            if status == "success":
                print(f"✅ 任務 {task_id} 成功完成。", file=sys.stderr)
                return True
            elif status == "failed":
                print(f"❌ 任務 {task_id} 失敗。", file=sys.stderr)
                return False
            elif status is None: # 查詢狀態本身失敗
                print(f"WARN: 無法獲取任務 {task_id} 的狀態，重試中...", file=sys.stderr)
            else:
                elapsed_time = int(time.time() - self.start_time)
                print(f"DEBUG: 任務 {task_id} 狀態: {status} (已等待 {elapsed_time} 秒)", file=sys.stderr)
            
            time.sleep(poll_interval)
            
        print(f"❌ 任務 {task_id} 超時，未在 {max_wait_time} 秒內完成。", file=sys.stderr)
        return False

    def get_task_results(self, task_id: str) -> Optional[List[Dict]]:
        """
        獲取任務結果。
        
        Args:
            task_id: 任務 ID。
            
        Returns:
            結果列表 (包含圖片 URL 等)，如果失敗則為 None。
        """
        print(f"DEBUG: 正在獲取任務 {task_id} 的結果...", file=sys.stderr)
        try:
            params = {'taskId': task_id}
            headers = {'x-api-key': self.api_key}
            
            response = self.session.get(f"{self.base_url}/task/openapi/result", params=params, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            print(f"DEBUG: 獲取結果響應: {result}", file=sys.stderr)

            if result.get('code') == 0 and result.get('data') and result['data'].get('resultList'):
                print(f"✅ 成功獲取任務 {task_id} 的結果。", file=sys.stderr)
                return result['data']['resultList']
            else:
                error_msg = result.get('msg', '未知結果獲取錯誤')
                print(f"❌ 獲取任務結果失敗: {error_msg}", file=sys.stderr)
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 獲取任務結果請求失敗: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ 獲取任務結果時發生錯誤: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None

    def download_image(self, image_url: str, save_path: str) -> bool:
        """
        下載圖片。
        
        Args:
            image_url: 圖片的 URL。
            save_path: 本地保存路徑。
            
        Returns:
            是否下載成功。
        """
        print(f"DEBUG: 正在下載圖片從 {image_url} 到 {save_path}...", file=sys.stderr)
        try:
            response = self.session.get(image_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ 圖片下載成功: {save_path}", file=sys.stderr)
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ 下載圖片請求失敗: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ 下載圖片時發生錯誤: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return False

    def save_results(self, results: List[Dict], output_dir: str = "outputs") -> List[str]:
        """
        保存所有結果圖片。
        
        Args:
            results: 任務結果列表。
            output_dir: 輸出目錄。
            
        Returns:
            保存的本地檔案路徑列表。
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        saved_paths = []
        for i, res in enumerate(results):
            if res.get('type') == 'image' and res.get('url'):
                image_url = res['url']
                # 從 URL 提取檔案名，或生成一個唯一的檔案名
                parsed_url = urlparse(image_url)
                original_filename = Path(parsed_url.path).name
                # 確保檔案名唯一，並固定為 .png 副檔名
                save_filename = f"result_{i}_{uuid.uuid4().hex}_{Path(original_filename).stem}.png"
                save_path = os.path.join(output_dir, save_filename)
                
                if self.download_image(image_url, save_path):
                    saved_paths.append(save_path)
        return saved_paths

    def cancel_task(self, task_id: str = None) -> bool:
        """
        取消任務。
        
        Args:
            task_id: 任務 ID，默認為當前任務。
            
        Returns:
            是否取消成功。
        """
        if not task_id:
            task_id = self.current_task_id
            
        if not task_id:
            print("❌ 沒有可取消的任務", file=sys.stderr)
            return False
            
        try:
            payload = {
                'apiKey': self.api_key,
                'taskId': task_id
            }
            
            response = self.session.post(
                f"{self.base_url}/task/openapi/cancel",
                json=payload,
                timeout=15
            )
            
            result = response.json()
            
            if result.get('code') == 0:
                print(f"✅ 任務已取消: {task_id}", file=sys.stderr)
                return True
            else:
                error_msg = result.get('msg', '未知錯誤')
                print(f"❌ 取消任務失敗: {error_msg}", file=sys.stderr)
                return False
                
        except Exception as e:
            print(f"❌ 取消任務錯誤: {e}", file=sys.stderr)
            return False

# 移除頂層的 main() 函數調用，因為這個檔案現在作為一個模組被導入
# if __name__ == "__main__":
#     main()
