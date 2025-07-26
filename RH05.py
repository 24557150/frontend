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

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow 未安裝，將無法獲取圖片詳細信息", file=sys.stderr)


class RunningHubImageProcessor:
    """RunningHub 圖像處理器"""
    
    def __init__(self, api_key: str = None, workflow_id: str = None, 
                 load_image_node_id: str = "65", base_url: str = "https://api.runninghub.ai"):
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

    def process_image(self, image_path: str, prompt_text: str = "", 
                     output_dir: str = "outputs", max_wait_time: int = 300) -> bool:
        """
        完整的圖片處理流程 (直接調用 RunningHub API)
        
        Args:
            image_path: 輸入圖片路徑
            prompt_text: 提示詞
            output_dir: 輸出目錄
            max_wait_time: 最大等待時間 (此處主要用於 API 調用超時)
            
        Returns:
            是否處理成功
        """
        print("🎨 RunningHub 圖生圖 AI 處理器 (直接 API 調用模式)", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        
        # 驗證檔案
        is_valid, error_msg = self.validate_file(image_path)
        if not is_valid:
            print(f"❌ 檔案驗證失敗: {error_msg}", file=sys.stderr)
            return False
            
        # 顯示圖片資訊
        self.print_image_info(image_path)

        # --- 新增: 圖片壓縮 ---
        processed_image_path = self._compress_image(image_path, max_size_mb=8.0)
        # --- 結束新增 ---

        try:
            # --- 呼叫 RunningHub API ---
            # 這裡使用 workflow_id 和 load_image_node_id 來構建 API 請求
            # RunningHub 的 /process 接口通常會直接處理圖片並返回結果
            # 根據 RH05a.py 的邏輯，我們需要上傳圖片和 prompt
            
            headers = {"x-api-key": self.api_key}
            files = {"image": open(processed_image_path, "rb")} # 使用壓縮後的圖片
            data = {
                "prompt": prompt_text,
                "workflowId": self.workflow_id, # 傳遞 workflowId
                "loadImageNodeId": self.load_image_node_id # 傳遞 loadImageNodeId
            }
            
            print(f"DEBUG: 正在向 RunningHub API ({self.base_url}/process) 發送請求...", file=sys.stderr)
            response = self.session.post(
                f"{self.base_url}/process", # 假設這是直接處理的 API 端點
                headers=headers,
                files=files,
                data=data,
                timeout=max_wait_time # 使用 max_wait_time 作為 API 調用超時
            )
            
            print(f"DEBUG: RunningHub API 狀態碼 {response.status_code}", file=sys.stderr)
            
            if response.status_code == 200:
                # 確保輸出目錄存在
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                
                # 從響應中獲取圖片內容
                # 假設 RunningHub 直接返回圖片二進制數據
                output_filename = f"pose_corrected_{uuid.uuid4().hex}.png" # 固定為 PNG
                out_path = Path(output_dir) / output_filename
                
                with open(out_path, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ 姿勢矯正成功，結果保存到: {out_path}", file=sys.stderr)
                return True
            else:
                # --- 修改這裡：打印完整的響應內容 ---
                print(f"ERROR: RunningHub API 回傳錯誤: {response.status_code} - {response.text}", file=sys.stderr)
                return False
        except requests.exceptions.Timeout as e:
            print(f"ERROR: RunningHub API 請求超時: {e}", file=sys.stderr)
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"ERROR: RunningHub API 連接錯誤: {e}", file=sys.stderr)
            return False
        except requests.RequestException as e:
            print(f"ERROR: RunningHub API 請求失敗: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"CRITICAL ERROR: process_image 執行失敗: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr) # 打印完整堆棧追溯
            return False
        finally:
            # 清理壓縮後的臨時文件，如果它不是原始文件
            if processed_image_path and processed_image_path != image_path and os.path.exists(processed_image_path):
                os.remove(processed_image_path)
                print(f"DEBUG: Cleaned up compressed temporary file: {processed_image_path}", file=sys.stderr)

    # 移除原有的 upload_image, create_task, check_task_status, wait_for_completion, get_task_results, download_image, save_results 方法
    # 因為我們現在直接使用 /process 接口

    def cancel_task(self, task_id: str = None) -> bool:
        """
        取消任務 (此方法可能不再適用於直接調用 /process 接口的模式，但保留以防萬一)
        
        Args:
            task_id: 任務 ID，默認為當前任務
            
        Returns:
            是否取消成功
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


def main():
    """主函數 (用於本地測試，Cloud Run 不會直接調用)"""
    parser = argparse.ArgumentParser(
        description="RunningHub 圖生圖 AI - Python 版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s image.jpg                                    # 基本處理
  %(prog)s image.jpg -p "beautiful artwork, detailed"  # 使用提示詞
  %(prog)s image.jpg -o ./results                       # 指定輸出目錄
  %(prog)s image.jpg -k YOUR_API_KEY                    # 提供 API Key
        """
    )
    
    parser.add_argument(
        'image_path',
        help='輸入圖片路徑'
    )
    
    parser.add_argument(
        '-p', '--prompt',
        default='姿勢矯正', # 預設提示詞為姿勢矯正
        help='提示詞 (默認: 姿勢矯正)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='outputs',
        help='輸出目錄 (默認: outputs)'
    )
    
    parser.add_argument(
        '-k', '--api-key',
        help='RunningHub API Key'
    )
    
    parser.add_argument(
        '-w', '--workflow-id',
        default='1944945226931953665', # 預設姿勢矯正的 workflow ID
        help='工作流 ID (默認: 1944945226931953665)'
    )
    
    parser.add_argument(
        '-n', '--node-id',
        default='65',
        help='Load Image 節點 ID (默認: 65)'
    )
    
    parser.add_argument(
        '--base-url',
        default='https://api.runninghub.ai', # 調整預設 API URL
        help='API 基礎 URL (默認: https://api.runninghub.ai)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細輸出'
    )
    
    args = parser.parse_args()
    
    # 檢查圖片檔案是否存在
    if not os.path.exists(args.image_path):
        print(f"❌ 圖片檔案不存在: {args.image_path}", file=sys.stderr)
        sys.exit(1)
        
    # 創建處理器
    processor = RunningHubImageProcessor(
        api_key=args.api_key,
        workflow_id=args.workflow_id,
        load_image_node_id=args.node_id,
        base_url=args.base_url
    )
    
    if args.verbose:
        print(f"🔧 配置資訊:")
        print(f"   API Key: {processor.api_key[:8]}..." if processor.api_key else "未設定")
        print(f"   Workflow ID: {processor.workflow_id}")
        print(f"   Load Image 節點 ID: {processor.load_image_node_id}")
        print(f"   基礎 URL: {processor.base_url}")
        print(f"   超時時間: {args.timeout}s")
        print()
    
    try:
        # 執行處理
        success = processor.process_image(
            image_path=args.image_path,
            prompt_text=args.prompt,
            output_dir=args.output,
            max_wait_time=args.timeout
        )
        
        if success:
            print("\n🎊 恭喜！圖片處理完成")
            sys.exit(0)
        else:
            print("\n💔 圖片處理失敗", file=sys.stderr)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷，正在嘗試取消任務...", file=sys.stderr)
        if processor.current_task_id:
            processor.cancel_task()
        print("👋 程序已退出", file=sys.stderr)
        sys.exit(130)
        
    except Exception as e:
        print(f"\n💥 未預期的錯誤: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
