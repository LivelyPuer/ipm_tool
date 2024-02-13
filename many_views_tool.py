import json
import os
from tkinter import *
from tkinter import filedialog as fd

import numpy as np
from PIL import Image
from matplotlib import pyplot as plt

from homography_tool import HomographyTool
from ipm_calibration_tool import CalibrationTool

side_name = {
    (0, 0): "forward_left",
    (0, 1): "left",
    (0, 2): "backward_left",
    (1, 0): "forward",
    (1, 2): "backward",
    (2, 0): "forward_right",
    (2, 1): "right",
    (2, 2): "backward_right",
}
show_side = {
    "forward": 2,
    "left": 4,
    "right": 6,
    "backward": 8,
}
rotate_side = {
    "forward": lambda x: x,
    "left": lambda x: np.rot90(x),
    "right": lambda x: np.rot90(x, -1),
    "backward": lambda x: np.rot90(x, 2),
}
project_root = "data"


def get_rgb(rgb):
    return "#%02x%02x%02x" % rgb


class Camera:
    def __init__(self, tk_object, pos):
        self.tk_object = tk_object
        self.pos = pos


class ManyCameras:
    def __init__(self):
        self.root = Tk()
        self.start_pos = (450, 100)
        self.root.title("Calibration tool for IPM")  # title of the GUI window
        self.root.maxsize(1500, 1000)  # specify the max size the window can expand to
        self.nav = Canvas(self.root)
        self.nav.config(width=1500, height=100)
        self.nav.grid(row=0, column=0)
        self.cameras = []
        self.canvas = Canvas(self.root)
        self.canvas.config(width=1500, height=1300)
        self.canvas.grid(row=1, column=0)
        self.canvas.bind('<Button-1>', self.selected)
        self.config_text = ""
        self.images = {}
        self.place_camera_elements()

        self.find_homography_button = Button(
            self.nav,
            text='Load config',
            command=self.load_config
        )
        self.load_image_button = Button(
            self.nav,
            text='Load images',
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
        self.root.mainloop()
        self.images = {}

    def place_camera_elements(self):

        self.canvas.create_text(750, 50,
                                text="Forward",
                                justify=CENTER, font="Verdana 14")
        self.canvas.create_text(100, 100, text=self.config_text, font="Verdana 14", tags="config_text")
        self.canvas.create_text(100, 500, text=str(self.images), font="Verdana 14", tags="images_text")

        for r in range(3):
            for c in range(3):
                if r == 1 and c == 1:
                    self.canvas.create_rectangle(self.start_pos[0] + 10 + 200 * r, self.start_pos[1] + 10 + 200 * c,
                                                 self.start_pos[0] + 200 * (r + 1), self.start_pos[1] + 200 * (c + 1),
                                                 fill='grey',
                                                 outline='blue',
                                                 width=3,
                                                 activedash=(5, 4), tags=f"{r}  {c}")
                else:
                    self.cameras.append(Camera(
                        self.canvas.create_rectangle(self.start_pos[0] + 10 + 200 * r, self.start_pos[1] + 10 + 200 * c,
                                                     self.start_pos[0] + 200 * (r + 1),
                                                     self.start_pos[1] + 200 * (c + 1),
                                                     fill='yellow',
                                                     outline='green',
                                                     width=3,
                                                     activedash=(5, 4)), (r, c)))

    def load_config(self):
        self.config_text = os.listdir(os.path.join(project_root, "config"))
        self.canvas.itemconfig("config_text", text="\n".join(self.config_text))

    def load_images(self):
        filename = fd.askopenfilename(filetypes=[("JSON file", "*.json")])
        with open(filename) as file:
            images = json.load(file)
            self.images = dict(images["data"])
        self.canvas.itemconfig("images_text", text="\n".join(self.images))

    def load_homografy(self):
        fig = plt.figure()

        for k, v in self.images.items():
            print(k, v)
            config_path = os.path.join(project_root, "config", f'{k}.yaml')

            ht = HomographyTool()
            ht.load_image(v)
            ht.load_config(config_path)
            self.images[k] = Image.fromarray(rotate_side[k](ht.find_homography()))
            ax1 = fig.add_subplot(3, 3, show_side[k])
            ax1.imshow(self.images[k])
        res = Image.new("RGB", (1200 * 3, 1200 * 3), color="black")
        res.paste(self.images["forward"], (1200, 0))
        res.paste(self.images["left"], (0, 1200))
        res.paste(self.images["backward"], (1200, 2400))
        res.paste(self.images["right"], (2400, 1200))

        ax1 = fig.add_subplot(3, 3, 5)
        ax1.imshow(res)
        fig.show()
    def selected(self, event):
        pos_x = (event.x - self.start_pos[0]) // 200
        pos_y = (event.y - self.start_pos[1]) // 200
        CalibrationTool(self.root, side_name[(pos_x, pos_y)], os.path.join(project_root, "config"))
