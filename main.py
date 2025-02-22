import random
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import queue
import os

# 定义全局变量
time_list = []
compliments = []
message_queue = queue.Queue()

# 打印当前工作目录
print("当前工作目录:", os.getcwd())

# 初始化 GUI 窗口
root = tk.Tk()
root.title("自动夸人小助手")
root.geometry("300x200")  # 设置窗口大小

# 设置时间的输入值
time_label = tk.Label(root, text="夸人时间 (HH:MM):")
time_label.pack()

time_entry = tk.Entry(root)
time_entry.pack(pady=10)

# 添加倒计时标签
countdown_label = tk.Label(root, text="", font=("Arial", 12))
countdown_label.pack(pady=10)

# 定义颜色和字体
BUTTON_COLOR = "#4CAF50"
LABEL_FONT = ("Arial", 12)

def is_valid(time_str):
    """验证时间格式是否为 HH:MM"""
    try:
        hours, minutes = map(int, time_str.split(":"))
        if 0 <= hours < 24 and 0 <= minutes < 60:
            return True
        else:
            return False
    except ValueError:
        return False

def load_compliments():
    """从文件加载夸人话术"""
    file_path = os.path.join(os.path.dirname(__file__), "resources", "compliments.txt")
    print(f"文件路径: {file_path}")  # 打印文件路径
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            compliments = f.readlines()
            print(f"读取到的夸人话术: {compliments}")  # 调试信息
            return [c.strip() for c in compliments if c.strip()]
    except FileNotFoundError:
        messagebox.showerror("错误", "夸人话术文件 compliments.txt 未找到！")
        return []

def compliment_at_time(target_time_str):
    try:
        target_time = datetime.strptime(target_time_str, "%H:%M").time()
    except ValueError:
        messagebox.showerror("错误", "请输入正确的格式！例如 12:30")
        return

    # 获取当前时间
    now = datetime.now()
    target_datetime = datetime.combine(now.date(), target_time)

    # 如果目标时间已经过去，设置为第二天的同一时间
    if target_datetime < now:
        target_datetime += timedelta(days=1)

    # 计算时间差
    delta = (target_datetime - now).total_seconds()

    # 如果时间差小于0，说明时间已经过去
    if delta < 0:
        messagebox.showwarning("警告", "夸人时间已过，明天同一时间再夸！")
        return

    print(f"等待 {delta} 秒后触发夸人功能...")  # 调试信息

    # 延迟到目标时间
    time.sleep(delta)

    # 读取夸人话术
    compliments = load_compliments()
    if not compliments:
        messagebox.showerror("错误", "话术内容为空，请检查！")
        return

    # 随机选择一条夸人话术
    chosen_compliment = random.choice(compliments)

    # 将消息放入队列
    message_queue.put(chosen_compliment)

def start_compliment():
    global time_list  # 声明 time_list 为全局变量
    input_times = time_entry.get().strip()
    if not input_times:
        messagebox.showerror("错误", "输入时间！")
        return

    # 分割时间点
    time_list = [t.strip() for t in input_times.split(',')]

    for time_str in time_list:
        if not is_valid(time_str):
            messagebox.showerror("错误", f"输入时间格式不正确: {time_str}，请输入 HH:MM 格式！")
            return

        # 启动线程执行夸人任务
        threading.Thread(target=compliment_at_time, args=(time_str,), daemon=True).start()

    messagebox.showinfo("提示", f"夸人时间已经设置为 {','.join(time_list)}！")

# 检查文件是否存在
file_path = os.path.join(os.path.dirname(__file__), "resources", "compliments.txt")
if not os.path.exists(file_path):
    messagebox.showerror("错误", "夸人话术文件 compliments.txt 未找到！")
else:
    compliments = load_compliments()  # 初始加载

# 启动按钮
start_button = tk.Button(
    root,
    text="开始夸人",
    command=start_compliment,
    font=LABEL_FONT,
    bg=BUTTON_COLOR,
    fg="white",
    padx=10,
    pady=5
)
start_button.pack(pady=10)

# 倒计时函数
def update_countdown():
    global time_list  # 声明 time_list 为全局变量
    now = datetime.now()
    next_time = None
    min_delta = float('inf')

    # 找到最近的夸人时间
    for time_str in time_list:
        target_time = datetime.strptime(time_str, "%H:%M").time()
        target_datetime = datetime.combine(now.date(), target_time)
        if target_datetime < now:
            target_datetime += timedelta(days=1)
        delta = (target_datetime - now).total_seconds()
        if delta < min_delta:
            min_delta = delta
            next_time = target_datetime

    if next_time:
        countdown_label.config(text=f"距离下一个夸人时间还有：{min_delta // 60} 分钟 {min_delta % 60} 秒")
    else:
        countdown_label.config(text="没有设置夸人时间")

    # 每秒更新一次
    root.after(1000, update_countdown)

# 启动倒计时更新
update_countdown()

# 文件监听器
class ComplimentFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("compliments.txt"):
            global compliments
            compliments = load_compliments()
            print("文件已修改，夸人话术已更新")  # 调试信息
            message_queue.put("夸人话术已经更新")

observer = Observer()
observer.schedule(ComplimentFileHandler(), path='resources', recursive=False)
observer.start()

# 在主循环中保持监听
def process_queue():
    while not message_queue.empty():
        message = message_queue.get()
        messagebox.showinfo("提示", message)
    root.after(100, process_queue)

# 启动队列处理
process_queue()

try:
    root.mainloop()
except KeyboardInterrupt:
    observer.stop()
observer.join()