import tkinter as tk
from tkinter import ttk
from collections import deque
import random

# 页表项类
class PageTableEntry:
    def __init__(self, page_number, disk_location):
        self.page_number = page_number
        self.present = False       # 存在标志
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
            self.page_table[page] = PageTableEntry(page, disk_location=page * 1000)

    def access_page(self, job_id, page_number, operation):
        """访问页面，返回物理地址和缺页信息"""
        entry = self.page_table.get(page_number)
        if not entry:
            raise ValueError(f"Page {page_number} does not exist")

        if entry.present:
            # 页面已在内存，更新修改标志
            if operation in ["save", "存(save)"]:
                entry.modified = True
            physical = (entry.frame_number << 10) | (random.randint(0, self.block_size - 1))
            return physical, False, (None, None)
        else:
            # 缺页中断处理
            victim_page, victim_frame = self.handle_page_fault(job_id, page_number)
            physical = (entry.frame_number << 10) | (random.randint(0, self.block_size - 1))
            return physical, True, (victim_page, victim_frame)

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
                return (None, None)

        # 无空闲块，置换最早进入的页面
        if fifo_queue:
            victim_frame = fifo_queue.popleft()
            victim_page = None
            for p, e in self.page_table.items():
                if e.frame_number == victim_frame and e.present:
                    victim_page = p
                    break
            if victim_page:
                self.page_table[victim_page].present = False
                self.page_table[victim_page].frame_number = -1
                if self.page_table[victim_page].modified:
                    print(f"Page {victim_page} is written back to disk")

        # 分配新帧
        entry.frame_number = victim_frame
        entry.present = True
        fifo_queue.append(victim_frame)
        return (victim_page, victim_frame)

    def is_frame_free(self, frame):
        """检查帧是否未被任何页占用"""
        for entry in self.page_table.values():
            if entry.frame_number == frame and entry.present:
                return False
        return True

# 可视化界面（最终修复版）
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
        self.memory_blocks = {}  # 显式初始化内存块字典
        self.setup_gui()
        self.animation_queue = []
        self.is_animating = False

    def setup_gui(self):
        self.root.title("请求式分页管理模拟器（最终版）")
        self.root.geometry("900x600")

        # 主容器（使用grid布局）
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部区域容器（6:4比例）
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky="nsew", pady=5)

        # 配置列比例
        top_frame.columnconfigure(0, weight=6)  # 左侧60%
        top_frame.columnconfigure(1, weight=4)  # 右侧40%
        top_frame.rowconfigure(0, weight=1)

        # 左侧页表区域（60%宽度）
        left_pane = ttk.Frame(top_frame)
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 右侧内存块区域（40%宽度）
        right_pane = ttk.Frame(top_frame)
        right_pane.grid(row=0, column=1, sticky="nsew")

        # 页表表格配置
        self.tree_page = ttk.Treeview(
            left_pane,
            columns=("page", "present", "frame", "modified", "disk"),
            show="headings",
            height=8
        )
        columns = [
            ("页号", 80), ("存在标志", 100),
            ("内存块号", 100), ("修改标志", 100), ("磁盘位置", 120)
        ]
        for idx, (text, width) in enumerate(columns):
            self.tree_page.heading(f"#{idx + 1}", text=text)
            self.tree_page.column(f"#{idx + 1}", width=width, anchor="center")
        self.tree_page.pack(fill=tk.BOTH, expand=True)

        # 内存块状态面板
        mem_frame = ttk.Frame(right_pane)
        mem_frame.pack(fill=tk.BOTH, expand=True)

        # 内存块展示画布
        self.memory_canvas = tk.Canvas(mem_frame, bg="white", bd=1, relief=tk.SUNKEN)
        self.memory_canvas.pack(fill=tk.BOTH, expand=True)

        # 中间指令记录区域
        mid_frame = ttk.Frame(main_frame)
        mid_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        # -------------------------- 中间区域：指令执行记录 --------------------------
        self.frame_mid = ttk.Frame(self.root)
        self.frame_mid.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        # 指令执行记录表格
        self.tree_log = ttk.Treeview(
            self.frame_mid,
            columns=("step", "op", "page", "offset", "physical", "fault", "victim"),
            show="headings",
            height=8
        )
        columns = {
            "step": ("序号", 60),
            "op": ("操作", 80),
            "page": ("页号", 60),
            "offset": ("页内地址", 80),
            "physical": ("物理地址", 100),
            "fault": ("缺页", 60),
            "victim": ("置换页面", 100)
        }
        for col, (text, width) in columns.items():
            self.tree_log.heading(col, text=text)
            self.tree_log.column(col, width=width, anchor="center")
        self.tree_log.pack(fill=tk.BOTH, expand=True)

        # -------------------------- 底部区域：操作按钮 --------------------------
        # 底部控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky="ew", pady=5)

        self.btn_start = ttk.Button(control_frame, text="开始执行", command=self.start_animation)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_reset = ttk.Button(control_frame, text="重置", command=self.reset)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # 配置主布局权重
        main_frame.rowconfigure(0, weight=4)  # 顶部区域占40%高度
        main_frame.rowconfigure(1, weight=5)  # 中间区域占50%高度
        main_frame.rowconfigure(2, weight=1)  # 底部按钮占10%高度

        # 初始化数据
        self.manager.allocate_job("job1", [0, 1, 2, 3, 4, 5, 6])
        self.update_table()
        self.draw_memory_blocks()

    def update_table(self):
        """更新页表表格数据"""
        self.tree_page.delete(*self.tree_page.get_children())
        for page in sorted(self.manager.page_table.keys()):
            entry = self.manager.page_table[page]
            values = (
                page,
                "✓" if entry.present else "✗",
                entry.frame_number if entry.frame_number != -1 else "-",
                "✓" if entry.modified else "✗",
                f"0x{entry.disk_location:04X}"
            )
            self.tree_page.insert("", "end", values=values,
                                tags=("present" if entry.present else "absent"))
        self.tree_page.tag_configure("present", foreground="green")
        self.tree_page.tag_configure("absent", foreground="red")


    def draw_memory_blocks(self):
        """绘制专业的内存块状态图"""
        self.memory_canvas.delete("all")
        canvas_width = self.memory_canvas.winfo_width()
        canvas_height = self.memory_canvas.winfo_height()

        # 动态计算布局参数
        cols = 2  # 每行显示2个块
        rows = 2  # 共显示4个块
        block_size = min((canvas_width - 40) // cols, (canvas_height - 40) // rows)
        spacing = 10

        start_x = (canvas_width - (cols * block_size + (cols - 1) * spacing)) // 2
        start_y = (canvas_height - (rows * block_size + (rows - 1) * spacing)) // 2

        for idx, frame in enumerate(self.manager.allocated_frames.get("job1", [])):
            row = idx // cols
            col = idx % cols

            x = start_x + col * (block_size + spacing)
            y = start_y + row * (block_size + spacing)

            used = any(e.frame_number == frame and e.present
                       for e in self.manager.page_table.values())

            # 绘制紧凑型内存块
            self.memory_canvas.create_rectangle(
                x, y, x + block_size, y + block_size,
                fill="#FF4444" if used else "#44FF44",
                outline="black",
                width=2,
                tags=f"frame_{frame}"
            )
            self.memory_canvas.create_text(
                x + block_size / 2, y + block_size / 2,
                text=f"帧{frame}\n{'使用中' if used else '空闲'}",
                font=('宋体', 9),
                fill="white" if used else "black"
            )
    def animate_memory_blocks(self, old_frame, new_frame):
        """专业动画效果：渐变+缩放"""

        def animate_step(step):
            if step <= 10:
                # 旧块渐隐
                if old_frame in self.memory_blocks:
                    current_color = self.memory_canvas.itemcget(
                        self.memory_blocks[old_frame], "fill")
                    new_color = self.interpolate_color(current_color, "#888888", step / 10)
                    self.memory_canvas.itemconfig(
                        self.memory_blocks[old_frame],
                        fill=new_color,
                        width=2 * (1 - step / 10)
                    )

                # 新块渐显
                if new_frame in self.memory_blocks:
                    current_color = self.memory_canvas.itemcget(
                        self.memory_blocks[new_frame], "fill")
                    new_color = self.interpolate_color("#44FF44", current_color, step / 10)
                    self.memory_canvas.itemconfig(
                        self.memory_blocks[new_frame],
                        fill=new_color,
                        width=2 * (1 + step / 10)
                    )

                self.root.after(50, lambda: animate_step(step + 1))
            else:
                # 恢复最终状态
                self.draw_memory_blocks()
                self.root.after(500, self.process_next_instruction)

        animate_step(1)

    def interpolate_color(self, start_color, end_color, ratio):
        """颜色渐变算法"""
        start = self.memory_canvas.winfo_rgb(start_color)
        end = self.memory_canvas.winfo_rgb(end_color)
        r = int(start[0] + (end[0] - start[0]) * ratio)
        g = int(start[1] + (end[1] - start[1]) * ratio)
        b = int(start[2] + (end[2] - start[2]) * ratio)
        return f"#{r // 256:02x}{g // 256:02x}{b // 256:02x}"

    def start_animation(self):
        """开始自动执行指令"""
        if not self.is_animating:
            self.animation_queue = self.instructions.copy()
            self.process_next_instruction()

    def process_next_instruction(self):
        if not self.animation_queue:
            self.is_animating = False
            return

        self.is_animating = True
        step, op, page, offset = self.animation_queue.pop(0)
        try:
            physical, page_fault, (victim_page, victim_frame) = self.manager.access_page("job1", page, op)
        except Exception as e:
            self.log_error(f"执行指令错误: {e}")
            return

        # 更新指令执行记录
        item_id = self.tree_log.insert(
            "", "end",
            values=(
                step + 1,
                op,
                page,
                offset,
                physical,
                "是" if page_fault else "否",
                f"{victim_page} (帧 {victim_frame})" if victim_page else "-"
            )
        )
        self.tree_log.see(item_id)

        # 更新界面
        self.update_table()
        self.draw_memory_blocks()

        # 触发动画
        if page_fault and victim_frame is not None:
            self.animate_memory_blocks(victim_frame, self.manager.page_table[page].frame_number)
        else:
            self.root.after(1000, self.process_next_instruction)

    def animate_memory_blocks(self, old_frame, new_frame):
        """内存块闪烁动画"""
        def flash(obj, color1, color2, count):
            if count > 0:
                current_color = color1 if count % 2 == 0 else color2
                self.canvas_memory.itemconfig(obj, fill=current_color)
                self.root.after(300, lambda: flash(obj, color1, color2, count-1))
            else:
                self.canvas_memory.itemconfig(obj, fill="red" if "red" in [color1, color2] else "green")

        if old_frame in self.memory_blocks:
            flash(self.memory_blocks[old_frame][0], "red", "white", 3)
        if new_frame in self.memory_blocks:
            flash(self.memory_blocks[new_frame][0], "green", "white", 3)
        self.root.after(2000, self.process_next_instruction)

    def reset(self):
        """重置模拟器"""
        self.manager = PagingManager()
        self.manager.allocate_job("job1", [0, 1, 2, 3, 4, 5, 6])
        self.current_step = 0
        self.tree_log.delete(*self.tree_log.get_children())
        self.update_table()
        self.draw_memory_blocks()
        self.is_animating = False

    def log_error(self, message):
        """记录错误信息"""
        self.tree_log.insert("", "end", values=("错误", message, "", "", "", "", ""))


if __name__ == "__main__":
    root = tk.Tk()
    app = PagingVisualizer(root)
    root.mainloop()