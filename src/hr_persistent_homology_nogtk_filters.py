##
import os
import graph_tool.all as gt
from numpy.linalg import norm
from pylab import *
from datetime import datetime

##
# importing data
##

##
mass, lum, mag = loadtxt("new_data.txt", usecols=(2, 3, 4), unpack=True, skiprows=2)
# building the graph


g = gt.Graph(directed=False)

Lum = g.new_vertex_property("float")
Mag = g.new_vertex_property("float")
Mass = g.new_vertex_property("float")
Position = g.new_vp("vector<double>")
Distance = g.new_edge_property("float")

g.vp.lum = Lum
g.vp.mag = Mag
g.vp.mass = Mass
g.vp.pos = Position
g.ep.dist = Distance

N = 800
v = g.add_vertex(N)

mag = mag[0:N]
lum = lum[0:N]
mass = mass[0:N]

init_foot = 0.0001
ibin =      0.0001
fbin =      0.15

max_iter=1
init_step=0.5
K=1.5


#init_foot = 0.003
#ibin = 0.003
#fbin = 0.21
#init_step = 0.5  # move step
#K = 1.5
#max_iter = 8

##
# minmax scaling
mag -= min(mag)
mag /= max(mag)
lum -= min(lum)
lum /= max(lum)
mass -= min(mass)
mass /= max(mass)
##
# applying properties
for i, v in enumerate(g.vertices()):
    g.vp.mass[v] = mass[i]
    g.vp.lum[v] = lum[i]
    g.vp.mag[v] = mag[i]
    g.vp.pos[v] = np.array([mag[i], -lum[i]])

##
posv = g.vp.pos.get_2d_array([0, 1]).T
##
gg, gpos = gt.geometric_graph(posv, fbin)
##
ug = gt.graph_union(gg, g, intersection=g.vertex_index, internal_props=True)
##


def set_distances(g):
    dists = []
    for e in ug.edges():
        s, t = e
        pos_s = np.array(g.vp.pos[s])
        pos_t = np.array(g.vp.pos[t])
        distance = norm(pos_s - pos_t)
        # print(distance)
        dists.append(distance)
        g.ep.dist[e] = distance
    return dists

##
distances = set_distances(ug)

##
def graph_sequence(g, ibin, init_foot, fbin, init_step, max_iter, K):

    dist_array = np.array(g.ep.dist.a)
    filter_array = dist_array <= ibin
    gv = gt.GraphView(g, efilt=filter_array)
    ng = gt.Graph(gv, prune=True)
    pos = gt.sfdp_layout(ng, pos=ng.vp.pos, K=K)
    ng.vp.pos = pos
    graphs = [ng]

    cbin = ibin + init_foot
    # pos = gt.sfdp_layout(g, pos=pos, K=1.5)
    while cbin <= fbin:
        filter_array = dist_array <= cbin
        gv = gt.GraphView(g, efilt=filter_array)
        ng = gt.Graph(gv, prune=True)
        ng.copy_property(graphs[-1].vp.pos, tgt=ng.vp.pos)
        # print(ng.num_edges())
        ng.vp.pos = gt.sfdp_layout(
            ng, pos=ng.vp.pos, max_iter=max_iter, init_step=init_step, K=K
        )
        graphs.append(ng)

        cbin += init_foot
        # step += init_foot * 3
    return graphs


def draw_frames(glist):
    stamp = datetime.strftime(datetime.now(), "%d_%h-%H-%M")
    outpath = f"./outputs_{stamp}"
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    for i, gu in enumerate(glist):
        gt.graph_draw(
            gu,
            pos=gu.vp.pos,
            vertex_fill_color=gu.vp.lum,
            edge_pen_width=0.2,
            vertex_size=gt.prop_to_size(gu.vp.mass, mi=2, ma=10, log=False, power=2),
            output=os.path.join(outpath, "frame%06d.png" % i), adjust_aspect=False
        )


##
%timeit -n 1 -r 1 graph_sequence(ug, ibin, init_foot, fbin, init_step, max_iter, K)
##
glist = graph_sequence(ug, ibin, init_foot, fbin, init_step, max_iter, K)

##
draw_frames(glist)

##
