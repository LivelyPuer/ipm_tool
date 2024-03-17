import json
import os
from tkinter import *
from tkinter import filedialog as fd

import PIL
from PIL import Image, ImageTk
from matplotlib import pyplot as plt

from homography_tool import HomographyTool
from ipm360 import IPM360
from ipm_calibration_tool import CalibrationTool
from untils.rectangle import rectangle

project_root = "data"


def get_rgb(rgb):
    return "#%02x%02x%02x" % rgb


class Camera:
    def __init__(self, tk_object, pos):
        self.tk_object = tk_object
        self.pos = pos


class ManyCameras:
    cameras_count = 6
    preview_image_size = 200
    # Позиционирование камер проходит против часовой стрелки от камеры, смотрящей вперед
    default_cameras_positions = [(200, 0), (0, 200), (0, 400), (200, 600), (400, 400), (400, 200)]
    cameras_position = []
    cameras_images = [None for i in range(cameras_count)]
    rotated_cameras_images = []

    def my_callback(self, var):
        self.place_camera_elements()

    def __init__(self):
        self.fullconfig = {"data": []}
        for i in range(self.cameras_count):
            self.fullconfig["data"].append({"pos": self.default_cameras_positions[i], "angle": 0, "homography": {}})
        self.root = Tk()
        self.start_pos = (450, 100)
        self.root.title("Calibration tool for IPM")  # title of the GUI window
        self.root.maxsize(1500, 1000)  # specify the max size the window can expand to
        self.nav = Canvas(self.root)
        self.nav.config(width=1500, height=100)
        self.nav.grid(row=0, column=0)
        self.cameras = []
        self.canvas = Canvas(self.root)
        self.canvas.config(width=750, height=900)
        self.canvas.grid(row=1, column=0)
        self.canvas.bind('<Button-1>', self.selected)
        self.frame_config = Frame(self.root, borderwidth=1, relief=SOLID)
        self.frame_config.config(width=600, height=600)
        self.frame_config.grid(row=1, column=1, padx=5, pady=5)
        self.configs_frames = []
        for i in range(self.cameras_count):
            card = Frame(self.frame_config, borderwidth=1, relief=SOLID)
            self.configs_frames.append(card)
            card.config(width=560, height=130)
            card.grid(row=int(i / 2), column=i % 2, padx=10, pady=10)

            varx = IntVar()
            vary = IntVar()
            vara = IntVar()

            varx.set(self.default_cameras_positions[i][0])
            vary.set(self.default_cameras_positions[i][1])

            ll = Label(card, text=f"Camera {i}")
            ll.grid(row=0)

            lx = Label(card, text="X")
            lx.grid(row=1, column=0)
            wx = Scale(card, from_=0, to=600, orient=HORIZONTAL, variable=varx, command=self.my_callback)
            wx.grid(row=1, column=1)

            wx.bind("<Button-1>", lambda event: event.widget.focus_set())

            ly = Label(card, text="Y")
            ly.grid(row=2, column=0)
            wy = Scale(card, from_=0, to=600, orient=HORIZONTAL, variable=vary, command=self.my_callback)
            wy.grid(row=2, column=1)
            wy.bind("<Button-1>", lambda event: event.widget.focus_set())

            la = Label(card, text="Angle")
            la.grid(row=3, column=0)
            wa = Scale(card, from_=0, to=359, orient=HORIZONTAL, variable=vara, command=self.my_callback)
            wa.grid(row=3, column=1)
            wa.bind("<Button-1>", lambda event: event.widget.focus_set())

            self.cameras_position.append((wx, wy))
            self.rotated_cameras_images.append(wa)

        self.images = {}
        self.place_camera_elements()

        self.find_homography_button = Button(
            self.nav,
            text='Load config',
            command=self.load_config
        )
        self.save_config_button = Button(
            self.nav,
            text='Save config',
            command=self.save_config
        )
        self.load_image_button = Button(
            self.nav,
            text='Load preview images',
            command=self.load_images
        )
        self.load_homografy_button = Button(
            self.nav,
            text='Load homografy',
            command=self.load_homografy
        )
        self.find_homography_button.grid(row=0, column=1, padx=5, pady=5)
        self.load_image_button.grid(row=0, column=2, padx=5, pady=5)
        self.load_homografy_button.grid(row=0, column=3, padx=5, pady=5)
        self.save_config_button.grid(row=0, column=4, padx=5, pady=5)
        self.root.mainloop()
        self.images = {}

    def place_camera_elements(self):
        self.canvas.delete("all")
        # self.canvas.create_image(0, 0,
        #                          anchor=NW, image=PhotoImage("data/set1/set1_back.png"))
        # Отображение предпросмотра камер
        for i in range(len(self.cameras_position)):
            if not self.cameras_images[i]:
                self.canvas.create_rectangle(
                    *rectangle(self.cameras_position[i][0].get(), self.cameras_position[i][1].get(),
                               200, 200),
                    fill='grey',
                    outline='blue',
                    width=3,
                    activedash=(5, 4), tags=f"camera_{i}")
            else:
                img = self.cameras_images[i].rotate(self.rotated_cameras_images[i].get(), PIL.Image.NEAREST,
                                                    expand=1).convert('RGBA')
                pixdata = img.load()

                width, height = img.size
                for y in range(height):
                    for x in range(width):
                        if pixdata[x, y] == (0, 0, 0, 255):
                            pixdata[x, y] = (0, 0, 0, 0)
                photo = ImageTk.PhotoImage(img)
                globals()[f"self.canvas.photo{i}"] = photo
                self.canvas.create_image(self.cameras_position[i][0].get(), self.cameras_position[i][1].get(),
                                         anchor=NW, image=photo)
                # Отображение списка конфигов
                # for i in range(len(self.default_cameras_positions)):

    def load_config(self):
        filename = fd.askopenfilename(filetypes=[("JSON config", "*.json")])
        if not os.path.exists(filename):
            print('Config file not found. Use default values')
            return
        with open(filename) as file:
            config = json.load(file)
        self.fullconfig = dict(config)
        self.parce_config()

    def parce_config(self):
        for i in range(len(self.cameras_position)):
            self.cameras_position[i][0].set(self.fullconfig["data"][i]["pos"][0] // 4)
            self.cameras_position[i][1].set(self.fullconfig["data"][i]["pos"][1] // 4)
            self.rotated_cameras_images[i].set(self.fullconfig["data"][i]["angle"])
        self.place_camera_elements()

    def save_config(self):
        filename = fd.asksaveasfile(filetypes=[("JSON config", "*.json")]).name
        if filename.split(".")[-1] != "json":
            filename += ".json"
        self.save_pos_to_fullconfig()
        with open(filename, 'w') as file:
            json.dump(self.fullconfig, file)

    def save_pos_to_fullconfig(self):
        for i in range(len(self.cameras_position)):
            self.fullconfig["data"][i]["pos"] = (
            self.cameras_position[i][0].get() * 4, self.cameras_position[i][1].get() * 4)
            self.fullconfig["data"][i]["angle"] = self.rotated_cameras_images[i].get()

    def load_images(self):
        ipm360 = IPM360()
        ipm360.load_config(self.fullconfig)
        ipm360.homography360(self.cameras_images).show()

    def load_homografy(self):
        fig = plt.figure()

        for k, v in self.images.items():
            config_path = os.path.join(project_root, "config", f'{k}.yaml')

            ht = HomographyTool()
            ht.load_image(v)
            ht.load_config(config_path)
            img = Image.fromarray(ht.find_homography())
            # self.cameras_images[] img.resize((self.preview_image_size, self.preview_image_size))
        res = Image.new("RGB", (1200 * 3, 1200 * 3), color="black")
        res.paste(self.images["forward"], (1200, 0))
        res.paste(self.images["left"], (0, 1200))
        res.paste(self.images["backward"], (1200, 2400))
        res.paste(self.images["right"], (2400, 1200))

        ax1 = fig.add_subplot(3, 3, 5)
        ax1.imshow(res)
        fig.show()

    def selected(self, event):
        nearby_tags = self.canvas.find_closest(event.x, event.y)
        if self.canvas.gettags(nearby_tags[0])[0].split("_")[0] != "camera":
            return
        idx = int(self.canvas.gettags(nearby_tags[0])[0].split("_")[1])
        cb = CalibrationTool(self.root, f"Camera #{idx}", os.path.join(project_root, "config"))
        config, image = cb.get_data()
        if config and image:
            print(config, image)
            image = image.resize((200, 200))
            self.fullconfig["data"][idx]["homography"] = config
            self.cameras_images[idx] = image
            self.place_camera_elements()
