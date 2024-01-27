from tkinter import *


class ManyCameras:
    def __init__(self):
        self.root = Tk()

        self.root.title("Calibration tool for IPM")  # title of the GUI window
        self.root.maxsize(1500, 1000)  # specify the max size the window can expand to

        self.left_frame = Frame(self.root, width=1000, height=100)
        self.left_frame.grid(row=0, column=0, padx=10, pady=5, columnspan=2)

        self.center_frame = Frame(self.root, width=500, height=400)
        self.center_frame.grid(row=1, column=0, padx=10, pady=5)

        self.canvas = Canvas(self.center_frame)
        self.canvas.grid(row=0, column=0)
        self.canvas.config(width=500, height=500)
        # self.limits_container.bind("<B1-Motion>", self.drag)

        self.place_camera_elements()
        self.root.mainloop()

    def place_camera_elements(self):
        self.canvas.delete('all')

        self.canvas.create_rectangle(200, 100, 300, 400, tags="car", fill="yellow")