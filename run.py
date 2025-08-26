import uuid
import yaml
from prov.model import ProvDocument
from prov.dot import prov_to_dot
import argparse

IDENTIFIER = "yProv4WFsLite"

class ProvWorkflowManager:
    def __init__(self):
        self.doc = ProvDocument()
        self.doc.add_namespace(IDENTIFIER, IDENTIFIER)
        self.entities = {}
        self.activities = {}

    def _get_or_create_entity(self, uid, label=None):
        if not uid:
            uid = f"{IDENTIFIER}:entity-{uuid.uuid4()}"
        if uid not in self.entities:
            self.entities[uid] = self.doc.entity(uid, {"prov:label": label or uid})
        return self.entities[uid]

    def _create_activity(self, aid=None, label=None):
        if not aid:
            aid = f"activity-{uuid.uuid4()}"
        activity = self.doc.activity(aid, None, None, {"prov:label": label or aid})
        self.activities[aid] = activity
        return activity

    def load_from_yaml(self, yaml_path):
        with open(yaml_path, 'r') as f:
            workflow = yaml.safe_load(f)

        for task in workflow.get("tasks", []):
            task_id = task.get("id") or f"activity-{uuid.uuid4()}"
            task_id = IDENTIFIER + ":" + task_id
            label = task.get("label", task_id)
            inputs = [IDENTIFIER +":" + i for i in task.get("inputs", []) if i]
            outputs = [IDENTIFIER +":" + o for o in task.get("outputs", []) if o]

            activity = self._create_activity(task_id, label)

            for input_id in inputs:
                entity = self._get_or_create_entity(input_id)
                self.doc.used(activity, entity)

            for output_id in outputs:
                entity = self._get_or_create_entity(output_id)
                self.doc.wasGeneratedBy(entity, activity)
                
    def export_prov_json(self, path="workflow_prov.json"):
        with open(path, "w") as f:
            f.write(self.doc.serialize(indent=2))

    def render_graph(self, path="workflow_graph.png"):
        dot = prov_to_dot(self.doc)
        dot.write_png(path)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(
        prog='yProv4WFsLite',
        description='A simple Python tool to build W3C-PROV provenance graphs from workflow descriptions written in YAML.',)
    
    parser.add_argument('filename')
    parser.add_argument('-j', '--json')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    output_prov = args.json if args.json else "output_prov"
    if not output_prov.endswith(".json"): 
        output_prov += ".json"
    output_graph = args.output if args.output else "output_graph"
    if not output_graph.endswith(".png") and not output_graph.endswith(".jpg"): 
        output_graph += ".png"

    manager = ProvWorkflowManager()
    manager.load_from_yaml(args.filename)
    manager.export_prov_json(output_prov)
    manager.render_graph(output_graph)