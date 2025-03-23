import random
import tkinter as tk
from tkinter import ttk
from collections import deque

from torch.fx.experimental.migrate_gradual_types import operation


# 页表项类
class PageTableEntry:
    def __init__(self, page_number, disk_location):
        self.page_number = page_number#页号
        self.present = False       # 标志
        self.frame_number = -1     # 内存块号
        self.modified = False      # 修改标志
        self.disk_location = disk_location  # 磁盘位置

# 分页管理类
class PagingManager:
    def __init__(self, total_memory=64 * 1024, block_size=1024, job_blocks=4):
        self.block_size = block_size
        self.num_frames = total_memory // block_size  # 64KB / 1KB = 64块
        self.job_blocks = job_blocks  # 作业分配的内存块数（局部置换范围）

        # 初始化页表和内存
        self.page_table = {}       # {页号: PageTableEntry}
        self.free_frames = deque(range(self.num_frames))  # 全局空闲帧队列
        self.allocated_frames = {} # {作业ID: [分配的帧]}
        self.job_fifo = {}         # {作业ID: deque(分配的帧顺序)}

    def allocate_job(self, job_id, pages):
        """为作业分配初始内存块"""
        if job_id not in self.allocated_frames:
            frames = []
            for _ in range(self.job_blocks):
                if self.free_frames:
                    frame = self.free_frames.popleft()
                    frames.append(frame)
            self.allocated_frames[job_id] = frames
            self.job_fifo[job_id] = deque(frames)
        # 初始化页表
        for page in pages:
            self.page_table[page] = PageTableEntry(page, disk_location=page * 1000)  # 示例磁盘位置

    def access_page(self, job_id, page_number, operation):
        """访问页面，返回物理地址和缺页信息"""
        entry = self.page_table.get(page_number)
        if not entry:
            raise ValueError(f"Page {page_number} does not exist")

        if entry.present:
            # 页面已在内存，更新修改标志
            if operation in ["save", "存(save)"]:
                entry.modified = True
            physical = (entry.frame_number << 10) | (random.randint(0, self.block_size-1))  # 模拟块内地址
            return physical, False, None
        else:
            # 缺页中断处理
            victim = self.handle_page_fault(job_id, page_number)
            physical = (entry.frame_number << 10) | (random.randint(0, self.block_size-1))
            return physical, True, victim

    def handle_page_fault(self, job_id, page_number):
        """局部置换的FIFO算法"""
        entry = self.page_table[page_number]
        frames = self.allocated_frames.get(job_id, [])
        fifo_queue = self.job_fifo.get(job_id, deque())

        # 检查是否有空闲块
        for frame in frames:
            if self.is_frame_free(frame):
                entry.frame_number = frame
                entry.present = True
                fifo_queue.append(frame)
                return None

        # 无空闲块，置换最早进入的页面
        if fifo_queue:
            victim_frame = fifo_queue.popleft()
            # 找到被置换的页
            victim_page = None
            for p, e in self.page_table.items():
                if e.frame_number == victim_frame and e.present:
                    victim_page = p
                    break
            if victim_page:
                # 标记被置换页
                self.page_table[victim_page].present = False
                self.page_table[victim_page].frame_number = -1
                if self.page_table[victim_page].modified:
                    print(f"Page {victim_page} is written back to disk")

        # 分配新帧
        entry.frame_number = victim_frame
        entry.present = True
        fifo_queue.append(victim_frame)
        return victim_page

    def is_frame_free(self, frame):
        """检查帧是否未被任何页占用"""
        for entry in self.page_table.values():
            if entry.frame_number == frame and entry.present:
                return False
        return True

# 可视化界面
class PagingVisualizer:
    def __init__(self, root):
        self.root = root
        self.manager = PagingManager()
        self.current_step = 0
        self.instructions = [
            (0, "+", 0, 72), (1, "/", 1, 50), (2, "×", 2, 15),
            (3, "存(save)", 3, 26), (4, "取(load)", 0, 56), (5, "-", 6, 40),
            (6, "+", 4, 56), (7, "-", 5, 23), (8, "存(save)", 1, 37),
            (9, "+", 2, 78), (10, "-", 4, 1), (11, "存(save)", 6, 86)
        ]
        self.setup_gui()

    def setup_gui(self):
        self.root.title("请求式分页管理模拟器")
        self.root.geometry("800x600")  # 设置窗口大小

        # 控制按钮
        self.frame = ttk.Frame(self.root)
        self.frame.pack(pady=10)
        self.btn_next = ttk.Button(self.frame, text="下一步", command=self.next_step)
        self.btn_next.pack(side=tk.LEFT, padx=5)
        self.btn_reset = ttk.Button(self.frame, text="重置", command=self.reset)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # 页表显示
        self.canvas = tk.Canvas(self.root, width=750, height=200, bg="white")
        self.canvas.pack(pady=10)

        # 日志输出
        self.log = tk.Text(self.root, height=20, width=90)  # 增加日志窗口高度
        self.log.pack(pady=10)

        # 初始化作业
        self.manager.allocate_job("job1", [0, 1, 2, 3, 4, 5, 6])

    def next_step(self):
        """执行下一步指令"""
        if self.current_step >= len(self.instructions):
            self.log.insert(tk.END, "所有指令已执行完毕！\n")
            return

        step, op, page, offset = self.instructions[self.current_step]
        physical, page_fault, victim = self.manager.access_page("job1", page, op)
        log_msg = (
            f"指令 {step+1}: 操作={op}, 页号={page}, 页内地址={offset}\n"
            f"物理地址={physical}, 缺页={page_fault}"
        )
        if page_fault:
            log_msg += f", 置换页面={victim}\n"
        else:
            log_msg += "\n"
        self.log.insert(tk.END, log_msg)
        self.current_step += 1
        self.draw_page_table()

    def reset(self):
        """重置模拟器"""
        self.manager = PagingManager()
        self.manager.allocate_job("job1", [0, 1, 2, 3, 4, 5, 6])
        self.current_step = 0
        self.log.delete(1.0, tk.END)
        self.draw_page_table()

    def draw_page_table(self):
        """绘制页表和内存状态"""
        self.canvas.delete("all")
        x, y = 20, 20
        # 绘制页表
        self.canvas.create_text(x, y, text="页号 | 存在 | 内存块 | 修改 | 磁盘位置", anchor="w")
        y += 30
        for page in sorted(self.manager.page_table.keys()):
            entry = self.manager.page_table[page]
            text = (
                f"{page:2d} | {entry.present} | {entry.frame_number:3d} | "
                f"{entry.modified} | {entry.disk_location:5d}"
            )
            color = "green" if entry.present else "red"
            self.canvas.create_text(x, y, text=text, anchor="w", fill=color)
            y += 20
        # 绘制内存块
        y = 20
        x = 400
        self.canvas.create_text(x, y, text="内存块状态（作业分配块: 0-3）", anchor="w")
        y += 30
        for frame in self.manager.allocated_frames["job1"]:
            used = any(e.frame_number == frame for e in self.manager.page_table.values() if e.present)
            color = "red" if used else "green"
            self.canvas.create_rectangle(x, y, x + 100, y + 20, fill=color)
            self.canvas.create_text(x + 50, y + 10, text=f"帧 {frame}")
            y += 30

# 运行程序
if __name__ == "__main__":
    root = tk.Tk()
    app = PagingVisualizer(root)
    root.mainloop()