import os
import time
import datetime
import io
import PIL.Image
import random

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QSize, QThreadPool, QRect, QMutex, QRunnable
from PyQt5.QtGui import QImage, QPainter

import parameters
from misc import encodeImage
from tabs.basic.basic_input import BasicInputRole

class OutputWriter(QRunnable):
    guard = QMutex()
    def __init__(self, img, metadata, outputs, subfolder, filename):
        super(OutputWriter, self).__init__()
        self.setAutoDelete(True)

        if not OutputWriter.guard.tryLock(5000):
            OutputWriter.guard.unlock()
            OutputWriter.guard.lock()

        m = PIL.PngImagePlugin.PngInfo()
        if metadata:
            m.add_text("parameters", parameters.formatParameters(metadata))

        folder = os.path.join(outputs, subfolder)
        os.makedirs(folder, exist_ok=True)

        if not filename:
            idx = parameters.getIndex(folder)
            filename = f"{idx:08d}-" + datetime.datetime.now().strftime("%m%d%H%M")

        self.img = img
        self.tmp = os.path.join(folder, f"{filename}.tmp")
        self.file = os.path.join(folder, f"{filename}.png")
        self.metadata = m

    @pyqtSlot()
    def run(self):
        if type(self.img) == QImage:
            self.img = encodeImage(self.img)

        if type(self.img) == bytes:
            self.img = PIL.Image.open(io.BytesIO(self.img))

        self.img.save(self.tmp, format="PNG", pnginfo=self.metadata)
        os.replace(self.tmp, self.file)

        OutputWriter.guard.unlock()

class RequestManager(QObject):
    artifact = pyqtSignal(int, QImage, str)
    result = pyqtSignal(int, QImage, object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.parameters = None

        self.requests = []
        self.count = 0
        self.seed = 0
        
        self.ids = []
        self.mapping = {}

        self.annotations = {}

        self.subfolders = {}
        self.filenames = {}

        self.monitoring = False

        self.grid = None
        self.grid_image = None
        self.grid_images = {}
        self.grid_id = None

    def setRequests(self, requests):
        self.requests = requests
        self.count = len(requests)

    def makeRequest(self, request=None):
        if not request:
            request = self.requests.pop()
        filename = self.finalizeRequest(request)

        subfolder = ""
        if self.parameters:
            subfolder = self.parameters._values.get("output_folder")
        id = self.gui.makeRequest(request)

        self.subfolders[id] = subfolder or request["type"]
        self.filenames[id] = filename if subfolder else ""
        self.ids += [id]
        return id
    
    def makeAnnotationRequest(self, request, input_id):
        id = self.makeRequest(request)
        self.annotations[id] = input_id

    def cancelRequest(self):
        if self.ids:
            self.setRequests([])
            self.gui.cancelRequest(self.ids.pop())

    def finalizeRequest(self, request):
        data = request["data"]
        filename = None
        for k in ["image", "mask", "cn_image", "area"]:
            for i in range(len(data.get(k, []))):
                if not data[k][i]:
                    continue
                if type(data[k][i]) == str:
                    if not filename:
                        filename = data[k][i]
                    data[k][i] = encodeImage(QImage(data[k][i]))
                elif type(data[k][i]) == list:
                    for j in range(len(data[k][i])):
                        if type(data[k][i][j]) == str:
                            if not filename:
                                filename = data[k][i][j]
                            data[k][i][j] = encodeImage(QImage(data[k][i][j]))
        if filename:
            filename = filename.rsplit(os.path.sep, 1)[-1].rsplit(".", 1)[0]

        return filename
    
    def parseInputs(self, inputs):
        found = {}
        links = {}
        controls = {}

        segmentation = []
        
        if inputs:
            for i in inputs:
                data = []
                if i._role == BasicInputRole.IMAGE:
                    if i._image and not i._image.isNull():
                        data += [encodeImage(i._originalCrop or i._original)]
                    if i._files:
                        for f in i._files[::-1]:
                            data += [i.getFilePath(f)]
                    if data:
                        found[i] = data
                if i._role == BasicInputRole.MASK or (i._role == BasicInputRole.CONTROL and i._control_mode == "Inpaint"):
                    if i._linked:
                        links[i] = i._linked
                        if i._image and not i._image.isNull():
                            data += [encodeImage(i._image)]
                        if i._files:
                            for f in i._files[::-1]:
                                data += [i.getFilePath(f)]
                        if data:
                            found[i] = data
                            data = []
                if i._role == BasicInputRole.SUBPROMPT:
                    if i._linked:
                        links[i] = i._linked
                    if i._image and not i._image.isNull():
                        data += [[encodeImage(a) for a in i.getAreas()]]
                    if data:
                        found[i] = data
                if i._role == BasicInputRole.CONTROL:
                    model = i._control_settings.get("mode")
                    opts = {
                        "scale": i._control_settings.get("strength"),
                        "annotator": i._control_settings.get("preprocessor"),
                        "args": i.getControlArgs()
                    }
                    k = i
                    if model == "Inpaint" and i._linked:
                        k = i._linked
                    if k._image and not k._image.isNull():
                        data += [(model, opts, encodeImage(k._image or k._original))]
                    if k._files:
                        for f in k._files[::-1]:
                            data += [(model, opts, k.getFilePath(f))]
                    if data:
                        controls[i] = data
                if i._role == BasicInputRole.SEGMENTATION:
                    opts = i.getSegmentationArgs()
                    if i._image and not i._image.isNull():
                        data += [(encodeImage(i._originalCrop or i._original), opts)]
                    if i._files:
                        for f in i._files[::-1]:
                            data += [(i.getFilePath(f), opts)]
                    if data:
                        segmentation += data

        return found, links, controls, segmentation

    def buildRequests(self, parameters, inputs):
        self.parameters = parameters

        found, links, controls, segmentation = self.parseInputs(inputs)

        if segmentation:
            self.buildSegmentationRequests(segmentation)
        else:
            self.buildStandardRequests(found, links, controls)
            if False:
                base = self.requests[0]
                self.buildGridRequests(base)

    def buildSegmentationRequests(self, segmentation):
        requests = []
        for img, opts in segmentation:
            request = {
                "type": "segmentation",
                "data": {
                    "image": [img],
                    "seg_opts": [opts],
                    "device": self.parameters._values.get("device")
                }
            }
            requests += [request]
        self.setRequests(requests)

    def buildStandardRequests(self, found, links, controls):
        images, masks, areas = [], [], []
        used = []
        for k in found:
            if k in used:
                continue
            linked = [k] + [i for i in links if links[i] == k]
            size = max([len(found[i]) for i in linked])
            for z in range(size):
                img, msk, are = None, None, []
                for j in linked:
                    data = found[j][z % len(found[j])]
                    if j._role == BasicInputRole.IMAGE:
                        img = data
                    if j._role == BasicInputRole.MASK or (j._role == BasicInputRole.CONTROL and j._control_mode == "Inpaint"):
                        msk = data
                    if j._role == BasicInputRole.SUBPROMPT:
                        are = data
                if msk and not img:
                    continue
                images += [img]
                masks += [msk]
                areas += [are]
            used += linked

        seed = int(self.parameters._values.get("seed"))
        subseed = int(self.parameters._values.get("subseed"))
        if seed == -1:
            seed = random.randrange(2147483646)
        if subseed == -1:
            subseed = random.randrange(2147483646)

        batch_size = int(self.parameters._values.get("batch_size"))
        batch_count = int(self.parameters._values.get("batch_count"))

        total = max([len(controls[k]) for k in controls]) if controls else 0
        total = max(len(images), batch_count * batch_size, total)

        def get_portion(data, start, amount):
            if not data:
                return []
            out = []
            for i in range(amount):
                out += [data[(start+i)%len(data)]]
            return out

        requests = []
        i = 0
        ci = 0
        while total > 0:
            size = min(total, batch_size)
            batch_images = get_portion(images, i, size)
            batch_masks = get_portion(masks, i, size)
            batch_areas = get_portion(areas, i, size)
            batch_control = [controls[k][ci%len(controls[k])] for k in controls]

            if any([b == None for b in batch_images]):
                batch_images, batch_masks = [], []

            i += batch_size
            total -= batch_size
            ci += 1
            
            request = self.parameters.buildRequest(size, batch_images, batch_masks, batch_areas, batch_control)

            if "seed" in request["data"]:
                request["data"]["seed"] = seed
                seed += size

            if "subseed" in request["data"]:
                request["data"]["subseed"] = subseed
                subseed += size

            requests += [request]
        
        self.setRequests(requests)
    
    def buildGridRequests(self, base):
        self.setRequests([base] * 4)

    def handleResult(self, id, name):
        if not id in self.ids:
            if not (self.monitoring and name == "result"):
                return

        if not id in self.mapping:
            self.mapping[id] = (time.time_ns() // 1000000) % (2**31 - 1)

        if self.grid != None:
            if self.grid_id == None:
                self.grid_id = id
            self.gridResult(id, self.mapping[self.grid_id], name)
        else:
            self.normalResult(id, self.mapping[id], name)

    def normalResult(self, id, out, name):
        if name == "preview":
            previews = self.gui._results[id]["preview"]
            out = self.mapping[id]
            for i in range(len(previews)-1, -1, -1):
                self.artifact.emit(out, previews[i], "preview")
                out += 1

        if name == "result":
            if id in self.ids:
                self.ids.remove(id)
            results = self.gui._results[id]["result"]
            metadata = self.gui._results[id].get("metadata", None)
            artifacts = {k:v for k,v in self.gui._results[id].items() if not k in {"result", "metadata", "preview"}}
            out = self.mapping[id]

            if id in self.annotations:
                self.artifact.emit(self.annotations[id], results[0], "Annotated")
                del self.annotations[id]
                return

            for i in range(len(results)-1, -1, -1):
                result = results[i]
                meta = metadata[i] if metadata else None

                subfolder = self.subfolders.get(id, "monitor")
                filename = self.filenames.get(id, None)
                writer = OutputWriter(result, meta, self.gui.outputDirectory(), subfolder, filename)
                file = writer.file
                QThreadPool.globalInstance().start(writer)

                self.result.emit(out, result, meta, file)

                artifacts = {k:v[i%len(v)] for k,v in artifacts.items() if v[i%len(v)]}
                for k, v in artifacts.items():
                    self.artifact.emit(out, v, k)

                out += 1

    def gridResult(self, id, out, name):
        available = self.gui._results[id]
        if "result" in available:
            images = available["result"]
        elif "preview" in available:
            images = available["preview"]
        else:
            return
        
        for i in range(len(images)-1, -1, -1):
            if not id + i in self.grid:
                self.grid += [id + i]
            self.grid_images[id + i] = images[i]

        wc, hc = 2, 2
        w, h = 512, 512
        grid = QImage(QSize(int(w*wc),int(h*hc)), QImage.Format_ARGB32_Premultiplied)
        grid.fill(0)

        painter = QPainter(grid)
        for x in range(2):
            for y in range(2):
                idx = y*2 + x
                if idx >= len(self.grid):
                    continue
                image = self.grid_images[self.grid[idx]]
                painter.drawImage(QRect(int(x*w), int(y*h), w, h), image)
        painter.end()
        
        if name == "preview":
            self.artifact.emit(out, grid, "preview")
        elif name == "result":
            if id in self.ids:
                self.ids.remove(id)

            subfolder = self.subfolders.get(self.grid_id, "monitor")
            filename = self.filenames.get(self.grid_id, None)
            writer = OutputWriter(grid, None, self.gui.outputDirectory(), subfolder, filename)
            file = writer.file
            QThreadPool.globalInstance().start(writer)

            self.result.emit(out, grid, None, file)