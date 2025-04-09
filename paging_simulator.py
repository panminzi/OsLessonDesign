import tkinter as tk
from tkinter import ttk
from collections import deque


class PageTableEntry:
    def __init__(self, page_number, disk_location):
        self.page_number = page_number
        self.present = False
        self.frame_number = -1
        self.modified = False
        self.disk_location = disk_location


class PagingManager:
    def __init__(self, total_memory=64 * 1024, block_size=1024, job_blocks=4):
        self.block_size = block_size
        self.num_frames = total_memory // block_size
        self.job_blocks = job_blocks

        self.page_table = {}
        initial_frames = {5, 8, 9, 1}
        self.free_frames = deque(sorted(set(range(self.num_frames)) - initial_frames))
        self.allocated_frames = {}
        self.job_fifo = {}

    def allocate_job(self, job_id, pages):
        if job_id not in self.allocated_frames:
            frames = [5, 8, 9, 1]  # 手动分配初始页
            self.allocated_frames[job_id] = frames
            self.job_fifo[job_id] = deque(frames)

        disk_loc_map = {0: 0x10, 1: 0x12, 2: 0x13, 3: 0x21,
                        4: 0x22, 5: 0x23, 6: 0x125}
        frame_map = {0: 5, 1: 8, 2: 9, 3: 1}

        for page in pages:
            disk_loc = disk_loc_map.get(page, page * 1000)
            entry = PageTableEntry(page, disk_loc)
            if page in [0, 1, 2, 3]:
                entry.present = True
                entry.frame_number = frame_map[page]
            self.page_table[page] = entry

    def access_page(self, job_id, page_number, operation, offset):
        entry = self.page_table[page_number]
        if entry.present:
            if operation in ["save", "存(save)"]:
                entry.modified = True
            physical = (entry.frame_number << 10) | offset
            return physical, False, (None, None)
        else:
            victim_page, victim_frame = self.handle_page_fault(job_id, page_number)
            entry.modified = (operation in ["save", "存(save)"])
            physical = (entry.frame_number << 10) | offset
            return physical, True, (victim_page, victim_frame)

    def handle_page_fault(self, job_id, page_number):
        """处理缺页中断的核心算法（FIFO页面置换）"""
        #获取目标页表项和作业的帧资源
        entry = self.page_table[page_number]#获取目标页表项和作业的帧资源
        frames = self.allocated_frames[job_id]#获取目标页表项和作业的帧资源
        fifo_queue = self.job_fifo[job_id]# 维护帧使用顺序的FIFO队列

        # 查找空闲帧
        for frame in frames:
            if self.is_frame_free(frame):
               # 维护帧使用顺序的FIFO队列
                entry.frame_number = frame
                entry.present = True  #维护帧使用顺序的FIFO队列
                fifo_queue.append(frame)#维护帧使用顺序的FIFO队列
                return (None, None)#维护帧使用顺序的FIFO队列

        # FIFO置换，维护帧使用顺序的FIFO队列
        victim_frame = fifo_queue.popleft()
        # 精确查找被置换页
        victim_page = None
        for p, e in self.page_table.items():  # 遍历所有页表项
            if e.frame_number == victim_frame and e.present:
                victim_page = p #维护帧使用顺序的FIFO队列
                break
        # 如果被置换页曾被修改，需要写回磁盘
        if self.page_table[victim_page].modified:
            print(f"写回磁盘: 页{victim_page}")

        # 更新被置换页的状态
        self.page_table[victim_page].present = False#更新被置换页的状态
        self.page_table[victim_page].frame_number = -1#更新被置换页的状态
        # 更新被置换页的状态
        entry.frame_number = victim_frame
        entry.present = True
        fifo_queue.append(victim_frame)
        return (victim_page, victim_frame)

    def is_frame_free(self, frame):
          # 遍历所有页表项，检查是否有页占用该帧且处于内存中
          # 遍历所有页表项，检查是否有页占用该帧且处于内存中
        return not any(e.frame_number == frame and e.present
                       for e in self.page_table.values())


class PagingVisualizer(tk.Toplevel):
    def __init__(self, master, main_window):
        super().__init__(master)
        self.main_window = main_window  # 保存主窗口的引用
        # 其他初始化代码...
        self.manager = PagingManager()
        self.instructions = [
            (0, "+", 0, 72), (1, "/", 1, 50), (2, "×", 2, 15),
            (3, "存(save)", 3, 26), (4, "取(load)", 0, 56), (5, "-", 6, 40),
            (6, "+", 4, 56), (7, "-", 5, 23), (8, "存(save)", 1, 37),
            (9, "+", 2, 78), (10, "-", 4, 1), (11, "存(save)", 6, 86)
        ]
        self.setup_gui()
        self.manager.allocate_job("job1", [0, 1, 2, 3, 4, 5, 6])
        self.update_table()

    def setup_gui(self):
        self.title("请求式分页管理模拟器")
        self.geometry("1000x700")

        # 主布局
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部区域
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 页表
        self.tree_page = ttk.Treeview(top_frame, columns=("页号", "存在", "块号", "修改标志", "磁盘位置"),
                                      show="headings", height=8)
        for col, width in [("页号", 80), ("存在", 80), ("块号", 80), ("修改标志", 80), ("磁盘位置", 120)]:
            self.tree_page.heading(col, text=col)
            self.tree_page.column(col, width=width, anchor='center')
        self.tree_page.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 内存显示
        self.mem_canvas = tk.Canvas(top_frame, bg='white', bd=2, relief=tk.GROOVE)
        self.mem_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        # 日志
        self.tree_log = ttk.Treeview(main_frame,
                                     columns=("序号", "操作", "页号", "页内地址", "物理地址", "缺页", "置换"),
                                     show="headings", height=12)
        for col, width in [("序号", 60), ("操作", 80), ("页号", 60), ("页内地址", 80),
                           ("物理地址", 100), ("缺页", 60), ("置换", 100)]:
            self.tree_log.heading(col, text=col)
            self.tree_log.column(col, width=width, anchor='center')
        self.tree_log.pack(fill=tk.BOTH, expand=True)

        # 控制按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="开始执行", command=self.start_animation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重置", command=self.reset).pack(side=tk.LEFT, padx=5)
        # 返回按钮（左）
        ttk.Button(btn_frame, text="返回主界面", command=self.return_to_main).pack(side=tk.LEFT)
    def update_table(self):
        self.tree_page.delete(*self.tree_page.get_children())
        for page in sorted(self.manager.page_table):
            entry = self.manager.page_table[page]
            self.tree_page.insert("", "end", values=(
                page,
                "✓" if entry.present else "✗",
                entry.frame_number if entry.frame_number != -1 else "-",
                "✓" if entry.modified else "✗",
                f"0x{entry.disk_location:04X}"
            ))

    def draw_memory(self):
        self.mem_canvas.delete("all")
        w, h = self.mem_canvas.winfo_width(), self.mem_canvas.winfo_height()
        cols = 2
        rows = 2
        size = min((w - 40) // cols, (h - 40) // rows)
        spacing = 10

        start_x = (w - (cols * size + (cols - 1) * spacing)) // 2
        start_y = (h - (rows * size + (rows - 1) * spacing)) // 2

        for idx, frame in enumerate(self.manager.allocated_frames["job1"]):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (size + spacing)
            y = start_y + row * (size + spacing)

            used = any(e.frame_number == frame and e.present
                       for e in self.manager.page_table.values())

            self.mem_canvas.create_rectangle(
                x, y, x + size, y + size,
                fill="#FF4444" if used else "#44FF44",
                outline="black"
            )
            self.mem_canvas.create_text(
                x + size / 2, y + size / 2,
                text=f"块{frame}\n{'使用中' if used else '空闲'}",
                font=('宋体', 10),
                fill="white" if used else "black"
            )

    def start_animation(self):
        for instruction in self.instructions:
            self.process_instruction(instruction)
            self.update()
            self.after(1000)

    def process_instruction(self, inst):
        step, op, page, offset = inst
        try:
            physical, fault, (victim, frame) = self.manager.access_page("job1", page, op, offset)
            replace_info = f"页{victim}→页{frame}" if victim is not None else "-"  # 明确处理None

            # 物理地址格式化
            physical_str = f"{physical} (0x{physical:04X})" if not fault else "-"

            valid_physical = physical if not fault else None # 新增物理地址有效性检查
            print(f":11页{victim} \n")

            # 修正地址显示格式
            self.tree_log.insert("", "end", values=(
                step + 1,
                op,
                page,
                f"{offset} (0x{offset:03X})",  # 同时显示十进制和十六进制
                physical_str,
                "是" if fault else "否",
                replace_info  # 显示置换关系
            ))
            self.update_table()
            self.draw_memory()
        except Exception as e:
            self.tree_log.insert("", "end", values=(step + 1, "错误", str(e), "", "", "", ""))

    def reset(self):
        self.manager = PagingManager()
        self.manager.allocate_job("job1", [0, 1, 2, 3, 4, 5, 6])
        self.tree_log.delete(*self.tree_log.get_children())
        self.update_table()
        self.draw_memory()

        # 设置窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.return_to_main)

    def return_to_main(self):
        self.main_window.deiconify()  # 显示主窗口
        self.destroy()  # 销毁当前窗口

if __name__ == "__main__":
    root = tk.Tk()
    app = PagingVisualizer(root)
    root.mainloop()