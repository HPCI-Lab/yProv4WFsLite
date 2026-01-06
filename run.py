import uuid
import yaml
from prov.model import ProvDocument
from utils import custom_prov_to_dot, replace_nodes_with_images
import argparse
import os
import subprocess

IDENTIFIER = "y2Graph"

class ProvWorkflowManager:
    def __init__(self):
        self.doc = ProvDocument()
        self.doc.add_namespace(IDENTIFIER, IDENTIFIER)
        self.entities = {}
        self.activities = {}

    def _get_or_create_entity(self, uid, ents, label=None):
        if not uid:
            uid = f"{IDENTIFIER}:entity-{uuid.uuid4()}"

        if uid not in self.entities:
            self.entities[uid] = self.doc.entity(
                uid, {"prov:label": label or uid}
            )

        if ents:
            name = uid.replace(f"{IDENTIFIER}:", "")
            if name in ents:
                self.entities[uid].add_attributes(
                    {"prov:" + k: v for k, v in ents[name].items()}
                )

        return self.entities[uid]

    def _create_activity(self, aid=None, label=None, attributes=None):
        if attributes is None:
            attributes = {}
        if not aid:
            aid = f"activity-{uuid.uuid4()}"
        attributes["prov:label"] = label or aid
        activity = self.doc.activity(aid, None, None, attributes)
        self.activities[aid] = activity
        return activity

    def _create_user(self, label):
        return self.doc.agent(label)

    def load_from_yaml(self, yaml_path):
        with open(yaml_path, "r") as f:
            workflow = yaml.safe_load(f)

        entities = workflow.get("entities", {})

        for task in workflow.get("tasks", []):
            task_id = task.get("id") or f"activity-{uuid.uuid4()}"
            task_id = f"{IDENTIFIER}:{task_id}"

            label = task.get("label", task_id)
            agent = task.get("agent")
            attributes = task.get("attributes", [])

            attrs = {
                f"{IDENTIFIER}:{list(a.keys())[0]}": list(a.values())[0]
                for a in attributes
            }

            inputs = [f"{IDENTIFIER}:{i}" for i in task.get("inputs", []) if i]
            outputs = [f"{IDENTIFIER}:{o}" for o in task.get("outputs", []) if o]

            activity = self._create_activity(task_id, label, attrs)
            if agent: 
                user_id = IDENTIFIER + ":" + agent
                user = self._create_user(user_id)
                activity.wasAssociatedWith(user)

            if agent:
                user_id = f"{IDENTIFIER}:{agent}"
                user = self._create_user(user_id)
                activity.wasAssociatedWith(user)

            for input_id in inputs:
                entity = self._get_or_create_entity(input_id, entities)
                self.doc.used(activity, entity)

            for output_id in outputs:
                entity = self._get_or_create_entity(output_id, entities)
                self.doc.wasGeneratedBy(entity, activity)

    def export_prov_json(self, path):
        with open(path, "w") as f:
            f.write(self.doc.serialize(indent=2))

    def render_graph(self, path):
        dot = custom_prov_to_dot(self.doc)
        dot_str = replace_nodes_with_images(dot.to_string())

        dot_path = os.path.splitext(path)[0] + ".dot"
        with open(dot_path, "w") as f:
            f.write(dot_str)

        if path.endswith(".pdf"):
            subprocess.run(["dot", "-Tpdf", dot_path, "-o", path])
        else:
            subprocess.run(["dot", "-Tpng", dot_path, "-o", path])

    def load_from_prov_json(self, json_path):
        """
        Load an existing PROV-JSON and merge it into the current document.
        Unification happens automatically by identifier.
        """
        temp_doc = ProvDocument()
        with open(json_path, "rb") as f:
            temp_doc = temp_doc.deserialize(content=f.read())

        for ns in temp_doc.namespaces:
            prefix = ns.prefix
            uri = str(ns.uri)
            if prefix not in self.doc._namespaces:
                self.doc.add_namespace(prefix, uri)

        self.doc.update(temp_doc)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="y2Graph",
        description="Build and merge W3C-PROV provenance graphs from YAML or PROV-JSON.",
    )

    parser.add_argument(
        "filenames",
        nargs="+",
        help="Input files (YAML workflows or PROV JSONs)",
    )

    parser.add_argument(
        "--from-json",
        action="store_true",
        help="Treat input files as PROV-JSON instead of YAML",
    )

    parser.add_argument(
        "--join",
        action="store_true",
        help="Join all inputs into a single PROV document",
    )

    parser.add_argument("-j", "--json", help="Output JSON filename")
    parser.add_argument("-o", "--output", help="Output graph filename")

    args = parser.parse_args()

    # =========================
    # JOINED MODE
    # =========================
    if args.join:
        manager = ProvWorkflowManager()

        for file in args.filenames:
            if args.from_json:
                manager.load_from_prov_json(file)
            else:
                manager.load_from_yaml(file)

        json_path = args.json or "final_prov.json"
        if not json_path.endswith(".json"):
            json_path += ".json"

        graph_path = args.output or "final_graph.pdf"
        if not graph_path.endswith((".png", ".pdf")):
            graph_path += ".pdf"

        if not args.from_json: 
            manager.export_prov_json(json_path)
        manager.render_graph(graph_path)

    # =========================
    # SEPARATE MODE
    # =========================
    else:
        for file in args.filenames:
            manager = ProvWorkflowManager()

            if args.from_json:
                manager.load_from_prov_json(file)
            else:
                manager.load_from_yaml(file)

            base = os.path.splitext(os.path.basename(file))[0]
            if not args.from_json: 
                manager.export_prov_json(f"{base}.json")
            manager.render_graph(f"{base}.pdf")
