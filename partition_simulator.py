import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
import time


class MemoryManager(tk.Toplevel):  # 改为继承Toplevel
    def __init__(self, master=None):  # 修改构造函数
        super().__init__(master)
        self.title("动态分区存储管理模拟")
        self.geometry("800x600")
        self.max_pid = 0  # 最大PID计数器
        # 添加返回按钮（绑定主窗口恢复）
        self.return_button = tk.Button(
            self,
            text="返回主菜单",
            command=lambda: [self.destroy(), self.master.deiconify()]
        )
        self.return_button.pack(side=tk.BOTTOM, pady=10)

        self.canvas = tk.Canvas(self, width=800, height=400, bg="white")
        self.canvas.pack()

        self.memory = []  # 可用分区表
        self.allocated = []  # 已分配分区表

        # 初始化内存分区
        self.init_memory()

        # 算法选择
        self.algorithm_var = tk.StringVar(value="最先适应")  # 默认算法
        self.algorithm_label = tk.Label(self, text="选择分配算法:")
        self.algorithm_label.pack(side=tk.LEFT)
        self.algorithm_menu = ttk.Combobox(self, textvariable=self.algorithm_var,
                                           values=["最先适应", "最佳适应", "最坏适应"])
        self.algorithm_menu.pack(side=tk.LEFT)

        # 请求内存按钮
        self.request_button = tk.Button(self, text="请求内存", command=self.request_memory)
        self.request_button.pack(side=tk.LEFT)

        # 释放内存按钮
        self.release_button = tk.Button(self, text="释放内存", command=self.release_memory)
        self.release_button.pack(side=tk.LEFT)

        # 清空所有进程按钮
        self.clear_button = tk.Button(self, text="清空所有进程", command=self.clear_all_processes)
        self.clear_button.pack(side=tk.LEFT)

        # 绘制初始内存状态
        self.draw_memory()

    def init_memory(self):
        # 初始化内存分区
        self.memory = [(0, 800)]  # 起始地址和大小
        self.allocated = []  # 清空已分配分区表

    def draw_memory(self):
        self.canvas.delete("all")
        # 绘制空闲分区（绿色）
        for start, size in self.memory:
            self.canvas.create_rectangle(start, 100, start + size, 150,
                                         fill="green")  # 左上角是（start，100），右下角是（start+size，150）
            self.canvas.create_text(start + size / 2, 85, text=f"空闲:{size}KB")
        # 绘制已分配分区（蓝色）
        for start, size, pid in self.allocated:
            self.canvas.create_rectangle(start, 230, start + size, 280, fill="blue")  # 调整垂直位置
            self.canvas.create_text(start + size / 2, 215, text=f"P{pid}:{size}KB")  # 调整文本位置
        # 显示当前选择的算法
        self.canvas.create_text(400, 380, text=f"当前算法: {self.algorithm_var.get()}", font=("Arial", 12))

    def request_memory(self):
        size = simpledialog.askstring("请求内存", "请输入内存大小:", parent=self)  # 添加parent参数
        if size is None:  # 用户点击取消
            return
        try:
            size = int(size)
            if size <= 0:
                messagebox.showerror("错误", "内存大小必须大于0", parent=self)
                return

            # 创建表示申请内存大小的方块，从界面水平中心生成
            center_x = 400 - size / 2  # 水平中心位置
            block = self.canvas.create_rectangle(center_x, 0, center_x + size, 50, fill="red")
            self.animate_block(block, size)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数", parent=self)

    def animate_block(self, block, size):
        # 方块下落动画（优化动画逻辑）
        def _animate(y=0):
            if y < 400:
                self.canvas.move(block, 0, 2)
                if self.check_allocation(block, size):
                    return
                self.after(10, _animate, y + 2)
            else:
                self.canvas.delete(block)
                messagebox.showinfo("提示", "没有足够的内存", parent=self)

        _animate()

    def check_allocation(self, block, size):
        # 检查当前方块是否与空闲区匹配
        x1, y1, x2, y2 = self.canvas.coords(block)
        algorithm = self.algorithm_var.get()

        if algorithm == "最先适应":
            return self.first_fit(block, size)
        elif algorithm == "最佳适应":
            return self.best_fit(block, size)
        elif algorithm == "最坏适应":
            return self.worst_fit(block, size)
        else:
            return False

    def first_fit(self, block, size):
        # 最先适应算法
        for i, (start, s) in enumerate(self.memory):
            if s >= size:
                self.max_pid += 1  # 递增最大PID
                # 分配内存
                self.allocated.append((start, size,self.max_pid))
                if s > size:
                    self.memory[i] = (start + size, s - size)
                else:
                    del self.memory[i]
                self.draw_memory()
                self.canvas.delete(block)
                return True
        return False

    def best_fit(self, block, size):
        # 最佳适应算法
        best_index = -1
        best_size = float('inf')
        for i, (start, s) in enumerate(self.memory):
            if s >= size and s < best_size:
                best_index = i
                best_size = s
        if best_index != -1:
            self.max_pid += 1  # 递增最大PID
            # 分配内存
            self.allocated.append((self.memory[best_index][0], size, self.max_pid))
            if self.memory[best_index][1] > size:
                self.memory[best_index] = (self.memory[best_index][0] + size, self.memory[best_index][1] - size)
            else:
                del self.memory[best_index]
            self.draw_memory()
            self.canvas.delete(block)
            return True
        return False

    def worst_fit(self, block, size):
        # 最坏适应算法
        worst_index = -1
        worst_size = -1
        for i, (start, s) in enumerate(self.memory):
            if s >= size and s > worst_size:
                worst_index = i
                worst_size = s
        if worst_index != -1:
            self.max_pid += 1  # 递增最大PID
            # 分配内存
            self.allocated.append((self.memory[worst_index][0], size, self.max_pid))
            if self.memory[worst_index][1] > size:
                self.memory[worst_index] = (self.memory[worst_index][0] + size, self.memory[worst_index][1] - size)
            else:
                del self.memory[worst_index]
            self.draw_memory()
            self.canvas.delete(block)
            return True
        return False

    def release_memory(self):
        pid = simpledialog.askstring("释放内存", "请输入进程ID:", parent=self)
        if pid is None:  # 用户点击取消
            return
        try:
            pid = int(pid)
            for i, (start, size, p) in enumerate(self.allocated):
                if p == pid:
                    # 释放内存
                    self.memory.append((start, size))
                    self.memory.sort()
                    self.merge_memory()
                    del self.allocated[i]
                    self.draw_memory()
                    return

            messagebox.showerror("错误", "未找到该进程", parent=self)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数", parent=self)

    def clear_all_processes(self):
        # 清空所有进程
        if not self.allocated:
            messagebox.showinfo("提示", "当前没有已分配的进程", parent=self)
            return

        # 将所有已分配分区释放
        for start, size, pid in self.allocated:
            self.memory.append((start, size))
        self.allocated = []  # 清空已分配分区表
        self.max_pid = 0

        # 合并所有空闲分区
        self.memory.sort()
        self.merge_memory()

        # 更新界面
        self.draw_memory()
        messagebox.showinfo("提示", "已清空所有进程", parent=self)

    def merge_memory(self):
        # 合并相邻的空闲分区
        i = 0
        while i < len(self.memory) - 1:
            if self.memory[i][0] + self.memory[i][1] == self.memory[i + 1][0]:
                self.memory[i] = (self.memory[i][0], self.memory[i][1] + self.memory[i + 1][1])
                del self.memory[i + 1]
            else:
                i += 1

