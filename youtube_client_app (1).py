#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Downloader Client
מוריד סרטונים מיוטיוב דרך שרת פרטי - עוקף חסימות רשת
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import os
import json
import webbrowser
from urllib.parse import urlparse
from datetime import datetime
import sys

class YouTubeDownloader:
    def __init__(self):
        self.server_url = self.load_server_config()
        self.setup_gui()
        
    def load_server_config(self):
        """טוען הגדרות שרת מקובץ קונפיגורציה"""
        config_file = 'config.json'
        default_config = {
            'server_url': 'http://YOUR_SERVER_IP:5000',
            'download_dir': os.path.expanduser('~/Downloads'),
            'default_quality': 'best'
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('server_url', default_config['server_url'])
            else:
                # יצירת קובץ קונפיגורציה חדש
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                return default_config['server_url']
        except Exception:
            return default_config['server_url']
    
    def save_server_config(self, server_url):
        """שומר הגדרות שרת"""
        try:
            config = {'server_url': server_url}
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['server_url'] = server_url
            
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("YouTube Downloader - מוריד סרטונים")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Download tab
        self.download_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.download_frame, text="הורדה")
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_frame, text="הגדרות")
        
        self.setup_download_tab()
        self.setup_settings_tab()
        
    def setup_download_tab(self):
        # Title
        title_label = ttk.Label(self.download_frame, text="🎬 מוריד סרטונים מיוטיוב", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # URL input section
        url_section = ttk.LabelFrame(self.download_frame, text="📎 קישור הסרטון", padding="10")
        url_section.pack(fill=tk.X, pady=(0, 10))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_section, textvariable=self.url_var, font=('Arial', 11))
        self.url_entry.pack(fill=tk.X, pady=(5, 10))
        
        # URL buttons
        url_buttons_frame = ttk.Frame(url_section)
        url_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(url_buttons_frame, text="📋 הדבק מהלוח", 
                  command=self.paste_from_clipboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(url_buttons_frame, text="🔍 מידע על הסרטון", 
                  command=self.get_video_info).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(url_buttons_frame, text="🌐 פתח ביוטיוב", 
                  command=self.open_youtube).pack(side=tk.LEFT)
        
        # Options section
        options_section = ttk.LabelFrame(self.download_frame, text="⚙️ אפשרויות הורדה", padding="10")
        options_section.pack(fill=tk.X, pady=(0, 10))
        
        options_grid = ttk.Frame(options_section)
        options_grid.pack(fill=tk.X)
        
        # Quality selection
        ttk.Label(options_grid, text="איכות וידאו:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(options_grid, textvariable=self.quality_var, width=15,
                                   values=["best", "1080p", "720p", "480p", "360p", "worst"])
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Format selection
        ttk.Label(options_grid, text="פורמט:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.format_var = tk.StringVar(value="video")
        format_combo = ttk.Combobox(options_grid, textvariable=self.format_var, width=15,
                                   values=["video", "audio_mp3", "audio_m4a"])
        format_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Download directory
        dir_section = ttk.LabelFrame(self.download_frame, text="📁 תיקיית שמירה", padding="10")
        dir_section.pack(fill=tk.X, pady=(0, 10))
        
        dir_frame = ttk.Frame(dir_section)
        dir_frame.pack(fill=tk.X)
        
        self.download_dir_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.download_dir_var, font=('Arial', 10))
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(dir_frame, text="📂 בחר תיקיה", 
                  command=self.select_directory).pack(side=tk.RIGHT)
        
        # Download button
        download_section = ttk.Frame(self.download_frame)
        download_section.pack(fill=tk.X, pady=(0, 10))
        
        self.download_button = ttk.Button(download_section, text="⬇️ הורד עכשיו", 
                                        command=self.start_download, 
                                        style='Accent.TButton')
        self.download_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress section
        progress_section = ttk.LabelFrame(self.download_frame, text="📊 התקדמות", padding="10")
        progress_section.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="✅ מוכן להורדה")
        progress_label = ttk.Label(progress_section, textvariable=self.progress_var)
        progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_section, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X)
        
        # Log section
        log_section = ttk.LabelFrame(self.download_frame, text="📝 יומן פעילות", padding="10")
        log_section.pack(fill=tk.BOTH, expand=True)
        
        log_frame = ttk.Frame(log_section)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add initial log message
        self.log_message("🚀 יוטיוב דאונלודר מוכן לפעולה!")
        self.log_message(f"🔗 מחובר לשרת: {self.server_url}")
        
    def setup_settings_tab(self):
        # Server settings
        server_section = ttk.LabelFrame(self.settings_frame, text="🖥️ הגדרות שרת", padding="15")
        server_section.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(server_section, text="כתובת השרת:").pack(anchor=tk.W, pady=(0, 5))
        
        server_frame = ttk.Frame(server_section)
        server_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.server_url_var = tk.StringVar(value=self.server_url)
        server_entry = ttk.Entry(server_frame, textvariable=self.server_url_var, font=('Consolas', 10))
        server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(server_frame, text="💾 שמור", 
                  command=self.save_server_settings).pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Button(server_frame, text="🔍 בדוק", 
                  command=self.test_server_connection).pack(side=tk.RIGHT)
        
        # Server status
        self.server_status_var = tk.StringVar(value="❓ לא נבדק")
        status_label = ttk.Label(server_section, textvariable=self.server_status_var)
        status_label.pack(anchor=tk.W)
        
        # Application info
        info_section = ttk.LabelFrame(self.settings_frame, text="ℹ️ מידע על היישום", padding="15")
        info_section.pack(fill=tk.X, pady=(0, 15))
        
        info_text = """🎯 YouTube Downloader
        
📌 גרסה: 1.0
👨‍💻 מפתח: Assistant
📅 תאריך: """ + datetime.now().strftime("%d/%m/%Y") + """

🔧 תכונות:
• הורדת סרטונים באיכויות שונות
• המרה לפורמטי אודיו
• עקיפת חסימות רשת
• ממשק בעברית

⚠️ הערות חשובות:
• וודא שהשרת פועל ונגיש
• השתמש באופן חוקי ואתי
• כבד זכויות יוצרים"""
        
        info_label = ttk.Label(info_section, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.settings_frame)
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(buttons_frame, text="🗂️ פתח תיקיית הורדות", 
                  command=self.open_downloads_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="🔄 איפוס הגדרות", 
                  command=self.reset_settings).pack(side=tk.LEFT)
        
    def paste_from_clipboard(self):
        """הדבקה מהלוח"""
        try:
            clipboard_content = self.root.clipboard_get()
            if 'youtube.com' in clipboard_content or 'youtu.be' in clipboard_content:
                self.url_var.set(clipboard_content.strip())
                self.log_message("📋 קישור הודבק מהלוח")
            else:
                messagebox.showwarning("אזהרה", "הלוח לא מכיל קישור יוטיוב תקין")
        except tk.TclError:
            messagebox.showwarning("אזהרה", "הלוח ריק או לא נגיש")
    
    def open_youtube(self):
        """פתיחת יוטיוב בדפדפן"""
        url = self.url_var.get().strip()
        if url:
            webbrowser.open(url)
        else:
            webbrowser.open("https://www.youtube.com")
    
    def select_directory(self):
        """בחירת תיקיית הורדה"""
        directory = filedialog.askdirectory(initialdir=self.download_dir_var.get())
        if directory:
            self.download_dir_var.set(directory)
            self.log_message(f"📁 תיקיית הורדה שונתה ל: {directory}")
    
    def open_downloads_folder(self):
        """פתיחת תיקיית ההורדות"""
        download_dir = self.download_dir_var.get()
        if os.path.exists(download_dir):
            if sys.platform.startswith('win'):
                os.startfile(download_dir)
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{download_dir}"')
            else:
                os.system(f'xdg-open "{download_dir}"')
        else:
            messagebox.showerror("שגיאה", "תיקיית ההורדות לא קיימת")
    
    def log_message(self, message):
        """הוספת הודעה ליומן"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def test_server_connection(self):
        """בדיקת חיבור לשרת"""
        def test_connection():
            try:
                self.server_status_var.set("🔄 בודק חיבור...")
                server_url = self.server_url_var.get().strip().rstrip('/')
                
                response = requests.get(f"{server_url}/health", timeout=10)
                
                if response.status_code == 200:
                    self.server_status_var.set("✅ השרת זמין ופועל")
                    self.log_message("✅ חיבור לשרת תקין")
                else:
                    self.server_status_var.set("❌ השרת לא מגיב כראוי")
                    self.log_message("❌ השרת מחזיר שגיאה")
                    
            except requests.exceptions.Timeout:
                self.server_status_var.set("⏰ זמן החיבור פג")
                self.log_message("⏰ זמן החיבור לשרת פג")
            except requests.exceptions.ConnectionError:
                self.server_status_var.set("🔌 לא ניתן להתחבר לשרת")
                self.log_message("🔌 בעיית חיבור לשרת")
            except Exception as e:
                self.server_status_var.set(f"❌ שגיאה: {str(e)[:30]}")
                self.log_message(f"❌ שגיאה בבדיקת חיבור: {str(e)}")
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def save_server_settings(self):
        """שמירת הגדרות שרת"""
        new_url = self.server_url_var.get().strip().rstrip('/')
        if new_url:
            self.server_url = new_url
            self.save_server_config(new_url)
            self.log_message(f"💾 כתובת השרת נשמרה: {new_url}")
            messagebox.showinfo("הצלחה", "הגדרות השרת נשמרו בהצלחה")
        else:
            messagebox.showerror("שגיאה", "כתובת השרת לא יכולה להיות ריקה")
    
    def reset_settings(self):
        """איפוס הגדרות"""
        if messagebox.askyesno("אישור", "האם אתה בטוח שברצונך לאפס את כל ההגדרות?"):
            try:
                if os.path.exists('config.json'):
                    os.remove('config.json')
                self.server_url = "http://YOUR_SERVER_IP:5000"
                self.server_url_var.set(self.server_url)
                self.download_dir_var.set(os.path.expanduser("~/Downloads"))
                self.quality_var.set("best")
                self.format_var.set("video")
                self.log_message("🔄 הגדרות אופסו בהצלחה")
                messagebox.showinfo("הצלחה", "ההגדרות אופסו בהצלחה")
            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה באיפוס הגדרות: {str(e)}")
    
    def get_video_info(self):
        """קבלת מידע על הסרטון"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("שגיאה", "אנא הכנס קישור")
            return
        
        def fetch_info():
            try:
                self.progress_var.set("🔍 מקבל מידע על הסרטון...")
                self.progress_bar.start()
                
                response = requests.post(f"{self.server_url}/api/info", 
                                       json={"url": url}, timeout=30)
                
                if response.status_code == 200:
                    info = response.json()
                    self.log_message("=" * 50)
                    self.log_message(f"🎬 כותרת: {info['title']}")
                    self.log_message(f"👤 יוצר: {info['uploader']}")
                    
                    if info.get('duration'):
                        minutes = info['duration'] // 60
                        seconds = info['duration'] % 60
                        self.log_message(f"⏱️ אורך: {minutes}:{seconds:02d}")
                    
                    if info.get('view_count'):
                        self.log_message(f"👁️ צפיות: {info['view_count']:,}")
                    
                    # הצגת פורמטים זמינים
                    if info.get('formats'):
                        self.log_message("🎥 פורמטים זמינים:")
                        for fmt in info['formats'][:5]:  # מציג רק 5 ראשונים
                            quality = fmt.get('quality', 'לא ידוע')
                            ext = fmt.get('ext', 'לא ידוע')
                            size = fmt.get('filesize')
                            size_str = f" ({size//1024//1024:.1f}MB)" if size else ""
                            self.log_message(f"   • {quality} - {ext}{size_str}")
                    
                    self.log_message("=" * 50)
                    
                else:
                    error = response.json().get('error', 'שגיאה לא ידועה')
                    self.log_message(f"❌ שגיאה בקבלת מידע: {error}")
                    messagebox.showerror("שגיאה", error)
                    
            except requests.exceptions.Timeout:
                self.log_message("⏰ זמן קבלת המידע פג")
                messagebox.showerror("שגיאה", "זמן קבלת המידע פג")
            except Exception as e:
                self.log_message(f"❌ שגיאה בקבלת מידע: {str(e)}")
                messagebox.showerror("שגיאה", f"שגיאה בקבלת מידע: {str(e)}")
            finally:
                self.progress_bar.stop()
                self.progress_var.set("✅ מוכן להורדה")
        
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def start_download(self):
        """התחלת הורדה"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("שגיאה", "אנא הכנס קישור")
            return
        
        download_dir = self.download_dir_var.get()
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
                self.log_message(f"📁 תיקיה נוצרה: {download_dir}")
            except Exception as e:
                messagebox.showerror("שגיאה", f"לא ניתן ליצור תיקיה: {str(e)}")
                return
        
        def download():
            try:
                self.progress_var.set("⬇️ מתחיל הורדה...")
                self.progress_bar.start()
                self.download_button.config(state='disabled')
                
                # הכנת נתוני הבקשה
                format_selection = self.format_var.get()
                quality = self.quality_var.get()
                
                data = {
                    "url": url,
                    "quality": quality,
                    "audio_only": format_selection.startswith('audio')
                }
                
                self.log_message(f"📤 שולח בקשת הורדה לשרת...")
                self.log_message(f"🎯 איכות: {quality}")
                self.log_message(f"📝 פורמט: {format_selection}")
                
                # שליחת בקשת הורדה
                response = requests.post(f"{self.server_url}/api/download", 
                                       json=data, timeout=300)
                
                if response.status_code == 200:
                    result = response.json()
                    download_id = result['download_id']
                    filename = result['filename']
                    title = result.get('title', 'לא ידוע')
                    
                    self.log_message(f"✅ השרת סיים להוריד: {title}")
                    self.progress_var.set("📥 מוריד קובץ למחשב...")
                    
                    # הורדת הקובץ מהשרת
                    file_response = requests.get(f"{self.server_url}/api/file/{download_id}", 
                                               stream=True, timeout=300)
                    
                    if file_response.status_code == 200:
                        local_path = os.path.join(download_dir, filename)
                        
                        # כתיבת הקובץ
                        total_size = int(file_response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        with open(local_path, 'wb') as f:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    if total_size > 0:
                                        percent = (downloaded / total_size) * 100
                                        self.progress_var.set(f"📥 מוריד: {percent:.1f}%")
                        
                        self.log_message(f"💾 קובץ נשמר: {filename}")
                        self.log_message(f"📍 מיקום: {local_path}")
                        self.progress_var.set("🎉 הורדה הושלמה בהצלחה!")
                        
                        # הצגת הודעת הצלחה
                        result_msg = f"הקובץ נשמר בהצלחה!\n\nשם: {filename}\nמיקום: {local_path}"
                        if messagebox.askyesno("הורדה הושלמה", 
                                             result_msg + "\n\nלפתוח את התיקיה?"):
                            self.open_downloads_folder()
                    else:
                        self.log_message("❌ שגיאה בהורדת הקובץ מהשרת")
                        messagebox.showerror("שגיאה", "שגיאה בהורדת הקובץ מהשרת")
                        
                else:
                    error = response.json().get('error', 'שגיאה לא ידועה')
                    self.log_message(f"❌ שגיאת שרת: {error}")
                    messagebox.showerror("שגיאת שרת", error)
                    
            except requests.exceptions.Timeout:
                self.log_message("⏰ זמן ההורדה פג - הסרטון ארוך מדי או החיבור איטי")
                messagebox.showerror("שגיאה", "זמן ההורדה פג")
            except requests.exceptions.ConnectionError:
                self.log_message("🔌 בעיית חיבור לשרת")
                messagebox.showerror("שגיאה", "בעיית חיבור לשרת")
            except Exception as e:
                self.log_message(f"❌ שגיאה כללית: {str(e)}")
                messagebox.showerror("שגיאה", f"שגיאה בהורדה: {str(e)}")
            finally:
                self.progress_bar.stop()
                self.download_button.config(state='normal')
                if "הושלמה" not in self.progress_var.get():
                    self.progress_var.set("✅ מוכן להורדה")
        
        threading.Thread(target=download, daemon=True).start()
    
    def run(self):
        """הפעלת האפליקציה"""
        # בדיקת חיבור ראשונית
        self.test_server_connection()
        
        # הצגת הודעת פתיחה
        if "YOUR_SERVER_IP" in self.server_url:
            messagebox.showwarning("הגדרות נדרשות", 
                                 "אנא עדכן את כתובת השרת בלשונית 'הגדרות'")
        
        self.root.mainloop()

def main():
    """פונקציה ראשית"""
    try:
        app = YouTubeDownloader()
        app.run()
    except Exception as e:
        messagebox.showerror("שגיאה קריטית", f"שגיאה בהפעלת התוכנה: {str(e)}")

if __name__ == "__main__":
    main()