import re
import os
import ctypes
import math

#NOTE: imported by launcher

try:
    ctypes.windll.ole32.CoInitialize.restype = ctypes.HRESULT
    ctypes.windll.ole32.CoInitialize.argtypes = [ctypes.c_void_p]
    ctypes.windll.ole32.CoUninitialize.restype = None
    ctypes.windll.ole32.CoUninitialize.argtypes = None
    ctypes.windll.shell32.ILCreateFromPathW.restype = ctypes.c_void_p
    ctypes.windll.shell32.ILCreateFromPathW.argtypes = [ctypes.c_char_p]
    ctypes.windll.shell32.SHOpenFolderAndSelectItems.restype = ctypes.HRESULT
    ctypes.windll.shell32.SHOpenFolderAndSelectItems.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_ulong]
    ctypes.windll.shell32.ILFree.restype = None
    ctypes.windll.shell32.ILFree.argtypes = [ctypes.c_void_p]
except Exception:
    pass

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData, QByteArray, QBuffer, QIODevice, QUrl
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QColor, QImage, QSyntaxHighlighter, QColor
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from PyQt5.QtQml import qmlRegisterType, qmlRegisterUncreatableType

class FocusReleaser(QQuickItem):
    releaseFocus = pyqtSignal()
    dropped = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.setFiltersChildMouseEvents(True)
    
    def onPress(self, source):
        if not source.hasActiveFocus():
            self.releaseFocus.emit()

    def childMouseEventFilter(self, child, event):
        if event.type() == QEvent.MouseButtonPress:
            self.onPress(child)
        return False

    def mousePressEvent(self, event):
        self.onPress(self)
        event.setAccepted(False)

class ImageDisplay(QQuickPaintedItem):
    imageUpdated = pyqtSignal()
    sizeUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._centered = False
        self._trueWidth = 0
        self._trueHeight = 0
        self._trueX = 0
        self._trueY = 0

    @pyqtProperty(QImage, notify=imageUpdated)
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._last = None
        self._image = image

        self.setImplicitHeight(image.height())
        self.setImplicitWidth(image.width())
        self.imageUpdated.emit()

        if self._image and not self._image.isNull():
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio)
            if self._trueWidth != img.width() or self._trueHeight != img.height():
                self._trueWidth = img.width()
                self._trueHeight = img.height()
                self._trueX, self._trueY = self.arrange(img)
                self.sizeUpdated.emit()
        else:
            self._trueWidth = 0
            self._trueHeight = 0
            self.sizeUpdated.emit()

        self.update()

    @pyqtSlot(result=QImage)
    def clear(self):
        return QImage()

    @pyqtProperty(bool, notify=imageUpdated)
    def centered(self):
        return self._centered
    
    @centered.setter
    def centered(self, centered):
        self._centered = centered
        self.imageUpdated.emit()
        self.update()

    @pyqtProperty(int, notify=sizeUpdated)
    def trueWidth(self):
        return self._trueWidth
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueHeight(self):
        return self._trueHeight
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueX(self):
        return self._trueX
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueY(self):
        return self._trueY

    @pyqtProperty(int, notify=imageUpdated)
    def sourceWidth(self):
        if self._image:
            return self._image.width()
        return 0
    
    @pyqtProperty(int, notify=imageUpdated)
    def sourceHeight(self):
        if self._image:
            return self._image.height()
        return 0
    
    def arrange(self, img):
        x, y = 0, 0
        if self.centered:
            x = int((self.width() - img.width())/2)
            y = int((self.height() - img.height())//2)
        return x, y

    def paint(self, painter):
        if self._image and not self._image.isNull():
            transform = Qt.SmoothTransformation
            if not self.smooth():
                transform = Qt.FastTransformation

            # FIX THIS CRAP
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio, transform)
            x, y = self.arrange(img)

            if self._trueWidth != img.width() or self._trueHeight != img.height():
                self._trueWidth = img.width()
                self._trueHeight = img.height()
                self._trueX = x
                self._trueY = y
                self.sizeUpdated.emit()
            painter.drawImage(x,y,img)

class MimeData(QObject):
    def __init__(self, mimeData, parent=None):
        super().__init__(parent)
        self._mimeData = mimeData

    @pyqtProperty(QMimeData)
    def mimeData(self):
        return self._mimeData

class DropArea(QQuickItem):
    dropped = pyqtSignal(MimeData, arguments=["mimeData"])
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QQuickItem.ItemAcceptsDrops, True)
        self._containsDrag = False
        self._filters = []
    
    @pyqtProperty(bool, notify=updated)
    def containsDrag(self):
        return self._containsDrag
    
    @pyqtProperty(list, notify=updated)
    def filters(self):
        return self._filters
    
    def accepted(self, mimeData):
        if not self._filters:
            return True
        formats = mimeData.formats()
        if any([f in formats for f in self._filters]):
            return True
        if mimeData.hasUrls():
            for url in mimeData.urls():
                if url.scheme() in self._filters:
                    return True
                if url.isLocalFile():
                    ext = "*." + url.toLocalFile().rsplit('.',1)[-1].lower()
                    if ext in self._filters:
                        return True
        return False

    @filters.setter
    def filters(self, filters):
        self._filters = filters
        self.updated.emit()

    def dragEnterEvent(self, enter):
        if self.accepted(enter.mimeData()):
            enter.accept()
            self._containsDrag = True
            self.updated.emit()

    def dragLeaveEvent(self, leave):
        leave.accept()
        self._containsDrag = False
        self.updated.emit()

    def dragMoveEvent(self, move):
        if self.accepted(move.mimeData()):
            move.accept()

    def dropEvent(self, drop):
        if self.accepted(drop.mimeData()):
            drop.accept()
            self._containsDrag = False
            self.updated.emit()
            self.dropped.emit(MimeData(drop.mimeData()))

class SyntaxManager(QObject):
    def __init__(self, gui):
        super().__init__(gui)
        self.mode = "Prompt"
        self.ranges = False
        self.keywords = []
        self.highlighter = SyntaxHighlighter(self, gui)

    @pyqtSlot(str)
    def setMode(self, mode):
        self.mode = mode

    @pyqtSlot(bool)
    def setRanges(self, ranges):
        self.ranges = ranges

    @pyqtSlot(list)
    def setKeywords(self, keywords):
        self.keywords = [k.lower() for k in keywords]

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, manager, gui):
        super().__init__(gui)
        self.gui = gui
        self.manager = manager

    def highlightBlock(self, text):
        if self.manager.mode == "Prompt":
            self.highlightPrompt(text)
        elif self.manager.mode == "Keyword":
            self.highlightKeywords(text)
        elif self.manager.mode == "Integer":
            self.highlightIntegers(text)
        elif self.manager.mode == "Float":
            self.highlightFloats(text)

        if self.manager.ranges:
            self.highlightRanges(text)
        
    def highlightKeywords(self, text):
        good = QColor("#d0ff93")
        ok = QColor("#ffe993")
        err = QColor("#ff9393")
        for s, e in [m.span(0) for m in re.finditer("[^,]+?(?=,|$)", text)]:
            m = text[s:e].strip().lower()
            for k in self.manager.keywords:
                if k.startswith(m):
                    if k != m:
                        self.setFormat(s, e-s, ok)
                    else:
                        self.setFormat(s, e-s, good)
                        break
            else:
                self.setFormat(s, e-s, err)

    def highlightRanges(self,text):
        range = QColor("#93ffe9")
        range_bg = QColor("#d4faf2")

        for m in re.finditer(r"([+\-\d\.]+)-([+\-\d\.]+)((?:\(|\[)([+\-\d\.]+)(?:\)|\]))", text):
            s,e = m.span(0)
            self.setFormat(s, e-s, range_bg)
            for s,e in [m.span(1), m.span(2), m.span(4)]:
                self.setFormat(s, e-s, range)

    def highlightIntegers(self, text):
        err = QColor("#ff9393")
        for s, e in [m.span(0) for m in re.finditer("[^,]+?(?=,|$)", text)]:
            m = text[s:e].strip().lower()
            try:
                m = int(m)
            except:
                self.setFormat(s, e-s, err)
    
    def highlightFloats(self, text):
        err = QColor("#ff9393")
        for s, e in [m.span(0) for m in re.finditer("[^,]+?(?=,|$)", text)]:
            m = text[s:e].strip().lower()
            try:
                m = float(m)
            except:
                self.setFormat(s, e-s, err)
        
    def highlightPrompt(self, text):
        text = text + " "
        emb = QColor("#ffd893")
        lora_bg = QColor("#f9c7ff")
        lora = QColor("#d693ff")
        hn_bg = QColor("#c7fff6")
        hn = QColor("#93d6ff")
        err_bg = QColor("#ffc4c4")
        err = QColor("#ff9393")
        wild_bg = QColor("#c7ffd2")
        wild = QColor("#93ffa9")
        field = QColor("#9e9e9e")
        keyword = QColor("#ffb393")

        embeddings = set()
        if "TI" in self.gui._options:
            embeddings = set([self.gui.modelName(n) for n in self.gui._options["TI"]])

        loras = set()
        if "LoRA" in self.gui._options:
            loras = set([self.gui.modelName(n) for n in self.gui._options["LoRA"]])

        hns = set()
        if "HN" in self.gui._options:
            hns = set([self.gui.modelName(n) for n in self.gui._options["HN"]])

        wilds = set(self.gui.wildcards._wildcards.keys())

        for em in embeddings:
            for s, e  in [m.span() for m in re.finditer(em.lower(), text.lower())]:
                self.setFormat(s, e-s, emb)
        
        for s, e, ms, me in [(*m.span(0), *m.span(1)) for m in re.finditer("<@?lora:([^:>]+)([^>]+)?>", text.lower())]:
            m = text[ms:me]
            if m in loras:
                self.setFormat(s, e-s, lora_bg)
                self.setFormat(ms, me-ms, lora)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,lora)
            else:
                self.setFormat(s, e-s, err_bg)
                self.setFormat(ms, me-ms, err)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,err)
        
        for s, e, ms, me in [(*m.span(0), *m.span(1))  for m in re.finditer("<@?hypernet:([^:>]+)([^>]+)?>", text.lower())]:
            m = text[ms:me]
            if m in hns:
                self.setFormat(s, e-s, hn_bg)
                self.setFormat(ms, me-ms, hn)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,hn)
            else:
                self.setFormat(s, e-s, err_bg)
                self.setFormat(ms, me-ms, err)
                if text[s+1] == "@":
                    self.setFormat(s+1,1,err)

        for s, e, ms, me in [(*m.span(0), *m.span(1)) for m in re.finditer("@?__([^\s]+?)__(?!___)", text)]:
            m = text[ms:me]
            if m in wilds:
                self.setFormat(s, e-s, wild_bg)
                self.setFormat(ms, me-ms, wild)
                if text[s] == "@":
                    self.setFormat(s,1,wild)
            else:
                self.setFormat(s, e-s, err_bg)
                self.setFormat(ms, me-ms, err)
                if text[s] == "@":
                    self.setFormat(s,1,err)

        for s, e in [m.span(0) for m in re.finditer("((?<=\s|,)|^)(AND|BREAK|START|END)(?=\s|,|$)", text)]:
            self.setFormat(s, e-s, keyword)
        
        if text.startswith("Negative prompt: "):
            self.setFormat(0, 16, field)
        
        if text.startswith("Steps: "):
            for s, e in [m.span(1) for m in re.finditer("(?:\s)?([^,:]+):[^,]+(,)?", text.lower())]:
                self.setFormat(s, e-s, field)

def encodeImage(img):
    ba = QByteArray()
    bf = QBuffer(ba)
    bf.open(QIODevice.WriteOnly)
    img.save(bf, "PNG")
    return ba.data()

def cropImage(img, size, offset_x = 0, offset_y = 0, scale = 1):
    in_z = img.size()
        
    ar = size.width()/size.height()

    rh = in_z.height()/size.height()
    rw = in_z.width()/size.width()

    w, h = in_z.width(), in_z.height()

    if size.width() * rh > in_z.width():
        h = math.ceil(w / ar)
    elif size.height() * rw > in_z.height():
        w = math.ceil(h * ar)

    w, h = int(w / scale), int(h / scale)

    ox = (offset_x + 1)/2
    oy = (offset_y + 1)/2

    dx = int((in_z.width()-w)*ox)
    dy = int((in_z.height()-h)*oy)

    return img.copy(dx, dy, w, h)

def showFilesInExplorer(folder, files):
    ctypes.windll.ole32.CoInitialize(None)

    files = [os.path.normpath(f) for f in files]
    folder = os.path.normpath(folder)
    count = len(files)

    folder_pidl = ctypes.windll.shell32.ILCreateFromPathW(folder.encode('utf-16le') + b'\0')
    files_pidl = [
        ctypes.windll.shell32.ILCreateFromPathW(f.encode('utf-16le') + b'\0') for f in files
    ]

    files_pidl_arr = (ctypes.c_void_p * count)(*files_pidl)

    ctypes.windll.shell32.SHOpenFolderAndSelectItems(folder_pidl, count, files_pidl_arr, 0)

    for pidl in files_pidl[::-1]:
        ctypes.windll.shell32.ILFree(pidl)
    ctypes.windll.shell32.ILFree(folder_pidl)

    ctypes.windll.ole32.CoUninitialize()

NATSORT_KEY = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]

def sortFiles(files):
    return sorted(files, key=lambda f: NATSORT_KEY(f.rsplit(os.path.sep,1)[-1]))

def formatFloat(f):
    return f"{f:.4f}".rstrip('0').rstrip('.')

def weightText(text, inc, start, end):
    nothing = {"text": text, "start": start, "end": end}

    if not text:
        return nothing

    pre = {'<':-1, '(':-1, '[':-1}
    post = {'>':-1, ')':-1, ']':-1}
    inv = {'<':'>', '(':')', '[':']'}
    
    if text[start-1] in pre and (text[end] == inv[text[start-1]] or text[end] == ':'):
        end = start       

    if start == end:
        cnt = {k:0 for k in post}
        for i in range(start-1, -1, -1):
            c = text[i]
            if c in cnt:
                cnt[c] += 1
            if text[i] in pre:
                if cnt[inv[c]]:
                    cnt[inv[c]] -= 1
                elif pre[c] == -1:
                    pre[c] = i
        inv = {v:k for k,v in inv.items()}
        cnt = {k:0 for k in pre}
        for i in range(end, len(text)):
            c = text[i]
            if c in cnt:
                cnt[c] += 1
            if text[i] in post:
                if cnt[inv[c]]:
                    cnt[inv[c]] -= 1
                elif post[c] == -1:
                    post[c] = i
        inv = {v:k for k,v in inv.items()}
        potential = []
        
        for i,j in inv.items():
            if pre[i] != -1 and post[j] != -1:
                potential += [(pre[i], post[j])]
        if not potential:
            return nothing

        a,z = max(potential, key = lambda t: t[1] - t[0])
        z += 1
        snip = text[a:z]
        weight = None
        if snip[0] == '<':
            parts = snip[1:-1].split(":",2)
            if len(parts) < 2:
                return nothing
            content = parts[0] + ":" + parts[1]
            if len(parts) == 3:
                try:
                    weight = float(parts[2])
                except:
                    return nothing
        else:
            parts = snip[1:-1].rsplit(":", 1)
            content = parts[0]
            if len(parts) == 2:
                try:
                    weight = float(parts[1])
                except:
                    return nothing
        
        if weight == None:
            weight = {'(':1.1, '[':0.9, '<':1.0}[snip[0]]

        if snip[0] != '<' and weight + inc < 0 and inc < 0:
            return nothing
    
        weight = formatFloat(weight + inc)

        bracket = snip[0]
        if bracket == '[':
            bracket = '('

        if snip[0] != '<' and weight == "1":
            text = text[:a] + content + text[z:]
            start = a
            end = start + len(content)
        else:
            text = text[:a] + bracket + content + ":" + weight + inv[bracket] + text[z:]
            start = min(start, a + len(content) + 1)
            end = start
    else:
        weight = formatFloat(1 + inc)
        text = text[:start] + "(" + text[start:end] + ":" + weight + ")" + text[end:]
        end += 1
        start = end
        

    return {"text": text, "start": start, "end": end}

class DownloadInstance(QObject):
    updated = pyqtSignal()
    finished = pyqtSignal(int)
    aborted = pyqtSignal()
    def __init__(self, id, label, reply, is_download=True, parent=None):
        super().__init__(parent)
        self._id = id
        self._label = label
        self._progress = 0
        self._error = ""
        self._eta = ""
        self._type = "Download" if is_download else "Upload"

        self._reply = reply
        if self._reply:
            self._reply.downloadProgress.connect(self.onProgress)
            self._reply.finished.connect(self.onFinished)
            self.aborted.connect(self._reply.abort)

    @pyqtProperty(str, notify=updated)
    def label(self):
        return self._label
    
    @pyqtSlot(str)
    def setLabel(self, label):
        self._label = label
        self.updated.emit()
    
    @pyqtProperty(str, notify=updated)
    def type(self):
        return self._type

    @pyqtProperty(float, notify=updated)
    def progress(self):
        return self._progress
    
    @pyqtSlot(float)
    def setProgress(self, progress):
        self._progress = progress
        self.updated.emit()

    @pyqtProperty(str, notify=updated)
    def eta(self):
        return self._eta
    
    @pyqtSlot(str)
    def setEta(self, eta):
        self._eta = eta
        self.updated.emit()
    
    @pyqtProperty(str, notify=updated)
    def error(self):
        return self._error
    
    @pyqtSlot(str)
    def setError(self, error):
        self._error = error
        self.updated.emit()

    @pyqtSlot('qint64', 'qint64')
    def onProgress(self, current, total):
        progress = (current/total) if total else 0
        if abs(progress - self._progress) > 0.01:
            self.setProgress(progress)
            
    @pyqtSlot()
    def onFinished(self):
        if self._reply.error() != QNetworkReply.NetworkError.NoError:
            self._error = self._reply.errorString()

        self.updated.emit()
        self.finished.emit(self._id)

    @pyqtSlot()
    def doFinish(self):
        self.updated.emit()
        self.finished.emit(self._id)

    @pyqtSlot()
    def doCancel(self):
        self.aborted.emit()

class DownloadManager(QObject):
    updated = pyqtSignal()
    started = pyqtSignal(DownloadInstance)
    finished = pyqtSignal(DownloadInstance)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.gui = parent
        self._network = QNetworkAccessManager(self)
        self._id = 0
        self._downloads = {}
        self._finished = {}
        self._mapping = {}

        self.gui.response.connect(self.onBackendResponse)
        self.gui.reset.connect(self.onBackendReset)

    @pyqtProperty(list, notify=updated)
    def downloads(self):
        return [self._downloads[i] for i in sorted(list(self._downloads.keys()), reverse=True)]
    
    @pyqtProperty(list, notify=updated)
    def allDownloads(self):
        keys = sorted(list(self._downloads.keys()) + list(self._finished.keys()), reverse=True)
        out = []
        for k in keys:
            if k in self._downloads:
                out += [self._downloads[k]]
            else:
                out += [self._finished[k]]
        return out

    @pyqtSlot(str, QUrl, result=int)
    def download(self, label, url):
        reply = self._network.get(QNetworkRequest(url))
        self._id += 1
        id = self._id

        instance = DownloadInstance(id, label, reply)
        self._downloads[id] = instance
        instance.finished.connect(self.onFinished)
        
        self.updated.emit()
        self.started.emit(instance)

        return id
    
    @pyqtSlot(str, int, bool, result=int)
    def create(self, label, net_id, is_download):
        self._id += 1
        id = self._id

        instance = DownloadInstance(id, label, None, is_download)
        self._downloads[id] = instance
        self._mapping[net_id] = id
        instance.finished.connect(self.onFinished)

        self.updated.emit()
        self.started.emit(instance)

        return id

    @pyqtSlot(int)
    def onFinished(self, id):
        if not id in self._downloads:
            return
        
        instance = self._downloads[id]
        del self._downloads[id]

        self.finished.emit(instance)
        
        instance._reply = None
        instance.setProgress(1)
        instance.setEta("")
        self._finished[id] = instance

        self.updated.emit()

    @pyqtSlot(int, object)
    def onBackendResponse(self, id, response):
        if not response["type"] == "download":
            return
        data = response["data"]
        
        if not id in self._mapping:
            return
        net_id = self._mapping[id]
        if not net_id in self._downloads:
            return
        instance = self._downloads[net_id]

        if data["status"] == "started":
            instance.setLabel(data["label"])
        if data["status"] == "success":
            if "label" in data:
                instance.setLabel(data["label"])
            instance.doFinish()
            self.gui.refreshModels()
        if data["status"] == "error":
            instance.setError(data["message"])
            self.gui.setError("Downloading", data["message"], data["trace"])
            instance.doFinish()
        if data["status"] == "progress":
            instance.setProgress(data["progress"])
            
            if data["eta"]:
                minutes = int(data["eta"] // 60)
                seconds = int(data["eta"]) % 60
                instance.setEta(f"{minutes:02d}:{seconds:02d}")
            else:
                instance.setEta("")

    @pyqtSlot(int)
    def onBackendReset(self, id):
        if not id == -1:
            return
        for id in list(self._mapping.keys()):
            net_id = self._mapping[id]
            del self._mapping[id]
            if net_id in self._downloads:
                del self._downloads[net_id]
        self.updated.emit()

SUGGESTION_BLOCK_REGEX = lambda spaces: r'(?=\n|,|(?<!lora|rnet):|\||\[|\]|\(|\)'+ ('|\s)' if spaces else r')')
SUGGESTION_SOURCES = ["Model", "UNET", "VAE", "CLIP", "LoRA", "HN", "TI", "Wild", "Vocab", "Keyword"]

class SuggestionManager(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent

        self._sources = {k:False for k in SUGGESTION_SOURCES}

        self._models = []
        self._model_details = {}

        self._vocab = {}
        self._dictionary = {}
        self._dictionary_details = {}

        self._keywords = []
        
        self._results = []

        self.gui.optionsUpdated.connect(self.update)

    @pyqtProperty(list, notify=updated)
    def results(self):
        return self._results
    
    @pyqtSlot()
    def setPromptSources(self):
        self._sources = {k: False for k in SUGGESTION_SOURCES}
        for k in {"LoRA", "HN", "TI", "Wild", "Vocab"}:
            self._sources[k] = True
        self.update()
    
    @pyqtSlot(str)
    def setSource(self, source):
        if source == "Prompt":
            self.setPromptSources()
        else:
            self._sources = {k: False for k in SUGGESTION_SOURCES}
            self._sources[source] = True
            self.update()

    @pyqtSlot(list)
    def setKeywords(self, keywords):
        self._keywords = keywords

    @pyqtSlot()
    def update(self):
        self.updateCollection()
        self.updateVocab()
        self.updated.emit()
    
    def suggestionBlocks(self, text, pos):
        spaces = False

        blank = lambda m: '#' * len(m.group())
        safe = re.sub(r'__.+?__|<.+?>', blank, text)
        safe_blocks = re.split(SUGGESTION_BLOCK_REGEX(spaces), safe)

        blocks = []
        i = 0
        for b in safe_blocks:
            blocks += [text[i:i+len(b)]]
            i += len(b)

        i = 0
        before, after = "", ""
        for block in blocks:
            if pos <= i + len(block):
                before, after = block[:pos-i], block[pos-i:]
                break
            i += len(block)
        if before and before[0] in "\n,:|[]()":
            before = before[1:]
        return before, after

    def beforePos(self, text, pos):
        before, _ = self.suggestionBlocks(text, pos)

        while before and before[0] in "\n\t, ":
            before = before[1:]

        return before, pos-len(before)
    
    def afterPos(self, text, pos):
        _, after = self.suggestionBlocks(text, pos)

        if after:
            after = after.split("<",1)[0]

        return after, pos+len(after)
    
    def getSuggestions(self, text, onlyModels):
        text = text.lower().strip()
        if not text:
            return {}
        staging = {}

        for p,_ in self._models:
            pl = p.lower()
            dl = self.display(p).lower()
            if pl == text or dl == text:
                return {}
            if text in pl or text in dl:
                i = 1 - (len(text)/len(pl))
            else:
                continue
            staging[p] = i
        
        if onlyModels:
            return staging
        
        for t in self._dictionary:
            tl = t.lower()

            if tl == text:
                continue

            i = -1
            try:
                i = tl.index(text)
            except:
                pass

            if i == 0:
                i = 1 - (len(text.split()[0])/len(tl.split()[0]))
            elif i > 0:
                i = 1 - (len(text)/len(tl))
            else:
                continue
            staging[t] = i

        return staging

    @pyqtSlot(str, int, bool)
    def updateSuggestions(self, text, pos, onlyModels):
        self._results = []

        sensitivity = self.gui.config.get("autocomplete")

        before, _ = self.beforePos(text, pos)
        if before and sensitivity and len(before) >= sensitivity:
            staging = self.getSuggestions(before.lower(), onlyModels)
            if staging:
                key = lambda k: (staging[k], self._dictionary[k] if k in self._dictionary else 0)
                self._results = sorted(staging.keys(), key=key)
                if len(self._results) > 10:
                    self._results = self._results[:10]

        self.updated.emit()

    @pyqtSlot(str, result=str)
    def detail(self, text):
        if text in self._model_details:
            return self._model_details[text]
        if text in self._dictionary_details:
            return self._dictionary_details[text]
        return ""
    
    @pyqtSlot(str, result=str)
    def display(self, text):
        if text in self._model_details:
            detail = self._model_details[text]
            if detail == "LoRA":
                return f"<lora:{text}>"
            if detail == "HN":
                return f"<hypernet:{text}>"
            if detail == "Wild":
                return f"__{text}__"
        return text
    
    @pyqtSlot(str, int, result=str)
    def completion(self, text, start):
        if not text:
            return text
        if text in self._model_details:
            return self.display(text)
        return text

    @pyqtSlot(str, result=QColor)
    def color(self, text):
        if text in self._model_details:
            return {
                "TI": QColor("#ffd893"),
                "LoRA": QColor("#f9c7ff"),
                "HN": QColor("#c7fff6"),
                "Wild": QColor("#c7ffd2")
            }.get(self._model_details[text], QColor("#cccccc"))
        return QColor("#cccccc")

    @pyqtSlot(str, int, result=int)
    def start(self, text, pos):
        text, start = self.beforePos(text, pos)
        return start
    
    @pyqtSlot(str, int, result=int)
    def end(self, text, pos):
        text, end = self.afterPos(text, pos)
        return end
    
    @pyqtSlot(str, int, result=bool)
    def replace(self, text, pos):
        text, _ = self.beforePos(text, pos)
        return len(text) > 1
    
    @pyqtSlot()
    def updateCollection(self):
        self._models = []
        for t in {"UNET", "VAE", "CLIP", "LoRA", "TI", "HN"}:
            if self._sources[t] and t in self.gui._options:
                self._models += [(self.gui.modelName(n), t) for n in self.gui._options[t]]

        if self._sources["Wild"]:
            self._models += [(n, "Wild") for n in self.gui.wildcards._wildcards.keys()]
        
        if self._sources["Model"] and "UNET" in self.gui._options:
            models = []
            for n in self.gui._options["UNET"]:
                if n in self.gui._options["VAE"] and n in self.gui._options["CLIP"]:
                    models += [n]
            self._models += [(self.gui.modelName(n), "Model") for n in models]
        
        self._model_details = {k:v for k,v in self._models}
    
    @pyqtSlot()
    def updateVocab(self):
        self._dictionary = {}
        self._dictionary_details = {}

        if self._sources["Vocab"]:
            vocab = self.gui.config.get("vocab", [])
            
            self._vocab = {k:v for k,v in self._vocab.items() if k in vocab}
            for k in vocab:
                if not k in self._vocab:
                    p = k
                    if not os.path.isabs(p):
                        p = os.path.join(self.gui.modelDirectory(), k)
                    if os.path.exists(p):
                        with open(p, "r", encoding="utf-8") as f:
                            self._vocab[k] = f.readlines()
                    else:
                        self.vocabRemove(k)
            
            for k in self._vocab:
                total = len(self._vocab[k])
                for i, line in enumerate(self._vocab[k]):
                    line = line.strip()
                    tag, order = line, int(((i+1)/total)*1000000)
                    if "," in line:
                        tag, deco = line.split(",",1)[0].strip(), line.rsplit(",",1)[-1].strip()
                        self._dictionary_details[tag] = deco
                    self._dictionary[tag] = order
        
        if self._sources["Keyword"]:
            total = len(self._keywords)
            for i, entry in enumerate(self._keywords):
                order = int(((i+1)/total)*1000000)
                self._dictionary[entry] = order

    @pyqtSlot(str)
    def vocabAdd(self, file):
        vocab = self.gui.config.get("vocab", []) + [file]
        self.gui.config.set("vocab", vocab)
        self.updateVocab()
    
    @pyqtSlot(str)
    def vocabRemove(self, file):
        vocab = [v for v in self.gui.config.get("vocab", []) if not v == file]
        self.gui.config.set("vocab", vocab)
        self.updateVocab()

def format_float(x):
    return f"{x:.4f}".rstrip('0').rstrip('.')

def expandRanges(input, mode):
    import numpy as np

    brackets = {"[":"]", "(":")"}
    pattern = re.compile(r"([+\-\d\.]+)-([+\-\d\.]+)((?:\(|\[)([+\-\d\.]+)(?:\)|\]))")

    while m := pattern.search(input):
        p = list(input)
        s,e = m.span(0)

        start = m.group(1)
        end = m.group(2)
        specifier = m.group(3)
        interval = m.group(4)

        if brackets[specifier[0]] != specifier[-1]:
            return input

        try:
            if mode == "int":
                start, end = int(start), int(end)
            else:
                start, end = float(start), float(end)

            if specifier[0] == "[":
                interval = int(interval)
            else:
                interval = float(interval)

            if not interval:
                return input

            if specifier[0] == "[":
                values = np.linspace(start,end,interval)
            else:
                values = [float(v) for v in np.arange(start,end,interval)] + [end]
            
            values = [str(int(v)) if mode == "int" else format_float(v) for v in values]
            result = []
            for v in values:
                if not v in result:
                    result += [v]
            
            p[s:e] = ", ".join(result)
            input = ''.join(p)
        except:
            return input

    return input

GRID_TYPES = {
    "None":"",
    "Replace":"prompt",
    "Steps":"int",
    "Scale":"float",
    "Seed":"int",
    "Sampler":"options",
    "Strength":"float",
    "Upscaler":"options",
    "Model":"options",
    "UNET":"options",
    "CLIP":"options",
    "VAE":"options",
    "CLIP Skip":"int",
    "Eta":"float",
    "ToME Ratio":"float",
    "CFG Rescale":"float",
    "Alpha":"float",
    "CLIP Alpha":"float",
    "Rank":"int",
    "Block": "options",
    "Model A":"options",
    "Model B":"options",
    "Model C":"options"
}

GRID_OPTIONS = {
    "Sampler":"true_samplers",
    "Upscaler":"hr_upscalers",
    "Model":"models",
    "UNET":"UNETs",
    "CLIP":"CLIPs",
    "VAE":"VAEs",
    "Model A":"models",
    "Model B":"models",
    "Model C":"models",
}

GRID_ADV_OPTIONS = {"ToME Ratio", "CFG Rescale"}
GRID_MERGE_OPTIONS = {"Alpha", "CLIP Alpha", "VAE Source", "Rank", "Model A", "Model B", "Model C", "Block"}
GRID_MODEL_OPTIONS = {"Model", "UNET", "VAE", "CLIP", "Upscaler", "Model A", "Model B", "Model C"}

MERGE_BLOCKS_4 = ["DOWN0","DOWN1","DOWN2","DOWN3","MID","UP0","UP1","UP2","UP3"]
MERGE_BLOCKS_12 = ["IN00","IN01","IN02","IN03","IN04","IN05","IN06","IN07","IN08","IN09","IN10","IN11", "M00", "OUT00","OUT01","OUT02","OUT03","OUT04","OUT05","OUT06","OUT07","OUT08","OUT09","OUT10","OUT11"]

class GridManager(QObject):
    suggestionsUpdated = pyqtSignal()
    openingGrid = pyqtSignal()

    def __init__(self, parameters, manager, parent):
        super().__init__(parent)
        self.gui = parent.gui
        self.parameters = parameters
        self.manager = manager

        self.grid_x_suggestions = SuggestionManager(self.gui)
        self.grid_y_suggestions = SuggestionManager(self.gui)

    def buildAxis(self, type, input, match):
        if type == "None":
            return [""], [{}]
        mode = self.gridTypeMode(type)

        input = expandRanges(input, mode)
        match = match.strip()
        inputs = input.split(",")
        values = []
        labels = []
        key = type.lower().replace(" ", "_")
        prefix = type

        if mode == "int":
            inputs = [int(v.strip()) for v in inputs]
        elif mode == "float":
            inputs = [float(v.strip()) for v in inputs]
        elif mode == "options":
            if type == "Block":
                prefix = ""
                opts = self.gridTypeOptions("Block")
                if inputs[0] == "4 Block":
                    inputs = MERGE_BLOCKS_4
                if inputs[0] == "12 Block":
                    inputs = MERGE_BLOCKS_12
            else:
                opts = self.parameters._values.get(GRID_OPTIONS[type], [])

            mapping = {o.lower():o for o in opts}
            if type in GRID_MODEL_OPTIONS:
                mapping = {self.gui.modelName(o).lower():o for o in opts}

            inputs = [v.strip().lower() for v in inputs]
            inputs = [mapping[v] for v in inputs if v]
            names = [self.gui.modelName(v) for v in inputs]

            if type == "Model":
                prefix = ""
                values = [{"UNET":v, "CLIP":v, "VAE":v} for v in inputs]
            if type == "Upscaler":
                values = [{"img2img_upscaler":v, "hr_upscaler":v, "VAE":v} for v in inputs]
            if type == "Sampler":
                prefix = ""
                values = [{"true_sampler":v} for v in inputs]

            labels = [f"{type}: {v}" if prefix else str(v) for v in names]
        if type == "Replace":
            if "\n" in input:
                inputs = [v for v in input.split("\n")]
            inputs = [v.strip() for v in inputs]
            labels = [f'"{v}"' for v in inputs]
            values = [{"replace":(match, v)} for v in inputs]
        if type in GRID_MERGE_OPTIONS:
            values = [{"modify":{key:v}} for v in inputs]
        if not labels:
            labels = [f"{type}: {v}" if prefix else str(v) for v in inputs]
        if not values:
            values = [{key:v} for v in inputs]
        
        return labels, values

    @pyqtSlot(str, str, str, str, str, str)
    def generateGrid(self, x_type, x_value, x_match, y_type, y_value, y_match):
        try:
            x_axis = self.buildAxis(x_type, x_value, x_match)
        except:
            self.gui.setError("Parsing", "Invalid X axis values", "")
            return

        try:
            y_axis = self.buildAxis(y_type, y_value, y_match)
        except:
            self.gui.setError("Parsing", "Invalid Y axis values", "")
            return

        grid = [x_axis, y_axis]
        
        inputs = []
        if hasattr(self.parent(), "_inputs"):
            inputs = self.parent()._inputs

        self.manager.cancelRequest()
        self.manager.buildGridRequests(self.parameters, inputs, grid)
        self.manager.makeRequest()

    @pyqtSlot()
    def openGrid(self):
        self.openingGrid.emit()

    @pyqtSlot(result=list)
    def gridTypes(self):
        types = list(GRID_TYPES.keys())
        if not self.gui.config.get("advanced"):
            types = [t for t in types if not t in GRID_ADV_OPTIONS]
        if not self.parent().name == "Merge":
            types = [t for t in types if not t in GRID_MERGE_OPTIONS]
        return types
    
    @pyqtSlot(str, result=str)
    def gridTypeMode(self, type):
        return GRID_TYPES[type]

    @pyqtSlot(str, result=list)
    def gridTypeOptions(self, type):
        if type in GRID_OPTIONS:
            opts = self.parameters._values.get(GRID_OPTIONS[type])
            
            if type in GRID_MODEL_OPTIONS:
                opts = [self.gui.modelName(o) for o in opts]

            return opts
        if type == "Block":
            return MERGE_BLOCKS_4 + MERGE_BLOCKS_12 + ["4 Block", "12 Block", "UP", "DOWN", "IN", "OUT"]
        return []
    
    @pyqtSlot(str, str, result=bool)
    def gridValidate(self, type, value):
        if not type or not value.strip():
            return True
        
        mode = GRID_TYPES[type]
        if not mode:
            return True
        
        value = expandRanges(value, mode)
        values = [v.strip() for v in value.split(",") if v.strip()]
        
        if mode == "int":
            try:
                values = [int(v) for v in values]
            except:
                return False
        elif mode == "float":
            try:
                values = [float(v) for v in values]
            except:
                return False
        elif mode == "options":
            options = [o.lower() for o in self.gridTypeOptions(type)]
            if not options:
                return True
            for v in values:
                if not v.lower() in options:
                    return False
        
        return True
    
    @pyqtProperty(SuggestionManager, notify=suggestionsUpdated)
    def gridXSuggestions(self):
        return self.grid_x_suggestions
    
    @pyqtProperty(SuggestionManager, notify=suggestionsUpdated)
    def gridYSuggestions(self):
        return self.grid_y_suggestions
    
    @pyqtSlot(str, SuggestionManager, SyntaxManager)
    def gridConfigureRow(self, type, suggestions, highlighter):
        if not type in GRID_TYPES:
            return
        
        mode = GRID_TYPES[type]

        if mode == "prompt":
            suggestions.setSource("Prompt")
            highlighter.setMode("Prompt")
        elif mode == "int":
            suggestions.setSource("")
            highlighter.setMode("Integer")
        elif mode == "float":
            suggestions.setSource("")
            highlighter.setMode("Float")
        
        if mode != "options":
            return
        
        keywords = self.gridTypeOptions(type)

        suggestions.setKeywords(keywords)
        highlighter.setKeywords(keywords)
        suggestions.setSource("Keyword")
        highlighter.setMode("Keyword")

def registerTypes():
    qmlRegisterType(ImageDisplay, "gui", 1, 0, "ImageDisplay")
    qmlRegisterType(FocusReleaser, "gui", 1, 0, "FocusReleaser")
    qmlRegisterType(DropArea, "gui", 1, 0, "AdvancedDropArea")
    qmlRegisterType(MimeData, "gui", 1, 0, "MimeData")
    qmlRegisterUncreatableType(DownloadInstance, "gui", 1, 0, "DownloadInstance", "Not a QML type")
    qmlRegisterUncreatableType(DownloadManager, "gui", 1, 0, "DownloadManager", "Not a QML type")
    qmlRegisterUncreatableType(SuggestionManager, "gui", 1, 0, "SuggestionManager", "Not a QML type")
    qmlRegisterUncreatableType(SyntaxManager, "gui", 1, 0, "SyntaxManager", "Not a QML type")
    qmlRegisterUncreatableType(GridManager, "gui", 1, 0, "GridManager", "Not a QML type")