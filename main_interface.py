import tkinter as tk
from tkinter import ttk
from partition_simulator import MemoryManager
from paging_simulator import PagingVisualizer

class MainInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("操作系统课程设计")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.setup_styles()
        self.create_widgets()
        self.set_icon()

    def setup_styles(self):
        """统一配置界面样式"""
        self.style = ttk.Style()

        # 配置主框架样式
        self.style.configure("Main.TFrame", background="#f0f3f5")

        # 配置标题样式
        self.style.configure("Title.TLabel",
                             font=("微软雅黑", 18, "bold"),
                             foreground="#2c3e50",
                             background="#f0f3f5")

        # 修改后的按钮样式（黑色字体）
        self.style.configure("Primary.TButton",
                             font=("微软雅黑", 12),
                             padding=10,
                             foreground="black",  # 修改为黑色字体
                             background="#ecf0f1",
                             bordercolor="#bdc3c7",
                             width=20,  # 固定按钮宽度
                             anchor="center")  # 文字居中

        self.style.map("Primary.TButton",
                       background=[("active", "#d0d3d4"), ("disabled", "#bdc3c7")])

    def set_icon(self):
        """设置窗口图标（需要准备ico文件）"""
        try:
            self.root.iconbitmap("os_icon.ico")
        except:
            pass

    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(pady=20)

        ttk.Label(title_frame,
                  text="操作系统课程设计",
                  style="Title.TLabel").pack()

        # 功能按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        # 添加装饰线
        ttk.Separator(btn_frame, orient="horizontal").pack(fill=tk.X, pady=10)

        buttons = [
            ("动态分区管理模拟", self.open_partition_simulator),
            ("动态分页管理模拟", self.open_paging_simulator),
            ("退出系统", self.root.quit)
        ]

        # 统一设置按钮尺寸
        for text, command in buttons:
            btn = ttk.Button(btn_frame,
                             text=text,
                             style="Primary.TButton",
                             command=command)
            btn.pack(fill=tk.X, pady=4, ipady=5)  # ipady增加垂直内边距

        # 版本信息
        version_label = ttk.Label(main_frame,
                                  text="版本 1.0 | © 2023 操作系统课程设计",
                                  style="Title.TLabel")
        version_label.pack(side=tk.BOTTOM, pady=10)


        for text, command in buttons:
            btn = ttk.Button(btn_frame,
                             text=text,
                             style="Primary.TButton",
                             command=command)
            btn.pack(fill=tk.X, pady=8, ipady=5)

        # 版本信息
        version_label = ttk.Label(main_frame,
                                  text="版本 1.0 | © 2023 操作系统课程设计",
                                  style="Title.TLabel")
        version_label.pack(side=tk.BOTTOM, pady=10)

    def open_partition_simulator(self):
        """打开分区模拟器"""
        self.root.withdraw()
        partition_window = MemoryManager(self.root)
        partition_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(partition_window))

    def open_paging_simulator(self):
        """打开分页模拟器"""
        self.root.withdraw()
        paging_window = PagingVisualizer(self.root, self.root)

    def on_child_close(self, child_window):
        """子窗口关闭处理"""
        if child_window.winfo_exists():
            child_window.destroy()
        self.root.deiconify()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainInterface(root)
    root.mainloop()