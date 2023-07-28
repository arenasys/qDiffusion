import math
import os
import time
import json
import difflib

from parameters import VariantMap
import sql
from tabs.basic.basic_output import BasicOutput
from tabs.basic.basic import BasicImageWriter as ImageWriter

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread, QThreadPool
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterUncreatableType
from PyQt5.QtSql import QSqlQuery

class MergeOperation(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._merger = parent

        self._parameters = VariantMap(self, {
            "operation": "Weighted Sum",
            "operations_checkpoint": ["Weighted Sum", "Add Difference"],#, "Insert LoRA"],
            "operations_lora": ["Weighted Sum", "Add Difference"],#, "Extract LoRA"],
            "mode": "Simple",
            "modes": ["Simple", "Advanced"],
            "preset": "None",
            "presets": ["Linear", "Linear Inverted", "Smooth", "Smooth Inverted"],
            "model_a": "",
            "model_b": "",
            "model_c": "",
            "alpha": 0.5,
            "clip_alpha": 0.5,
            "rank": 32,
            "conv_rank": 16,
            "vae_source": "Model A",
            "clip_source": "Model A",
            "sources": ["Model A", "Model B", "Model C"],
            "label": "4 Block",
            "labels": ["4 Block", "12 Block"]
        })

        self._block_labels_12 = ["IN00","IN01","IN02","IN03","IN04","IN05","IN06","IN07","IN08","IN09","IN10","IN11", "M00", "OUT00","OUT01","OUT02","OUT03","OUT04","OUT05","OUT06","OUT07","OUT08","OUT09","OUT10","OUT11"]
        self._block_labels_4 = ["DOWN0","DOWN1","DOWN2","DOWN3","MID","UP0","UP1","UP2","UP3"]
        self._block_weights = VariantMap(self, {k:0.0 for k in self._block_labels_12 + self._block_labels_4})

        self.setBlockWeightPreset("Linear")

        self._parameters.updated.connect(self.parametersUpdated)

    @pyqtProperty(VariantMap, notify=updated)
    def parameters(self):
        return self._parameters
    
    def operationModelTypes(self, type, op):
        return {
            "Weighted Sum": [type, type, None],
            "Add Difference": [type, type, type],
            "Insert LoRA": ["Checkpoint", "LoRA", None],
            "Extract LoRA": ["Checkpoint", "Checkpoint", None]
        }[op]

    @pyqtSlot(str)
    def parametersUpdated(self, key):
        if key == "operation":
            self.enforceModelTypes()

    def enforceModelTypes(self):
        type = self._merger._parameters.get("type")
        operation = self._parameters.get("operation")
        model_types = self.operationModelTypes(type, operation)

        allowed_unets = self._merger.gui._options.get("UNET", [])
        allowed_loras = self._merger.gui._options.get("LoRA", [])

        if type == "Checkpoint":
            allowed_unets = self.availableResults + allowed_unets
        else:
            allowed_loras = self.availableResults + allowed_loras

        for k, t in zip(["model_a", "model_b", "model_c"], model_types):
            if not t:
                self._parameters.set(k, "")

            allowed = allowed_unets if t == "Checkpoint" else allowed_loras
            model = self._parameters.get(k)
            if model and not model in allowed:
                self._parameters.set(k, "")

        self.updated.emit()
    
    @pyqtSlot(int, result=str)
    def modelMap(self, index):
        operation = self._parameters.get("operation")
        type = self._merger._parameters.get("type")
        type = self.operationModelTypes(type, operation)[index]

        if type == "LoRA":
            type = "LoRAs"
        else:
            type = "models"

        return type

    @pyqtSlot(result=int)
    def getIndex(self):
        return self._merger._operations.index(self)

    @pyqtProperty(str, notify=updated)
    def modelAMap(self):
        return self.modelMap(0)
    
    @pyqtProperty(str, notify=updated)
    def modelBMap(self):
        return self.modelMap(1)
    
    @pyqtProperty(str, notify=updated)
    def modelCMap(self):
        return self.modelMap(2)

    @pyqtProperty(VariantMap, notify=updated)
    def blockWeights(self):
        return self._block_weights
    
    @pyqtProperty(list, notify=updated)
    def availableResults(self):
        type = self._merger._parameters.get("type")
        if type == "Checkpoint":
            type = "Model"

        try:
            index = self._merger._operations.index(self)
            if index > 0:
                return [os.path.join(f"_result_{i}", f"{type} {i}") for i in range(index)]
        except:
            pass
        return []

    @pyqtSlot(str)
    def setBlockWeightPreset(self, preset):
        for i, label in enumerate(self._block_labels_12):
            if preset == "Linear":
                value = abs((12 - i)/12)
            elif preset == "Linear Inverted":
                value = 1 - abs((12 - i)/12)
            elif preset == "Smooth":
                x = abs((12 - i)/12)
                value = (3 - 2*x) * x**2
            elif preset == "Smooth Inverted":
                x = 1 - abs((12 - i)/12)
                value = (3 - 2*x) * x**2
            else:
                continue
            value = float(f"{value:.4f}")
            self._block_weights.set(label, value)

        for i, label in enumerate(self._block_labels_4):
            if preset == "Linear":
                value = abs((4 - i)/4)
            elif preset == "Linear Inverted":
                value = 1 - abs((4 - i)/4)
            elif preset == "Smooth":
                x = abs((4 - i)/4)
                value = (3 - 2*x) * x**2
            elif preset == "Smooth Inverted":
                x = 1 - abs((4 - i)/4)
                value = (3 - 2*x) * x**2
            else:
                continue
            value = float(f"{value:.4f}")
            self._block_weights.set(label, value)
        
        if self._parameters.get("preset") != preset:
            self._parameters.set("preset", preset)

    @pyqtSlot(result=str)
    def getBlockWeightLabels(self):
        labels = self._parameters.get("label")
        if labels == "12 Block":
            return self._block_labels_12
        if labels == "4 Block":
            return self._block_labels_4

    @pyqtSlot(result=str)
    def getBlockWeightValues(self):
        outputs = []
        for label in self.getBlockWeightLabels():
            value = self._block_weights.get(label)
            outputs += [f"{value:.4f}".rstrip('0').rstrip('.')]
        return ", ".join(outputs)
    
    @pyqtSlot(str)
    def setBlockWeightValues(self, values):
        values = [v.strip() for v in values.split(",")]

        if len(values) <= 9:
            self._parameters.set("label", "4 Block")
        else:
            self._parameters.set("label", "12 Block")

        parsed_values = {}
        for i, label in enumerate(self.getBlockWeightLabels()):
            try:
                value = max(0, min(1, float(values[i])))
                value = float(f"{value:.4f}".rstrip('0').rstrip('.'))
                parsed_values[label] = value
            except:
                continue
        
        for label in parsed_values:
            self._block_weights.set(label, parsed_values[label])

    def getRecipe(self, model_type):
        important = ["operation", "mode", "model_a", "model_b", "model_c", "alpha"]
        recipe = {k:self._parameters.get(k) for k in important}

        for k in ["model_a", "model_b", "model_c"]:
            if recipe[k].startswith("_result_"):
                recipe[k] = recipe[k].split(os.path.sep)[0]
            
        if recipe["operation"] == "Weighted Sum":
            del recipe["model_c"]

        if recipe["mode"] == "Advanced":
            recipe["alpha"] = [self._block_weights.get(label) for label in self.getBlockWeightLabels()]

        if model_type == "Checkpoint":
            for k in ["vae_source", "clip_source"]:
                recipe[k] = ["Model A", "Model B", "Model C"].index(self._parameters.get(k))
        else:
            for k in ["rank", "conv_rank"]:
                recipe[k] = int(self._parameters.get(k))
            recipe["clip_alpha"] = self._parameters.get("clip_alpha")
            
        del recipe["mode"]

        return recipe

class Merger(QObject):
    updated = pyqtSignal()
    selected = pyqtSignal()
    input = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "Merge"
        self.gui = parent
        self.hidden = True
        self._ids = []
        self._mapping = {}
        self._valid = False
        self._forever = False

        self._parameters = VariantMap(self, {
            "type": "Checkpoint",
            "types": ["Checkpoint", "LoRA"],
        })

        qmlRegisterSingletonType(Merger, "gui", 1, 0, "MERGER", lambda qml, js: self)
        qmlRegisterUncreatableType(MergeOperation, "gui", 1, 0, "MergeOperation", "Not a QML type")

        self._operations = []
        self.addOperation()
        self._selectedOperationIndex = 0

        self._outputs = {}
        self._openedIndex = -1

        self.gui.result.connect(self.result)
        self.gui.reset.connect(self.reset)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE merge_outputs(id INTEGER);")
        self.conn.enableNotifications("merge_outputs")

        self._parameters.updated.connect(self.parametersUpdated)

    @pyqtProperty(VariantMap, notify=updated)
    def parameters(self):
        return self._parameters

    @pyqtSlot(str)
    def parametersUpdated(self, key):
        type = self._parameters.get("type")
        for op in self._operations:
            allowed_operations = op._parameters.get("operations_checkpoint" if type == "Checkpoint" else "operations_lora")
            if not op._parameters.get("operation") in allowed_operations:
                op._parameters.set("operation", allowed_operations[0])  
            op.enforceModelTypes()
    
    @pyqtProperty(bool, notify=updated)
    def forever(self):
        return self._forever

    @forever.setter
    def forever(self, forever):
        self._forever = forever
        self.updated.emit()

    @pyqtSlot()
    def buildRecipe(self):
        recipe = []
        model_type = self._parameters.get("type")
        for o in self._operations:
            recipe += [o.getRecipe(model_type)]
        return recipe
    
    @pyqtSlot(result=str)
    def recipeName(self, full=False):
        names = []
        for op in self.buildRecipe():
            a = self.gui.modelName(op['model_a'])
            b = self.gui.modelName(op['model_b'])
            alpha = op['alpha']
            if op['operation'] == "Weighted Sum":
                if type(alpha) == float:
                    names += [f"{alpha:.2f}({a})+{1-alpha:.2f}({b})"]
                else:
                    weights = ""
                    if full:
                        weights = f"[{','.join([str(a) for a in alpha])}]"
                    names += [f"%({a})+%({b}){weights}"]
            elif op['operation'] == "Add Difference":
                c = self.gui.modelName(op['model_c'])
                if type(alpha) == float:
                    names += [f"({a})+{alpha:.2f}({b}-{c})"]
                else:
                    names += [f"({a})+%({b}-{c})"]
        for i in range(len(names)):
            match = f"_result_{i}"
            for k in range(len(names)):
                names[k] = names[k].replace(match, names[i])
        return names[-1]

    @pyqtSlot(result=QUrl)
    def recipeJSONName(self):
        return QUrl.fromLocalFile(os.path.join(os.getcwd(), self.recipeName() + ".json"))
    
    @pyqtSlot(QUrl)
    def saveRecipe(self, file):
        file = file.toLocalFile()
        recipe = self.buildRecipe()

        for i in range(len(recipe)):
            for k in ["model_a", "model_b", "model_c"]:
                if k in recipe[i]:
                    recipe[i][k] = self.gui.modelName(recipe[i][k])

        recipe = {
            "type": self._parameters.get("type"),
            "operations": recipe
        }

        try:
            with open(file, 'w', encoding="utf-8") as f:
                json.dump(recipe, f, indent=4)
        except Exception:
            return
        
    @pyqtSlot(QUrl)
    def loadRecipe(self, file):
        file = file.toLocalFile()
        recipe = []
        try:
            with open(file, 'r', encoding="utf-8") as f:
                recipe = json.load(f)
        except:
            return

        if type(recipe) == list:
            model_type = "Checkpoint"
            operations = recipe
        else:
            model_type = recipe["type"]
            operations = recipe["operations"]

        self._parameters.set("type", model_type)
        
        models = self.gui._options.get("UNET" if model_type == "Checkpoint" else "LoRA", [])

        self._operations = []
        for op in operations:
            operation = MergeOperation(self)
            try:
                operation._parameters.set("operation", op["operation"])
                for k in ["model_a", "model_b", "model_c"]:
                    if k in op:
                        model = op[k]
                        if model.startswith("_result_"):
                            index = int(model.split("_")[-1])
                            model = os.path.join(f"_result_{index}", f"Model {index}")
                        else:
                            model = self.gui.closestModel(model, models)
                        operation._parameters.set(k, model)
                sources = operation._parameters.get("sources")
                for k in ["vae_source", "clip_source"]:
                    source = sources[0]
                    if k in op:
                        source = sources[op[k]]
                    operation._parameters.set(k, source)
                alpha = op["alpha"]
                if type(alpha) == list:
                    operation._parameters.set("mode", "Advanced")
                    operation.setBlockWeightValues(",".join([str(a) for a in alpha]))
                else:
                    operation._parameters.set("alpha", alpha)
            except Exception as e:
                print(e)
                pass
            operation._parameters.updated.connect(self.check)
            self._operations += [operation]
        self.check()
        self._selectedOperationIndex = 0
        self.selected.emit()

    @pyqtProperty(bool, notify=updated)
    def valid(self):
        return self._valid

    @pyqtProperty(list, notify=updated)
    def operations(self):
        return self._operations
    
    @pyqtProperty(int, notify=selected)
    def selectedOperationIndex(self):
        return self._selectedOperationIndex
    
    @selectedOperationIndex.setter
    def selectedOperationIndex(self, index):
        if index != self._selectedOperationIndex:
            self._selectedOperationIndex = index
            self.selected.emit()

    @pyqtProperty(MergeOperation, notify=selected)
    def selectedOperation(self):
        return self._operations[self._selectedOperationIndex]

    @pyqtSlot()
    def addOperation(self):
        op = MergeOperation(self)
        op._parameters.updated.connect(self.check)
        self._operations += [op]
        self.check()

    @pyqtSlot()
    def deleteOperation(self):
        self._operations.remove(self.selectedOperation)
        self._selectedOperationIndex = max(0, self._selectedOperationIndex - 1)

        if len(self._operations) == 0:
            self.addOperation()
        else:
            self.check()

        for op in self._operations:
            op.enforceModelTypes()

        self.selected.emit()
    
    @pyqtSlot()
    def generate(self):
        for id in list(self._outputs.keys()):
            if not self._outputs[id]._ready:
                if self._openedIndex == id:
                    self.right()
                self.deleteOutput(id)
        self._ids = []
        self._mapping = {}

        basic = [t for t in self.gui.tabs if t.name == "Generate"][0]
        request = basic._parameters.buildRequest(1, [], [], [], [])

        model_type = self._parameters.get("type")
        operations = self.buildRecipe()
        name = self.recipeName()

        if model_type == "Checkpoint":
            for k in ["unet", "clip", "vae", "model"]:
                if k in request["data"]:
                    del request["data"][k]
        
        if model_type == "Checkpoint":
            request["data"]["merge_checkpoint_recipe"] = operations
        elif model_type == "LoRA":
            request["data"]["merge_lora_recipe"] = operations
        request["data"]["merge_name"] = name

        self._ids += [self.gui.makeRequest(request)]
    
    @pyqtSlot(str)
    def buildModel(self, filename):
        basic = [t for t in self.gui.tabs if t.name == "Generate"][0]
        device = basic._parameters._values.get("device")

        model_type = self._parameters.get("type")
        operations = self.buildRecipe()
        name = self.recipeName()

        if model_type == "Checkpoint":
            request = {"type":"manage", "data":{"operation": "build", "merge_checkpoint_recipe":operations, "merge_name": name, "file":filename+".safetensors", "device_name": device}}
            if basic._parameters._values.get("network_mode") == "Static":
                request["data"]["prompt"] = basic._parameters.buildPrompts(1)
        elif model_type == "LoRA":
            request = {"type":"manage", "data":{"operation": "build_lora", "merge_lora_recipe":operations, "merge_name": name, "file":filename+".safetensors", "device_name": device}}

        self.gui.makeRequest(request)

    @pyqtSlot()
    def cancel(self):
        if self._ids:
            self.gui.cancelRequest(self._ids.pop())
            self.updated.emit()

    @pyqtSlot(int, str)
    def result(self, id, name):
        if not id in self._ids:
            return
        
        results = self.gui._results[id]

        if not id in self._mapping:
            self._mapping[id] = (time.time_ns() // 1000000) % (2**31 - 1)

        out = self._mapping[id]
        if not out in self._outputs:
            sticky = self.isSticky()
            empty = len(self._outputs) == 0
            if "result" in results:
                initial = results["result"]
            elif "preview" in results:
                initial = results["preview"]
            else:
                return
            for i in range(len(initial)-1, -1, -1):
                self._outputs[out] = BasicOutput(self, initial[i])
                q = QSqlQuery(self.conn.db)
                q.prepare("INSERT INTO merge_outputs(id) VALUES (:id);")
                q.bindValue(":id", out)
                self.conn.doQuery(q)

                if not self._openedIndex in self._outputs:
                    self._openedIndex = out
                    self.updated.emit()
                if sticky:
                    self.stick()

                out += 1

        if name == "preview":
            previews = results["preview"]
            out = self._mapping[id]
            for i in range(len(previews)-1, -1, -1):
                self._outputs[out].setPreview(previews[i])
                out += 1

        if name == "result":
            sticky = self.isSticky()
            image = results["result"][0]
            metadata = results.get("metadata", [None])[0]
            out = self._mapping[id]
            if not self._outputs[out]._ready:
                writer = ImageWriter(image, metadata, self.gui.outputDirectory(), "merge", None)
                file = writer.file
                QThreadPool.globalInstance().start(writer)
                self._outputs[out].setResult(image, metadata, file)
            if sticky:
                self.stick()
        
            if self._forever:
                self.generate()
            
            self.updated.emit()

    @pyqtSlot(int)
    def reset(self, id):
        if id in self._mapping:
            out = self._mapping[id]
            if self._openedIndex == out:
                self.right()
            self.deleteOutput(self._mapping[id])
        self._ids = []

    @pyqtSlot(int, result=int)
    def outputIDToIndex(self, id):
        outputs = sorted(list(self._outputs.keys()), reverse=True)
        for i, p in enumerate(outputs):
            if p == id:
                return i
        return -1
    
    @pyqtSlot(int, result=int)
    def outputIndexToID(self, idx):
        outputs = sorted(list(self._outputs.keys()), reverse=True)
        if idx >= 0 and idx < len(outputs):
            return outputs[idx]
        return -1
    
    def isSticky(self):
        idx = self.outputIDToIndex(self._openedIndex)
        if idx == 0:
            return True
        if idx == 1 and not self._outputs[self.outputIndexToID(0)].ready:
            return True
        return False

    @pyqtSlot()
    def stick(self):
        index = self.outputIndexToID(0)
        if index in self._outputs and self._outputs[index]._ready:
            self._openedIndex = index
            self.updated.emit()

    @pyqtSlot()
    def right(self):
        if self._openedIndex == -1:
            return
        
        idx = self.outputIDToIndex(self._openedIndex) + 1
        id = self.outputIndexToID(idx)
        if id in self._outputs:
            self._openedIndex = id
            self.updated.emit()
            self.input.emit()

    @pyqtSlot()
    def left(self):
        if self._openedIndex == -1:
            return
        
        idx = self.outputIDToIndex(self._openedIndex) - 1
        id = self.outputIndexToID(idx)
        if id in self._outputs:
            self._openedIndex = id
            self.updated.emit()
            self.input.emit()

    @pyqtSlot(int, result=BasicOutput)
    def outputs(self, id):
        if id in self._outputs:
            return self._outputs[id]
        
    @pyqtProperty(int, notify=updated)
    def openedIndex(self):
        return self._openedIndex
    
    @openedIndex.setter
    def openedIndex(self, index):
        self._openedIndex = index
        self.updated.emit()

    @pyqtSlot(int)
    def deleteOutput(self, id):
        if not id in self._outputs:
            return
        del self._outputs[id]
        self.updated.emit()
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM merge_outputs WHERE id = :id;")
        q.bindValue(":id", id)
        self.conn.doQuery(q)
    
    @pyqtSlot(int)
    def deleteOutputAfter(self, id):
        for i in list(self._outputs.keys()):
            if i < id:
                del self._outputs[i]
        
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM merge_outputs WHERE id < :idx;")
        q.bindValue(":idx", id)
        self.conn.doQuery(q)
        self.updated.emit()

    @pyqtSlot()
    def check(self):
        self._valid = True
        for op in self.buildRecipe():
            for k in ["model_a", "model_b", "model_c"]:
                if k in op and not op[k]:
                    self._valid = False
        self.updated.emit()
     
    @pyqtSlot(str, result=str)
    def closestModel(self, name, models):
        if not models:
            return ''
        
        name = name.lower()
        best = models[0]
        score = 0

        for m in models:
            m_name = self.gui.modelName(m).lower()
            m_score = difflib.SequenceMatcher(a=m_name, b=name).ratio()
            if m_score > score:
                best = m
                score = m_score
        
        return best