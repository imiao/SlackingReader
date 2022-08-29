from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog
from tkinter.ttk import *
import keyboard
import mouse
import linecache
import os
import json
import ctypes
import math

# 告诉操作系统使用程序自身的dpi适配(高分屏适配)
ctypes.windll.shcore.SetProcessDpiAwareness(1)
# 获取屏幕的缩放因子
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)


class SkipDialog(simpledialog.Dialog):
    '''自定义跳转弹出框'''

    def __init__(self, title, prompt, filename,
                 initialvalue=None,
                 minvalue=None, maxvalue=None,
                 parent=None):

        self.prompt = prompt
        self.filename = filename
        self.file_chapters = filename.replace(".txt", "_chapters.json")
        self.minvalue = minvalue
        self.maxvalue = maxvalue

        self.initialvalue = initialvalue

        self.chapterListVar = StringVar()
        self.chapters = {}
        if os.path.exists(self.file_chapters):
            with open(self.file_chapters, 'r', encoding="utf-8") as f:
                self.chapters = json.load(f)
        else:
            self.makeTitleList()
        self.chapterListVar.set(" ".join(self.chapters.keys()))

        simpledialog.Dialog.__init__(self, parent, title)

    def destroy(self):
        if not os.path.exists(self.file_chapters):
            with open(self.file_chapters, 'w', encoding="utf-8") as f:
                json.dump(self.chapters, f, ensure_ascii=False)
        self.entry = None
        simpledialog.Dialog.destroy(self)

    def makeTitleList(self):
        '''生成章节列表'''
        lines = linecache.getlines(self.filename)
        for i in range(len(lines)):
            line = lines[i].strip()
            if line != "" and "第" in line and "章" in line:
                line = line.replace("\n", "").replace(" ", "").replace("=", "")
                if len(line) < 30:
                    self.chapters[line] = i + 1

    def selectTitle(self, event):
        '''选择章节'''
        cur = self.listbox.get(self.listbox.curselection())
        self.entry.delete(0, END)
        self.entry.insert(0, self.chapters[cur])

    def getNear(self, value):
        '''找到当前行数最近章节'''
        keys = list(self.chapters.keys())
        for i in range(1, len(keys)):
            if value < self.chapters[keys[i]]:
                return i - 1

    def body(self, master):
        near = self.getNear(self.initialvalue)
        frame = Frame(master)
        sbar = Scrollbar(frame)
        sbar.pack(side=RIGHT, fill=Y)
        self.listbox = Listbox(
            frame, width=40, listvariable=self.chapterListVar, yscrollcommand=sbar)
        self.listbox.pack()
        sbar.config(command=self.listbox.yview)
        self.listbox.see(near)
        self.listbox.bind('<Double-Button-1>', self.selectTitle)
        frame.grid(row=0, rowspan=2, column=0, padx=5, sticky=W)

        w = Label(master, text=self.prompt, justify=LEFT)
        w.grid(row=0, column=1, padx=5, sticky=W)

        self.entry = Entry(master, name="entry")
        self.entry.grid(row=1, column=1, padx=5, sticky=W+E)

        if self.initialvalue is not None:
            self.entry.insert(0, self.initialvalue)
            self.entry.select_range(0, END)

        return self.entry

    def buttonbox(self):

        box = Frame(self)

        w = Button(box, text="确定", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="取消", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def getresult(self):
        return self.getint(self.entry.get())

    def validate(self):
        try:
            result = self.getresult()
        except ValueError:
            messagebox.showwarning(
                "麻烦敲个数字",
                parent=self
            )
            return 0

        if self.minvalue is not None and result < self.minvalue:
            messagebox.showwarning(
                "错误",
                "最小值 %s "
                "重新试试吧" % self.minvalue,
                parent=self
            )
            return 0

        if self.maxvalue is not None and result > self.maxvalue:
            messagebox.showwarning(
                "错误",
                "最大值 %s "
                "重新试试吧" % self.maxvalue,
                parent=self
            )
            return 0

        self.result = result

        return 1


# 获取屏幕上某个坐标的颜色
def get_color(x, y):
    hdc = ctypes.windll.user32.GetDC(None)
    pixel = ctypes.windll.gdi32.GetPixel(hdc, x, y)
    r = pixel & 0x0000ff
    g = (pixel & 0x00ff00) >> 8
    b = pixel >> 16
    color = "#%02x%02x%02x" % (r, g, b)
    return color


class MRead:
    def __init__(self) -> None:
        self.tk = Tk()
        self.nowVar = StringVar()
        self.text = StringVar()
        self.hide = False
        self.listen_wheel = True
        # 加载配置文件
        self.load_config()
        # 程序初始化
        self.set_up()
        # 设置程序缩放（高分屏适配）
        self.tk.call('tk', 'scaling', ScaleFactor/75)

    def load_config(self):
        with open('./config.json', 'r', encoding="utf-8") as f:
            self.config = json.load(f)
        self.files = self.config["files"]
        self.width = self.config["width"]
        self.height = 100
        self.text_color = self.config["text_color"]
        self.font_name = self.config["font_name"]
        self.font_size = self.config["font_size"]
        self.font_px = self.font_size*4/3
        dirlist = os.listdir("./")
        txtlist = []
        # 增加新文件
        for txt_file in dirlist:
            if txt_file.endswith(".txt"):
                txtlist.append(txt_file)
                if txt_file not in self.files.keys():
                    self.files[txt_file] = 1
        if len(txtlist) == 0:
            messagebox.showerror(
                "错误", "同级目录下未找到txt文件。")
            exit(0)
        # 删除不存在的文件
        for kfile in list(self.files):
            if kfile not in txtlist:
                self.files.pop(kfile)
                
        self.now = self.config["now"]
        if len(self.now) == 0 or self.now not in txtlist:
            self.now = list(self.files.keys())[0]
            self.config["now"] = self.now

        self.nowVar.set(self.now)
        self.linenum = self.files[self.now]
        self.save_config()

    def save_config(self):
        self.files[self.now] = self.linenum
        with open('./config.json', 'w', encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def set_up(self):
        # 初始化显示在屏幕中央
        x = int((self.tk.winfo_screenwidth()-self.width)/2)
        y = int((self.tk.winfo_screenheight()-self.height)/2)
        size_geo = '%dx%d+%d+%d' % (self.width, self.height, x, y)
        self.bg_color = get_color(x, y)

        self.tk.geometry(size_geo)
        # 去除窗口边框、最大最小关闭按钮，同时任务栏不显示窗口
        self.tk.overrideredirect(True)
        # 设置为窗口最前
        self.tk.attributes("-topmost", True)
        # 绑定按键事件
        # 向上 显示窗口
        keyboard.add_hotkey('up', self.key_up)
        # 向下 隐藏窗口
        keyboard.add_hotkey('down', self.key_down)
        # 向左 上一页
        keyboard.add_hotkey('left', self.key_left)
        # 向右 下一页
        keyboard.add_hotkey('right', self.key_right)
        # ctrl+向下 退出
        keyboard.add_hotkey('ctrl+down', self.key_exit)
        # 滚轮翻页
        mouse.hook(self.key_wheel)
        # 按下左键 保存当前窗口坐标
        self.tk.bind('<Button-1>', self.save_last)
        # 拖动左键 移动窗口
        self.tk.bind("<B1-Motion>", self.drag)
        # 加载内容
        self.load_book()
        # 释放左键 修改窗口背景颜色
        self.tk.bind("<ButtonRelease-1>", self.change_bg)
        # 设置右键菜单
        self.set_menu()

    def run(self):
        self.tk.mainloop()

    def load_book(self):
        line = linecache.getline("./"+self.nowVar.get(), self.linenum)
        self.text.set(line)
        self.lb = Label(self.tk, textvariable=self.text, foreground=self.text_color, font=(self.font_name, self.font_size),
                        background=self.bg_color,
                        width=self.width,  wraplength=self.width - self.font_size/2, anchor="nw", justify="left")
        self.lb.pack()
        # 调整窗口和文本大小一致
        self.height = math.ceil(
            len(line)*(self.font_px+1) / self.width)*(self.font_px+6)
        self.tk.geometry("%dx%d" %
                         (self.width, self.height))

    def set_menu(self):
        self.menu = Menu(self.tk, tearoff=False)
        select_file_menu = Menu(self.tk, tearoff=False)
        for f in self.files.keys():
            select_file_menu.add_radiobutton(
                label=f,  variable=self.nowVar, value=f, command=self.select_file)
        self.menu.add_cascade(label="选择",  menu=select_file_menu)
        self.menu.add_command(label="跳转",  command=self.change_line)
        self.menu.add_command(label="退出",  command=self.key_exit)
        self.tk.bind("<Button-3>", self.show_menu)

    def select_file(self):
        if self.now != self.nowVar.get():
            self.config["now"] = self.nowVar.get()
            self.save_config()
            self.load_config()
            self.load_book()

    def change_line(self):
        self.listen_wheel = False
        skip = SkipDialog("跳转", "请输入想要跳转的行数:", self.nowVar.get(),
                          initialvalue=self.linenum, minvalue=1)
        self.listen_wheel = True
        linenum = skip.result
        if linenum is not None:
            self.linenum = linenum
            self.next_line()

    def save_last(self, event):
        self.lastClickX = event.x
        self.lastClickY = event.y

    def show_menu(self, event):
        # 使用 post()在指定的位置显示弹出菜单
        self.menu.post(event.x_root, event.y_root)

    def drag(self, event):
        x = event.x - self.lastClickX + self.tk.winfo_x()
        y = event.y - self.lastClickY + self.tk.winfo_y()
        self.tk.geometry("+%s+%s" % (x, y))

    def change_bg(self, event):
        # 取左上顶点的左边一个像素获取颜色
        x = self.tk.winfo_x() - 1
        y = self.tk.winfo_y()
        if x < 0:
            x = 0
        self.bg_color = get_color(x, y)
        self.lb.config(background=self.bg_color)

    def key_up(self):
        self.hide = False
        self.tk.update()
        self.tk.deiconify()

    def key_down(self):
        self.hide = True
        self.tk.update()
        self.tk.withdraw()
        self.save_config()

    def key_left(self):
        while True:
            if self.linenum <= 0:
                break
            self.linenum -= 1
            if self.next_line():
                break

    def key_right(self):
        while True:
            self.linenum += 1
            if self.next_line():
                break

    def key_wheel(self, event):
        if self.listen_wheel and not self.hide and isinstance(event, mouse.WheelEvent):
            if event.delta > 0:
                self.key_left()
            elif event.delta < 0:
                self.key_right()

    def next_line(self):
        line = linecache.getline(
            "./"+self.now, self.linenum)
        # 空内容直接跳过
        if line.strip() == "":
            return FALSE
        self.text.set(line)
        # 调整窗口和文本大小一致
        self.height = math.ceil(
            len(line)*(self.font_px+1) / self.width)*(self.font_px+6)
        self.tk.geometry("%dx%d" %
                         (self.width, self.height))
        return True

    def key_exit(self):
        print("exit")
        self.save_config()
        self.tk.destroy()


if __name__ == "__main__":
    r = MRead()
    r.run()
