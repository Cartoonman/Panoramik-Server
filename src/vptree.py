from collections import namedtuple
from collections import deque
import random
import numpy as np
import heapq

class NDPoint(object):
    """
    A point in n-dimensional space
    """

    def __init__(self, x, idx=None):
        self.x = np.array(x)
        self.idx = idx
    def __repr__(self):
        return "NDPoint(idx=%s, x=%s)" % (self.idx, self.x)

class VPTree(object):
    """
    An efficient data structure to perform nearest-neighbor
    search. 
    """

    def __init__(self, points, dist_fn=None):
        self.left = None
        self.right = None
        self.mu = None
        self.dist_fn = dist_fn if dist_fn is not None else l2

        # choose a better vantage point selection process
        self.vp = points.pop(random.randrange(len(points)))

        if len(points) < 1:
            return

        # choose division boundary at median of distances
        distances = [self.dist_fn(self.vp, p) for p in points]
        self.mu = np.median(distances)

        left_points = []  # all points inside mu radius
        right_points = []  # all points outside mu radius
        for i, p in enumerate(points):
            d = distances[i]
            if d >= self.mu:
                right_points.append(p)
            else:
                left_points.append(p)

        if len(left_points) > 0:
            self.left = VPTree(points=left_points, dist_fn=self.dist_fn)

        if len(right_points) > 0:
            self.right = VPTree(points=right_points, dist_fn=self.dist_fn)

    def is_leaf(self):
        return (self.left is None) and (self.right is None)

class PriorityQueue(object):
    def __init__(self, size=None):
        self.queue = []
        self.size = size

    def push(self, priority, item):
        self.queue.append((priority, item))
        self.queue.sort()
        if self.size is not None and len(self.queue) > self.size:
            self.queue.pop()


### Distance functions
def l2(p1, p2):
    return np.sqrt(np.sum(np.power(p2.x - p1.x, 2)))


def str2hex(x):
    scale = 16 ## equals to hexadecimal
    num_of_bits = 64
    return bin(int(x, scale))[2:].zfill(num_of_bits)



def hamming(p1,p2):
    x = str2hex(str(p1.x))
    y = str2hex(str(p2.x))
    """Calculate the Hamming distance between two bit strings"""
    assert len(x) == len(y)
    count,z = 0,int(x,2)^int(y,2)
    while z:
        count += 1
        z &= z-1 # magic!
    return count

### Operations
def get_nearest_neighbors(tree, q, k=1):
    """
    find k nearest neighbor(s) of q

    :param tree:  vp-tree
    :param q: a query point
    :param k: number of nearest neighbors

    """

    # buffer for nearest neightbors
    neighbors = PriorityQueue(k)

    # list of nodes ot visit
    visit_stack = deque([tree])

    # distance of n-nearest neighbors so far
    tau = np.inf

    while len(visit_stack) > 0:
        node = visit_stack.popleft()
        if node is None:
            continue

        d = tree.dist_fn(q, node.vp)
        if d < tau:
            neighbors.push(d, node.vp)
            tau, _ = neighbors.queue[-1]

        if node.is_leaf():
            continue

        if d < node.mu:
            if d < node.mu + tau:
                visit_stack.append(node.left)
            if d >= node.mu - tau:
                visit_stack.append(node.right)
        else:
            if d >= node.mu - tau:
                visit_stack.append(node.right)
            if d < node.mu + tau:
                visit_stack.append(node.left)
    return neighbors.queue


def get_all_in_range(tree, q, tau):
    """
    find all points within a given radius of point q

    :param tree: vp-tree
    :param q: a query point
    :param tau: the maximum distance from point q
    """

    # buffer for nearest neightbors
    neighbors = []

    # list of nodes ot visit
    visit_stack = deque([tree])

    while len(visit_stack) > 0:
        node = visit_stack.popleft()
        if node is None:
            continue

        d = tree.dist_fn(q, node.vp)
        if d < tau:
            neighbors.append((d, node.vp))

        if node.is_leaf():
            continue

        if d < node.mu:
            if d < node.mu + tau:
                visit_stack.append(node.left)
            if d >= node.mu - tau:
                visit_stack.append(node.right)
        else:
            if d >= node.mu - tau:
                visit_stack.append(node.right)
            if d < node.mu + tau:
                visit_stack.append(node.left)
    return neighbors



if __name__ == '__main__':
    X = np.random.uniform(0, 100000, size=10000)
    Y = np.random.uniform(0, 100000, size=10000)
    
    well = [('f5b31c8ce318295b', '/tmp/66.jpg'), ('572979f747012c99', '/tmp/41.jpg'), ('43f7b7636b48d110', '/tmp/42.jpg'), ('572939f747032c99', '/tmp/61.jpg'), ('47b7a7476b48c192', '/tmp/27.jpg'), ('e7953d69820b1c79', '/tmp/22.jpg'), ('290d9da9d69d721c', '/tmp/58.jpg'), ('e3773707d38189c1', '/tmp/18.jpg'), ('176b84f31dcd128d', '/tmp/10.jpg'), ('37f75a0887cc8595', '/tmp/2.jpg'), ('95156b4b6d2b5b05', '/tmp/43.jpg'), ('737038bc6ff12407', '/tmp/34.jpg'), ('95b31cab5a195b89', '/tmp/26.jpg'), ('37f75a0887cc8595', '/tmp/37.jpg'), ('c58d8ed8999ba60d', '/tmp/16.jpg'), ('bf834c01f91e7916', '/tmp/23.jpg'), ('517bee850da2e386', '/tmp/40.jpg'), ('ab19550775e11d17', '/tmp/35.jpg'), ('d1193939ddc5c6c2', '/tmp/68.jpg'), ('8f435047ad9c23b7', '/tmp/52.jpg'), ('a9abc4752e560cba', '/tmp/13.jpg'), ('b5db4be842a43873', '/tmp/67.jpg'), ('15156b4b2dab3b85', '/tmp/36.jpg'), ('ef778d14ad0b402d', '/tmp/44.jpg'), ('4bb5bc0f0b6b0b13', '/tmp/6.jpg'), ('5b5b86a46f5e9508', '/tmp/29.jpg'), ('33e64a4b0d1f9d15', '/tmp/4.jpg'), ('8955796b963986b8', '/tmp/46.jpg'), ('9fd304a1f906395e', '/tmp/59.jpg'), ('09e2af4455d4b6e9', '/tmp/5.jpg'), ('01ab4541aa73f6f6', '/tmp/11.jpg'), ('a9abc4752e560cba', '/tmp/8.jpg'), ('55dd3333eb52030b', '/tmp/63.jpg'), ('0feb0f1b6a68d0b1', '/tmp/47.jpg'), ('c73bc03b19cd12cd', '/tmp/51.jpg'), ('9363ddb89a4b292c', '/tmp/14.jpg'), ('bf936c07215a855b', '/tmp/45.jpg'), ('a5c3b85313d143f5', '/tmp/31.jpg'), ('b5644f13b3ec948c', '/tmp/33.jpg'), ('09e3afc42ba262f3', '/tmp/57.jpg'), ('112dee7a3b870339', '/tmp/3.jpg'), ('05074d3b6edd0e4e', '/tmp/65.jpg'), ('7915c68713c76e0b', '/tmp/56.jpg'), ('9fd304e17906395e', '/tmp/12.jpg'), ('bd050e9e37664dc1', '/tmp/69.jpg'), ('af13e55f21695e01', '/tmp/54.jpg'), ('9fd304f1398a39ca', '/tmp/28.jpg'), ('7f378c57ab422c03', '/tmp/21.jpg'), ('bf936c07a15e815a', '/tmp/15.jpg'), ('05074d3b6edd0e4e', '/tmp/53.jpg'), ('737038ac6ff52407', '/tmp/64.jpg'), ('9f49603787af2c1c', '/tmp/38.jpg'), ('5153ae151decc30f', '/tmp/1.jpg'), ('91360d6ebbe82b91', '/tmp/9.jpg'), ('8f27f3db211d6908', '/tmp/25.jpg'), ('1fd304f339ca3549', '/tmp/62.jpg'), ('f1f38205b4b7825b', '/tmp/32.jpg'), ('09e2abc455a7a6e9', '/tmp/50.jpg'), ('3f5fe46499e0d901', '/tmp/60.jpg'), ('9f49603187a7ae2e', '/tmp/17.jpg'), ('e39be01a9bc92d92', '/tmp/24.jpg'), ('dd250ece33b22563', '/tmp/7.jpg'), ('1390aceef1eb1619', '/tmp/19.jpg'), ('8f435067855c33f6', '/tmp/39.jpg'), ('95a31ca9d30d7b0b', '/tmp/48.jpg'), ('71b013158dc3d6e7', '/tmp/55.jpg'), ('aba955815555f351', '/tmp/49.jpg'), ('8faf7610cd79410d', '/tmp/20.jpg'), ('ef778d14ad0b402d', '/tmp/30.jpg')]

    points = map(lambda x: NDPoint(x[0], x[1]), well)
    
    #points = [NDPoint(x,i) for i, x in  enumerate(zip(X,Y))]
    #print points
    print ("_----------------------------")
    tree = VPTree(points,hamming)
    q = NDPoint('bf936c07a15e815a')
    #neighbors = get_nearest_neighbors(tree, q, 5)
    ok = get_all_in_range(tree,q,17)
    print ok
    
    print hamming(NDPoint('bf936c07a15e815a', '/tmp/15.jpg'),NDPoint('bf936c07215a855b', '/tmp/45.jpg'))
    print "query:"
    print "\t", q
    print "nearest neighbors: "
    for d, n in ok:
        print "\t", n

    
