import math
import os
import time
import json
import difflib

import parameters
from parameters import VariantMap
import sql
import misc
from tabs.basic.basic_output import BasicOutput
import manager

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread, QThreadPool
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterUncreatableType
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import QImage

class MergeOperation(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._merger = parent

        self._parameters = VariantMap(self, {
            "operation": "Weighted Sum",
            "operations_checkpoint": ["Weighted Sum", "Add Difference", "Insert LoRA"],
            "operations_lora": ["Weighted Sum", "Add Difference", "Modify LoRA", "Combine LoRA", "Extract LoRA"],
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
            "vae_source": "Model A",
            "sources": ["Model A", "Model B", "Model C"],
            "label": "4 Block",
            "labels": ["4 Block", "12 Block"]
        })

        self._block_labels_12 = misc.MERGE_BLOCKS_12
        self._block_labels_4 = misc.MERGE_BLOCKS_4
        self._block_weights = VariantMap(self, {k:0.0 for k in self._block_labels_12 + self._block_labels_4})

        self.setBlockWeightPreset("Linear")

        self._parameters.updated.connect(self.parametersUpdated)

    @pyqtProperty(VariantMap, notify=updated)
    def parameters(self):
        return self._parameters

    @pyqtProperty(int, notify=updated)
    def modelCount(self):
        type = self._merger._parameters.get("type")
        operation = self._parameters.get("operation")
        types = self.operationModelTypes(type, operation)
        return len([t for t in types if t])
    
    @pyqtProperty(bool, notify=updated)
    def hasAlpha(self):
        operation = self._parameters.get("operation")
        return not operation in {"Extract LoRA", "Combine LoRA"}
    
    @pyqtProperty(bool, notify=updated)
    def limitAlpha(self):
        type = self._merger._parameters.get("type")
        return type == "Checkpoint"
    
    def operationModelTypes(self, type, op):
        return {
            "Weighted Sum": [type, type, None],
            "Add Difference": [type, type, type],
            "Insert LoRA": ["Checkpoint", "LoRA", None],
            "Extract LoRA": ["Checkpoint", "Checkpoint", None],
            "Modify LoRA": ["LoRA", None, None],
            "Combine LoRA": ["LoRA", "LoRA", None],
        }[op]

    @pyqtSlot(str)
    def parametersUpdated(self, key):
        if key == "operation":
            self.enforceModelTypes()

            operation = self._parameters.get("operation")
            default_alpha = 0.5
            if operation in {"Insert LoRA", "Modify LoRA"}:
                default_alpha = 1.0
            self._parameters.set("alpha", default_alpha)
            self._parameters.set("clip_alpha", default_alpha)

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
        return ",".join(outputs)
    
    @pyqtSlot()
    def invertBlockWeightValues(self):
        for label in self.getBlockWeightLabels():
            value = self._block_weights.get(label)
            self._block_weights.set(label, 1.0 - value)
    
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
        important = ["operation", "mode", "model_a", "model_b", "model_c", "alpha", "clip_alpha"]
        recipe = {k:self._parameters.get(k) for k in important}

        for k in ["model_a", "model_b", "model_c"]:
            if recipe[k].startswith("_result_"):
                recipe[k] = recipe[k].split(os.path.sep)[0]
        
        model_types = self.operationModelTypes(model_type, recipe["operation"])
        if model_types[1] == None:
            del recipe["model_b"]
        if model_types[2] == None:
            del recipe["model_c"]

        if recipe["mode"] == "Advanced":
            recipe["alpha"] = [self._block_weights.get(label) for label in self.getBlockWeightLabels()]

        if model_type == "Checkpoint":
            recipe["vae_source"] = ["Model A", "Model B", "Model C"].index(self._parameters.get("vae_source"))
        else:
            rank = int(self._parameters.get("rank"))
            recipe["rank"] = rank
            recipe["conv_rank"] = max(int(rank//2), 8)
            recipe["clip_alpha"] = self._parameters.get("clip_alpha")
            
        del recipe["mode"]
        
        if not self.hasAlpha:
            for k in ["alpha", "clip_alpha"]:
                if k in recipe:
                    del recipe[k]
        
        return recipe

class Merger(QObject):
    updated = pyqtSignal()
    managersUpdated = pyqtSignal()
    operationSelected = pyqtSignal()
    outputSelected = pyqtSignal()
    
    input = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "Merge"
        self.gui = parent
        self.hidden = True
        self._outputs = {}
        self._valid = False

        self._manager = manager.RequestManager(self.gui, self.modifyRequest)
        self._forever = False

        self._parameters = VariantMap(self, {
            "type": "Checkpoint",
            "types": ["Checkpoint", "LoRA"],
            "strength": 1.0
        })

        qmlRegisterSingletonType(Merger, "gui", 1, 0, "MERGER", lambda qml, js: self)
        qmlRegisterUncreatableType(MergeOperation, "gui", 1, 0, "MergeOperation", "Not a QML type")

        self._operations = []
        self.addOperation()
        self._selected_operation_index = 0

        self._opened_index = -1

        self._grid = None

        self.gui.response.connect(self.handleResponse)
        self.gui.result.connect(self.handleResult)
        self.gui.reset.connect(self.handleReset)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE merge_outputs(id INTEGER);")
        self.conn.enableNotifications("merge_outputs")

        self._manager.result.connect(self.onResult)
        self._manager.artifact.connect(self.onArtifact)

        self._parameters.updated.connect(self.parametersUpdated)

    def getGenerateParameters(self):
        basic = [t for t in self.gui.tabs if t.name == "Generate"][0]
        return basic._parameters

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
            if op['operation'] == "Weighted Sum":
                a = self.gui.modelName(op['model_a'])
                b = self.gui.modelName(op['model_b'])
                alpha = op['alpha']
                if type(alpha) == float:
                    names += [f"{alpha:.2f}({a})+{1-alpha:.2f}({b})"]
                else:
                    weights = ""
                    if full:
                        weights = f"[{','.join([str(a) for a in alpha])}]"
                    names += [f"%({a})+%({b}){weights}"]
            elif op['operation'] == "Add Difference":
                a = self.gui.modelName(op['model_a'])
                b = self.gui.modelName(op['model_b'])
                c = self.gui.modelName(op['model_c'])
                alpha = op['alpha']
                if type(alpha) == float:
                    names += [f"({a})+{alpha:.2f}({b}-{c})"]
                else:
                    names += [f"({a})+%({b}-{c})"]
            elif op['operation'] == "Insert LoRA":
                a = self.gui.modelName(op['model_a'])
                b = self.gui.modelName(op['model_b'])
                alpha = op['alpha']
                clip_alpha = op['clip_alpha']
                if type(alpha) == float:
                    names += [f"({a})+({alpha:.2f},{clip_alpha:.2f})({b})"]
                else:
                    names += [f"({a})+(%,{clip_alpha:.2f})({b})"]
            elif op['operation'] == "Modify LoRA":
                a = self.gui.modelName(op['model_a'])
                names += [f"{a}"]
            elif op['operation'] == "Extract LoRA":
                a = self.gui.modelName(op['model_a'])
                b = self.gui.modelName(op['model_b'])
                names += [f"({a})-({b})"]
            elif op['operation'] == "Combine LoRA":
                a = self.gui.modelName(op['model_a'])
                b = self.gui.modelName(op['model_b'])
                names += [f"({a})+({b})"]
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

        if file.endswith(".json"):
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
        elif file.endswith(".png"):
            image = QImage(file)
            recipe = image.text("recipe")
            if not recipe:
                return
            recipe = json.loads(recipe)
            model_type = recipe["type"]
            operations = recipe["operations"]
            strength = recipe.get("strength", None)
            if strength != None:
                self._parameters.set("strength", strength)
        else:
            return

        self._parameters.set("type", model_type)
        
        models = {
            "Checkpoint": self.gui._options.get("UNET", []),
            "LoRA": self.gui._options.get("LoRA", [])
        }

        self._operations = []
        for op in operations:
            operation = MergeOperation(self)
            try:
                operation._parameters.set("operation", op["operation"])
                model_types = operation.operationModelTypes(model_type, op["operation"])
                for k, t in zip(["model_a", "model_b", "model_c"], model_types):
                    if k in op:
                        model = op[k]
                        if model.startswith("_result_"):
                            index = int(model.split("_")[-1])
                            label = "Model" if model_type == "Checkpoint" else "LoRA"
                            model = os.path.join(f"_result_{index}", f"{label} {index}")
                        else:
                            model = self.gui.closestModel(model, models[t])
                        operation._parameters.set(k, model)
                sources = operation._parameters.get("sources")

                vae_source = sources[0]
                if "vae_source" in op:
                    vae_source = sources[op["vae_source"]]
                operation._parameters.set("vae_source", vae_source)

                clip_alpha = op.get("clip_alpha", 1.0)
                if "clip_source" in op:
                    clip_alpha = float(op["clip_source"])
                operation._parameters.set("clip_alpha", clip_alpha)

                alpha = op["alpha"]
                if type(alpha) == list:
                    operation._parameters.set("mode", "Advanced")
                    operation.setBlockWeightValues(",".join([str(a) for a in alpha]))
                else:
                    operation._parameters.set("alpha", alpha)

                for k in ["clip_alpha", "rank", "conv_rank"]:
                    if k in op:
                        operation._parameters.set(k, op[k])
                
            except Exception as e:
                print(e)
                pass
            operation._parameters.updated.connect(self.check)
            self._operations += [operation]
        self.check()
        self._selected_operation_index = 0
        self.operationSelected.emit()

    @pyqtSlot(misc.MimeData)
    def drop(self, mimeData):
        mimeData = mimeData.mimeData
        for url in mimeData.urls():
            if url.isLocalFile():
                self.loadRecipe(url)
                break

    @pyqtProperty(bool, notify=updated)
    def valid(self):
        return self._valid

    @pyqtProperty(list, notify=updated)
    def operations(self):
        return self._operations
    
    @pyqtProperty(int, notify=operationSelected)
    def selectedOperationIndex(self):
        return self._selected_operation_index
    
    @selectedOperationIndex.setter
    def selectedOperationIndex(self, index):
        if index != self._selected_operation_index:
            self._selected_operation_index = index
            self.operationSelected.emit()

    @pyqtProperty(MergeOperation, notify=operationSelected)
    def selectedOperation(self):
        return self._operations[self._selected_operation_index]

    @pyqtSlot()
    def addOperation(self):
        op = MergeOperation(self)
        op._parameters.updated.connect(self.check)
        self._operations += [op]
        self.check()

    @pyqtSlot()
    def deleteOperation(self):
        self._operations.remove(self.selectedOperation)
        self._selected_operation_index = max(0, self._selected_operation_index - 1)

        if len(self._operations) == 0:
            self.addOperation()
        else:
            self.check()

        for op in self._operations:
            op.enforceModelTypes()

        self.operationSelected.emit()
    
    def modifyRequest(self, request, overrides=None):
        model_type = self._parameters.get("type")

        if overrides:
            op = self.selectedOperation
            backup_params = {k:v for k,v in op._parameters._map.items()}
            backup_weights = {k:v for k,v in op._block_weights._map.items()}
            for k,v in overrides.items():
                if k in op._parameters._map:
                    op._parameters._map[k] = v
            
            if "block" in overrides and op._parameters._map["mode"] == "Advanced":
                alpha = op._parameters._map["alpha"]
                block = overrides["block"]
                for k in op._block_weights._map:
                    if k.startswith(block):
                        op._block_weights._map[k] = alpha

        operations = self.buildRecipe()
        name = self.recipeName()

        if overrides:
            op._parameters._map = backup_params
            op._block_weights._map = backup_weights

        if model_type == "Checkpoint":
            for k in ["unet", "clip", "vae", "model"]:
                if k in request["data"]:
                    del request["data"][k]
        
        if model_type == "Checkpoint":
            request["data"]["merge_checkpoint_recipe"] = operations
        elif model_type == "LoRA":
            request["data"]["merge_lora_recipe"] = operations
            request["data"]["merge_lora_strength"] = self._parameters.get("strength")
        request["data"]["merge_name"] = name
        request["data"]["network_mode"] = "Dynamic"

        request["folder"] = "merge"
        
        return request

    @pyqtSlot()
    def generate(self, user=True):
        if user or not self._manager.requests:
            self._manager.buildRequests(self.getGenerateParameters(), [])
        
        self._manager.makeRequest()
        self.updated.emit()
    
    @pyqtSlot(str, bool)
    def buildModel(self, filename, prompt):
        parameters = self.getGenerateParameters()
        device = parameters._values.get("device")

        model_type = self._parameters.get("type")
        operations = self.buildRecipe()
        name = self.recipeName()

        if model_type == "Checkpoint":
            request = {"type":"manage", "data":{"operation": "build", "merge_checkpoint_recipe":operations, "merge_name": name, "file":filename+".safetensors", "device_name": device}}
            if prompt:
                request["data"]["prompt"] = parameters.buildPrompts()
        elif model_type == "LoRA":
            request = {"type":"manage", "data":{"operation": "build_lora", "merge_lora_recipe":operations, "merge_name": name, "file":filename+".safetensors", "device_name": device}}

        self.gui.makeRequest(request)

    @pyqtSlot()
    def cancel(self):
        self._manager.cancelRequest()
        self.updated.emit()

    @pyqtSlot(int, str)
    def handleResult(self, id, name):
        self._manager.handleResult(id, name)

    @pyqtSlot(int, object)
    def handleResponse(self, id, response):
        if response["type"] == "ack":
            id = response["data"]["id"]
            queue = response["data"]["queue"]
            if id in self._manager.ids and queue > 0:
                self.gui.setWaiting()

    def createOutput(self, id, image):
        self._outputs[id] = BasicOutput(self, image)
        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT INTO merge_outputs(id) VALUES (:id);")
        q.bindValue(":id", id)
        self.conn.doQuery(q)

    @pyqtSlot(int, QImage, object, str, bool)
    def onResult(self, id, image, metadata, filename, last):
        sticky = self.isSticky()

        if not id in self._outputs:
            self.createOutput(id, image)

        self._outputs[id].setResult(image, metadata, filename)

        if sticky:
            self.stick()

        if last:
            if self._forever or self._manager.requests:
                self.generate(user=False)
            else:
                self._manager.count = 0
                self.updated.emit()

    @pyqtSlot(int, QImage, str)
    def onArtifact(self, id, image, name):
        if not id in self._outputs:
            self.createOutput(id, image)
        
        if name == "preview":
            self._outputs[id].setPreview(image)
        else:
            self._outputs[id].addArtifact(name, image)

        self.updated.emit()

    @pyqtSlot(int)
    def handleReset(self, id):
        for out in list(self._outputs.keys()):
            if not self._outputs[out]._ready:
                if self._opened_index == out:
                    self.right()
                self.deleteOutput(out)

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
        idx = self.outputIDToIndex(self._opened_index)
        if idx == 0 or idx == -1:
            return True
        if idx > 0 and not self._outputs[self.outputIndexToID(idx-1)].ready:
            return True
        return False

    @pyqtSlot()
    def stick(self):
        i = max(0, self.outputIDToIndex(self._opened_index)-1)
        index = self.outputIndexToID(i)
        if index in self._outputs and self._outputs[index]._ready:
            self._opened_index = index
            self.outputSelected.emit()

    @pyqtSlot()
    def right(self):
        if self._opened_index == -1:
            return
        
        idx = self.outputIDToIndex(self._opened_index) + 1
        id = self.outputIndexToID(idx)
        if id in self._outputs:
            self._opened_index = id
            self.outputSelected.emit()
            self.input.emit()

    @pyqtSlot()
    def left(self):
        if self._opened_index == -1:
            return
        
        idx = self.outputIDToIndex(self._opened_index) - 1
        id = self.outputIndexToID(idx)
        if id in self._outputs:
            self._opened_index = id
            self.outputSelected.emit()
            self.input.emit()

    @pyqtSlot(int, result=BasicOutput)
    def outputs(self, id):
        if id in self._outputs:
            return self._outputs[id]
        
    @pyqtProperty(int, notify=outputSelected)
    def openedIndex(self):
        return self._opened_index
    
    @openedIndex.setter
    def openedIndex(self, index):
        self._opened_index = index
        self.outputSelected.emit()

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
    
    @pyqtProperty(manager.RequestManager, notify=managersUpdated)
    def manager(self):
        return self._manager

    @pyqtProperty(misc.GridManager, notify=managersUpdated)
    def grid(self):
        if not self._grid:
            self._grid = misc.GridManager(self.getGenerateParameters(), self._manager, self)
        return self._grid