from prov.model import ProvDocument
from prov.dot import prov_to_dot

# Create a provenance document
doc = ProvDocument()

# Define namespaces (optional, but stylistic)
ex = doc.add_namespace("ex", "http://example.org/")

# Create the elements
agent = doc.agent("ex:Agent")
entity = doc.entity("ex:Entity")
activity = doc.activity("ex:Activity")

# Add relations according to your diagram
doc.wasAttributedTo(entity, agent)
doc.wasAssociatedWith(activity, agent)
doc.wasGeneratedBy(entity, activity)
doc.used(activity, entity)
doc.wasDerivedFrom(entity, entity)   # self-derivation loop

# Convert to DOT
dot = prov_to_dot(doc, direction="LR")

# Change layout engine: dot / neato / fdp / sfdp / twopi / circo
# dot.set_rankdir("LR") 
dot.set("layout", "neato")   # or fdp, sfdp, circo, twopi
dot.set("splines", "curved")
dot.set("nodesep", "2.5")
dot.set("ranksep", "12.5")
# dot.set("pad", "10.6")
dot.set("overlap", "False")
# for node in dot.get_nodes(): 
#     node.set("marg", "10.6")

# for edge in dot.get_edges():
#     edge.set("minlen", "3")  # default = 1

# for edge in dot.get_edges():
#     edge.set("minlen", "2")

# for edge in dot.get_edges():
#     edge.set("labelfloat", "true")
#     edge.set("labeldistance", "4.0")   # default ~1; larger = farther away
#     edge.set("labelangle", "-25")      # rotates label relative to edge
#     edge.set("labelfontsize", "10")    # optional tweak
#     edge.set("minlen", "2")            # increases edge length slightly


# Save image output (choose PNG or PDF)
dot.write_svg("prov_diagram.svg")