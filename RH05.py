#!/usr/bin/env python3
"""
RunningHub 圖生圖 AI - Python 版本
專業圖像處理工具，基於 RunningHub API

功能：
- 圖片上傳和處理
- AI 工作流執行
- 任務狀態監控
- 結果下載和保存

作者：AI Assistant
日期：2025-07-15
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


class RunningHubImageProcessor:
    """RunningHub 圖像處理器"""
    
    def __init__(self, api_key: str = None, workflow_id: str = None, 
                 load_image_node_id: str = "65", base_url: str = "https://www.runninghub.cn"):
        """
        初始化處理器
        
        Args:
            api_key: RunningHub API Key
            workflow_id: 工作流 ID
            load_image_node_id: Load Image 節點 ID
            base_url: API 基礎 URL
        """
        self.api_key = api_key or "dcbfc7a79ccb45b89cea62cdba512755"
        # 如果沒有指定 workflow_id，就自動抓第一個可用的
        if workflow_id:
            self.workflow_id = workflow_id
        else:
            self.workflow_id = self.get_default_workflow_id()

# 保留 node_id，可手動指定
        self.load_image_node_id = load_image_node_id or "65"

        self.base_url = base_url
        
        self.current_task_id = None
        self.uploaded_filename = None
        self.start_time = None
        
        # 創建 session 以重用連接
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RunningHub-Python-Client/1.0'
        })
        
        # 支援的圖片格式
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'
        }
    
    def get_default_workflow_id(self) -> str:
        """自動取得第一個可用的 Workflow ID"""
        try:
            url = f"{self.base_url}/task/openapi/workflow/list"
            resp = self.session.get(url, params={"apiKey": self.api_key}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                workflows = data.get("data", [])
                if workflows:
                    first_id = workflows[0].get("id")
                    print(f"INFO: 自動取得 Workflow ID: {first_id}")
                    return str(first_id)
                print("WARN: 無法自動獲取 Workflow ID")
            else:
                print(f"ERROR: API 狀態碼 {resp.status_code}")
        except Exception as e:
            print(f"ERROR: 獲取 Workflow ID 失敗: {e}")
        return None
        
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
                print(f"警告: 無法獲取圖片詳細資訊: {e}")
                
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
            
    def upload_image(self, file_path: str) -> Optional[str]:
        """
        上傳圖片到 RunningHub
        
        Args:
            file_path: 圖片檔案路徑
            
        Returns:
            上傳成功返回檔案名，失敗返回 None
        """
        print("📤 正在上傳圖片...")
        
        try:
            # 確保檔案存在
            if not os.path.exists(file_path):
                print(f"❌ 檔案不存在: {file_path}")
                return None
                
            # 獲取檔案資訊
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            filename = Path(file_path).name
            
            print(f"   檔案名稱: {filename}")
            print(f"   檔案大小: {self.format_file_size(file_size)}")
            print(f"   MIME 類型: {mime_type}")
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, mime_type)
                }
                data = {
                    'apiKey': self.api_key,
                    'fileType': 'image'
                }
                
                print(f"   正在上傳到: {self.base_url}/task/openapi/upload")
                
                response = self.session.post(
                    f"{self.base_url}/task/openapi/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                print(f"   HTTP 狀態碼: {response.status_code}")
                
                # 檢查 HTTP 狀態碼
                if response.status_code != 200:
                    print(f"❌ HTTP 錯誤: {response.status_code}")
                    print(f"   響應內容: {response.text[:500]}")
                    return None
                
                result = response.json()
                
            if result.get('code') == 0 and result.get('data', {}).get('fileName'):
                filename = result['data']['fileName']
                self.uploaded_filename = filename
                print(f"✅ 圖片上傳成功: {filename}")
                return filename
            else:
                error_msg = result.get('msg', '未知錯誤')
                error_code = result.get('code', 'N/A')
                print(f"❌ 上傳失敗: {error_msg} (錯誤碼: {error_code})")
                print(f"   完整響應: {result}")
                return None
                
        except requests.exceptions.Timeout as e:
            print(f"❌ 請求超時: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 連接錯誤: {e}")
            return None
        except requests.RequestException as e:
            print(f"❌ 網路錯誤: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ 響應解析錯誤: {e}")
            print(f"   響應內容: {response.text if 'response' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"❌ 上傳錯誤: {e}")
            return None
            
    def create_task(self, filename: str, prompt_text: str = "") -> Optional[str]:
        """
        創建處理任務
        
        Args:
            filename: 上傳的圖片檔名
            prompt_text: 提示詞
            
        Returns:
            任務 ID 或 None
        """
        print("🚀 正在創建 AI 處理任務...")
        
        # 構建節點資訊
        node_info_list = [
            {
                'nodeId': self.load_image_node_id,
                'fieldName': 'image',
                'fieldValue': filename
            }
        ]
        
        # 添加提示詞（如果有）
        if prompt_text.strip():
            prompt_node_ids = ['6', '7', '1', '2', '3']  # 常見的提示詞節點 ID
            for node_id in prompt_node_ids:
                node_info_list.append({
                    'nodeId': node_id,
                    'fieldName': 'text',
                    'fieldValue': prompt_text.strip()
                })
                
        payload = {
            'apiKey': self.api_key,
            'workflowId': self.workflow_id,
            'nodeInfoList': node_info_list
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/task/openapi/create",
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('code') == 0 and result.get('data', {}).get('taskId'):
                task_id = str(result['data']['taskId'])
                self.current_task_id = task_id
                print(f"✅ 任務創建成功")
                print(f"   任務 ID: {task_id}")
                if prompt_text.strip():
                    print(f"   提示詞: {prompt_text}")
                return task_id
            else:
                error_msg = result.get('msg', '未知錯誤')
                print(f"❌ 任務創建失敗: {error_msg}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ 網路錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ 創建任務錯誤: {e}")
            return None
            
    def check_task_status(self, task_id: str) -> Optional[str]:
        """
        檢查任務狀態
        
        Args:
            task_id: 任務 ID
            
        Returns:
            任務狀態或 None
        """
        try:
            payload = {
                'apiKey': self.api_key,
                'taskId': task_id
            }
            
            response = self.session.post(
                f"{self.base_url}/task/openapi/status",
                json=payload,
                timeout=15
            )
            
            result = response.json()
            
            if result.get('code') == 0:
                return result.get('data')
            else:
                return None
                
        except Exception as e:
            print(f"⚠️  狀態檢查錯誤: {e}")
            return None
            
    def wait_for_completion(self, task_id: str, max_wait_time: int = 300) -> bool:
        """
        等待任務完成
        
        Args:
            task_id: 任務 ID
            max_wait_time: 最大等待時間（秒）
            
        Returns:
            是否成功完成
        """
        print("⏳ 等待 AI 處理完成...")
        self.start_time = time.time()
        
        status_map = {
            'QUEUED': {'text': '排隊中', 'icon': '⏳'},
            'RUNNING': {'text': '執行中', 'icon': '⚡'},
            'SUCCESS': {'text': '已完成', 'icon': '✅'},
            'FAILED': {'text': '失敗', 'icon': '❌'}
        }
        
        last_status = None
        
        while time.time() - self.start_time < max_wait_time:
            status = self.check_task_status(task_id)
            
            if status != last_status:
                if status in status_map:
                    status_info = status_map[status]
                    elapsed = int(time.time() - self.start_time)
                    print(f"{status_info['icon']} 狀態: {status_info['text']} (已等待 {elapsed}s)")
                last_status = status
                
            if status == 'SUCCESS':
                elapsed = int(time.time() - self.start_time)
                print(f"🎉 任務完成！總處理時間: {elapsed}s")
                return True
            elif status == 'FAILED':
                print("💥 任務執行失敗")
                return False
                
            time.sleep(2)  # 每 2 秒檢查一次
            
        print(f"⏰ 等待超時 ({max_wait_time}s)")
        return False
        
    def get_task_results(self, task_id: str) -> Optional[List[Dict]]:
        """
        獲取任務結果
        
        Args:
            task_id: 任務 ID
            
        Returns:
            結果列表或 None
        """
        print("📥 正在獲取處理結果...")
        
        try:
            payload = {
                'apiKey': self.api_key,
                'taskId': task_id
            }
            
            response = self.session.post(
                f"{self.base_url}/task/openapi/outputs",
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('code') == 0 and result.get('data'):
                results = result['data']
                print(f"✅ 成功獲取 {len(results)} 個結果")
                
                # 等待一下讓服務器準備好圖片文件
                if results:
                    print("⏳ 等待服務器準備圖片文件...")
                    time.sleep(3)
                
                return results
            else:
                error_msg = result.get('msg', '未知錯誤')
                print(f"❌ 獲取結果失敗: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ 獲取結果錯誤: {e}")
            return None
            
    def download_image(self, url: str, save_path: str, max_retries: int = 3) -> bool:
        """
        下載圖片（帶重試機制）
        
        Args:
            url: 圖片 URL
            save_path: 保存路徑
            max_retries: 最大重試次數
            
        Returns:
            是否下載成功
        """
        # 下載前延遲1秒
        time.sleep(1)
        
        for attempt in range(max_retries):
            try:
                # 如果不是第一次嘗試，額外等待
                if attempt > 0:
                    wait_time = 2 ** attempt  # 指數退避：2, 4, 8秒
                    print(f"   ⏳ 第 {attempt + 1} 次重試，等待 {wait_time}s...")
                    time.sleep(wait_time)
                
                # 設置更長的超時時間和更完整的 headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                }
                
                response = self.session.get(
                    url, 
                    timeout=(30, 120),  # (連接超時, 讀取超時)
                    stream=True,
                    headers=headers,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # 檢查內容類型
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"   ⚠️  警告: 響應不是圖片格式 ({content_type})")
                
                # 創建目錄
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # 下載文件
                with open(save_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # 過濾空chunk
                            f.write(chunk)
                            downloaded += len(chunk)
                
                # 驗證下載的文件
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    return True
                else:
                    print(f"   ⚠️  下載的文件為空或不存在")
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    continue
                    
            except requests.exceptions.Timeout as e:
                print(f"   ⏰ 超時錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"   🔌 連接錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"   🔍 圖片未找到 (嘗試 {attempt + 1}/{max_retries}): 可能還在生成中...")
                else:
                    print(f"   📡 HTTP錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                print(f"   💥 未知錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            
            # 如果不是最後一次嘗試，清理可能的部分下載文件
            if attempt < max_retries - 1 and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except:
                    pass
        
        print(f"❌ 下載失敗: 已重試 {max_retries} 次")
        return False
            
    def save_results(self, results: List[Dict], output_dir: str = "outputs") -> List[str]:
        """
        保存處理結果
        
        Args:
            results: 結果列表
            output_dir: 輸出目錄
            
        Returns:
            保存的檔案路徑列表
        """
        if not results:
            return []
            
        # 創建輸出目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_dir = Path(output_dir) # Path(output_dir) / f"task_{self.current_task_id}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        print(f"💾 正在保存結果到: {task_dir}")
        
        # 顯示所有結果的 URL 用於調試
        print("🔍 檢查結果 URL:")
        for i, result in enumerate(results):
            url = result.get('fileUrl', 'N/A')
            print(f"   第 {i+1} 張: {url}")
        print()
        
        for i, result in enumerate(results):
            if not result.get('fileUrl'):
                continue
                
            # 從 URL 提取檔名
            url = result['fileUrl']
            parsed_url = urlparse(url)
            original_filename = Path(parsed_url.path).name
            
            if not original_filename:
                original_filename = f"result_{i+1}.png"
                
            save_path = task_dir / original_filename
            if i == 0:
                save_path = task_dir / "KontextP.png"
            elif i == 1:
                save_path = task_dir / "KontextM.png"

            print(f"📥 下載第 {i+1} 張圖片: {original_filename}")
            
            if self.download_image(url, str(save_path), max_retries=3):
                saved_files.append(str(save_path))
                print(f"✅ 保存成功: {save_path}")
                
                # 打印圖片資訊
                if PIL_AVAILABLE and save_path.exists():
                    try:
                        with Image.open(save_path) as img:
                            print(f"   尺寸: {img.width} × {img.height} px")
                            print(f"   格式: {img.format}")
                            print(f"   檔案大小: {self.format_file_size(os.path.getsize(save_path))}")
                    except:
                        pass
            else:
                print(f"❌ 下載失敗: {original_filename}")
                
        # 保存任務資訊
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
        print(f"🎯 共保存 {len(saved_files)} 張圖片")
        
        return saved_files
        
    def process_image(self, image_path: str, prompt_text: str = "", 
                     output_dir: str = "outputs", max_wait_time: int = 300) -> bool:
        """
        完整的圖片處理流程
        
        Args:
            image_path: 輸入圖片路徑
            prompt_text: 提示詞
            output_dir: 輸出目錄
            max_wait_time: 最大等待時間
            
        Returns:
            是否處理成功
        """
        print("🎨 RunningHub 圖生圖 AI 處理器")
        print("=" * 50)
        
        # 驗證檔案
        is_valid, error_msg = self.validate_file(image_path)
        if not is_valid:
            print(f"❌ 檔案驗證失敗: {error_msg}")
            return False
            
        # 顯示圖片資訊
        self.print_image_info(image_path)
        
        # 上傳圖片
        filename = self.upload_image(image_path)
        if not filename:
            return False
            
        # 創建任務
        task_id = self.create_task(filename, prompt_text)
        if not task_id:
            return False
            
        # 等待完成
        if not self.wait_for_completion(task_id, max_wait_time):
            return False
            
        # 獲取結果
        results = self.get_task_results(task_id)
        if not results:
            return False
            
        # 保存結果
        saved_files = self.save_results(results, output_dir)
        
        print("\n" + "=" * 50)
        print(f"🎉 處理完成！成功生成 {len(saved_files)} 張圖片")
        
        return len(saved_files) > 0
        
    def cancel_task(self, task_id: str = None) -> bool:
        """
        取消任務
        
        Args:
            task_id: 任務 ID，默認為當前任務
            
        Returns:
            是否取消成功
        """
        if not task_id:
            task_id = self.current_task_id
            
        if not task_id:
            print("❌ 沒有可取消的任務")
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
                print(f"✅ 任務已取消: {task_id}")
                return True
            else:
                error_msg = result.get('msg', '未知錯誤')
                print(f"❌ 取消任務失敗: {error_msg}")
                return False
                
        except Exception as e:
            print(f"❌ 取消任務錯誤: {e}")
            return False


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="RunningHub 圖生圖 AI - Python 版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s image.jpg                                    # 基本處理
  %(prog)s image.jpg -p "beautiful artwork, detailed"  # 使用提示詞
  %(prog)s image.jpg -o ./results                       # 指定輸出目錄
  %(prog)s image.jpg -w 123456789 -n 65                # 自定義工作流
  %(prog)s image.jpg -t 600                             # 設定超時時間
        """
    )
    
    parser.add_argument(
        'image_path',
        help='輸入圖片路徑'
    )
    
    parser.add_argument(
        '-p', '--prompt',
        default='',
        help='提示詞 (可選)'
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
        help='工作流 ID'
    )
    
    parser.add_argument(
        '-n', '--node-id',
        default='65',
        help='Load Image 節點 ID (默認: 65)'
    )
    
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=300,
        help='最大等待時間，秒 (默認: 300)'
    )
    
    parser.add_argument(
        '--base-url',
        default='https://www.runninghub.cn',
        help='API 基礎 URL (默認: https://www.runninghub.cn)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細輸出'
    )
    
    args = parser.parse_args()
    
    # 檢查圖片檔案是否存在
    if not os.path.exists(args.image_path):
        print(f"❌ 圖片檔案不存在: {args.image_path}")
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
            print("\n💔 圖片處理失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷，正在嘗試取消任務...")
        if processor.current_task_id:
            processor.cancel_task()
        print("👋 程序已退出")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n💥 未預期的錯誤: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
