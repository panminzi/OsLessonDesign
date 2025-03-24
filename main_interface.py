import tkinter as tk
from tkinter import ttk
from partition_simulator import MemoryManager
from paging_simulator import PagingVisualizer


class MainInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("操作系统课程设计主界面")
        self.root.geometry("400x300")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)

        title = ttk.Label(main_frame, text="请选择实验模块", font=("微软雅黑", 16, "bold"))
        title.pack(pady=20)

        btn_style = ttk.Style()
        btn_style.configure("Main.TButton", font=("微软雅黑", 12), padding=10)

        ttk.Button(main_frame, text="动态分区管理模拟", style="Main.TButton",
                   command=self.open_partition_simulator).pack(fill=tk.X, pady=10)
        ttk.Button(main_frame, text="动态分页管理模拟", style="Main.TButton",
                   command=self.open_paging_simulator).pack(fill=tk.X, pady=10)
        ttk.Button(main_frame, text="退出系统", style="Main.TButton",
                   command=self.root.quit).pack(fill=tk.X, pady=10)

    def open_partition_simulator(self):
        self.root.withdraw()
        partition_window = MemoryManager(self.root)  # 传递主窗口引用
        partition_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(partition_window))

    def open_paging_simulator(self):
        self.root.withdraw()
        paging_window = PagingVisualizer(self.root)  # 传递主窗口引用
        paging_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(paging_window))

    def on_child_close(self, child_window):
        child_window.destroy()
        self.root.deiconify()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainInterface(root)
    root.mainloop()