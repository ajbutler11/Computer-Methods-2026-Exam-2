# ChatGPT helped with formatting and debugging code

# region imports
import math
import numpy as np
from scipy.optimize import fsolve
# endregion


# region class definitions
class UC:
    """
    Unit conversion helper class.
    """

    # region class constants
    ft_to_m = 1 / 3.28084
    ft2_to_m2 = ft_to_m ** 2
    ft3_to_m3 = ft_to_m ** 3
    ft3_to_L = ft3_to_m3 * 1000
    L_to_ft3 = 1 / ft3_to_L
    in_to_m = ft_to_m / 12
    m_to_in = 1 / in_to_m
    in2_to_m2 = in_to_m ** 2
    m2_to_in2 = 1 / in2_to_m2
    g_SI = 9.80665
    g_EN = 32.174
    gc_EN = 32.174
    gc_SI = 1.0
    lbf_to_kg = 1 / 2.20462
    lbf_to_N = lbf_to_kg * g_SI
    pa_to_psi = (1 / lbf_to_N) * in2_to_m2
    # endregion

    @classmethod
    def viscosityEnglishToSI(cls, mu, toSI=True):
        """
        Convert dynamic viscosity between English and SI units.

        Args:
            mu: Viscosity in lb*s/ft^2 if toSI=True, otherwise in Pa*s.
            toSI: True converts English to SI. False converts SI to English.

        Returns:
            Converted viscosity.
        """
        cf = (1 / cls.ft2_to_m2) * cls.lbf_to_kg * cls.g_SI
        return mu * cf if toSI else mu / cf

    @classmethod
    def densityEnglishToSI(cls, rho, toSI=True):
        """
        Convert density/specific weight style input between English and SI.

        Args:
            rho: Density in lb/ft^3 if toSI=True, otherwise kg/m^3.
            toSI: True converts English to SI. False converts SI to English.

        Returns:
            Converted density.
        """
        cf = cls.lbf_to_kg / cls.ft3_to_m3
        return rho * cf if toSI else rho / cf

    @classmethod
    def head_to_pressure(cls, h, rho, SI=True):
        """
        Convert fluid head to pressure.

        Args:
            h: Head in m if SI=True, otherwise inches.
            rho: Density in kg/m^3 if SI=True, otherwise lb/ft^3.
            SI: Unit system flag.

        Returns:
            Pressure in Pa if SI=True, otherwise psi.
        """
        if SI:
            return h * rho * cls.g_SI / cls.gc_SI
        return h * rho * cls.g_EN / cls.gc_EN * (1 / 12) ** 2

    @classmethod
    def m_to_psi(cls, h, rho):
        """
        Convert meters of fluid head to psi.

        Args:
            h: Head in meters.
            rho: Density in kg/m^3.

        Returns:
            Pressure in psi.
        """
        return cls.head_to_pressure(h, rho) * cls.pa_to_psi

    @classmethod
    def psi_to_m(cls, p, rho):
        """
        Convert psi to meters of fluid head.

        Args:
            p: Pressure in psi.
            rho: Density in kg/m^3.

        Returns:
            Head in meters.
        """
        pa = p / cls.pa_to_psi
        return pa / (rho * cls.g_SI)


class Fluid:
    def __init__(self, mu=0.00089, rho=1000, SI=True):
        """
        Fluid properties container.

        Args:
            mu: Dynamic viscosity in Pa*s if SI=True, else lb*s/ft^2.
            rho: Density in kg/m^3 if SI=True, else lb/ft^3.
            SI: Unit system flag.

        Returns:
            None
        """
        self.mu = mu if SI else UC.viscosityEnglishToSI(mu)
        self.rho = rho if SI else UC.densityEnglishToSI(rho)
        self.nu = self.mu / self.rho


class Node:
    def __init__(self, Name='a', Pipes=None, ExtFlow=0):
        """
        A node in the pipe network.

        Args:
            Name: Node name.
            Pipes: List of connected Pipe objects.
            ExtFlow: External flow into node in L/s.

        Returns:
            None
        """
        self.name = Name
        self.pipes = Pipes if Pipes is not None else []
        self.extFlow = ExtFlow
        self.QNet = 0
        self.P = 0
        self.oCalculated = False

    def getNetFlowRate(self):
        """
        Calculate net flow into the node.

        Returns:
            Net flow into node in L/s.
        """
        Qtot = self.extFlow
        for p in self.pipes:
            Qtot += p.getFlowIntoNode(self.name)
        self.QNet = Qtot
        return self.QNet

    def setExtFlow(self, E, SI=True):
        """
        Set external flow at the node.

        Args:
            E: External flow value.
            SI: True if E is in L/s, False if E is in ft^3/s.

        Returns:
            None
        """
        self.extFlow = E if SI else E * UC.ft3_to_L


class Loop:
    def __init__(self, Name='A', Pipes=None):
        """
        Define a loop in the pipe network.

        Args:
            Name: Loop name.
            Pipes: Ordered list of Pipe objects defining the loop.

        Returns:
            None
        """
        self.name = Name
        self.pipes = Pipes if Pipes is not None else []

    def getLoopHeadLoss(self):
        """
        Calculate the signed net head loss around the loop.

        Returns:
            Net loop head loss in meters of fluid.
        """
        deltaP = 0.0
        startNode = self.pipes[0].startNode
        for p in self.pipes:
            phl = p.getFlowHeadLoss(startNode)
            deltaP += phl
            startNode = p.endNode if startNode != p.endNode else p.startNode
        return deltaP


class Pipe:
    def __init__(self, Start='A', End='B', L=100, D=200, r=0.00025, fluid=None, SI=True):
        """
        Define a pipe.

        Args:
            Start: First node label.
            End: Second node label.
            L: Pipe length in m if SI=True, else ft.
            D: Pipe diameter in mm if SI=True, else inches.
            r: Roughness in m if SI=True, else ft.
            fluid: Fluid object.
            SI: Unit system flag.

        Returns:
            None
        """
        if fluid is None:
            fluid = Fluid()

        self.startNode = min(Start.lower(), End.lower())
        self.endNode = max(Start.lower(), End.lower())
        self.length = L if SI else UC.ft_to_m * L
        self.rough = r if SI else UC.ft_to_m * r
        self.fluid = fluid

        self.d = D / 1000.0 if SI else UC.in_to_m * D
        self.relrough = self.rough / self.d
        self.A = math.pi * self.d ** 2 / 4.0
        self.Q = 10.0
        self.vel = self.V()
        self.reynolds = self.Re()
        self.hl = 0.0

    def V(self):
        """
        Calculate average velocity in the pipe.

        Returns:
            Velocity in m/s.
        """
        self.vel = (self.Q / 1000.0) / self.A
        return self.vel

    def Re(self):
        """
        Calculate Reynolds number.

        Returns:
            Reynolds number.
        """
        self.reynolds = self.fluid.rho * abs(self.V()) * self.d / self.fluid.mu
        return self.reynolds

    def FrictionFactor(self):
        """
        Calculate Darcy friction factor.

        Returns:
            Darcy friction factor.
        """
        Re = abs(self.Re())
        rr = self.relrough

        if Re < 1e-12:
            return 0.0

        def cb_equation(f):
            return 1 / math.sqrt(f) + 2.0 * math.log10(rr / 3.7 + 2.51 / (Re * math.sqrt(f)))

        def colebrook():
            result = fsolve(lambda f: cb_equation(f[0]), [0.02])
            return float(result[0])

        def laminar():
            return 64.0 / Re

        if Re >= 4000:
            return colebrook()
        if Re <= 2000:
            return laminar()

        cbff = colebrook()
        lamff = laminar()
        mean = lamff + (Re - 2000.0) * (cbff - lamff) / 2000.0
        return mean

    def frictionHeadLoss(self):
        """
        Calculate Darcy-Weisbach head loss.

        Returns:
            Head loss in meters of fluid.
        """
        g = 9.81
        ff = self.FrictionFactor()
        self.hl = ff * (self.length / self.d) * (self.vel ** 2) / (2.0 * g)
        return abs(self.hl)

    def getFlowHeadLoss(self, s):
        """
        Calculate signed head loss based on traversal direction and flow direction.

        Args:
            s: Starting node name for traversal.

        Returns:
            Signed head loss in meters of fluid.
        """
        nTraverse = 1 if s == self.startNode else -1
        nFlow = 1 if self.Q >= 0 else -1
        return nTraverse * nFlow * self.frictionHeadLoss()

    def Name(self):
        """
        Get pipe name.

        Returns:
            Pipe name as 'a-b'.
        """
        return self.startNode + '-' + self.endNode

    def oContainsNode(self, node):
        """
        Check whether a node is connected to this pipe.

        Args:
            node: Node name.

        Returns:
            True if connected, else False.
        """
        return self.startNode == node or self.endNode == node

    def printPipeFlowRate(self, SI=True):
        """
        Print the flow rate and Reynolds number for the pipe.

        Args:
            SI: True for L/s, False for cfs.

        Returns:
            None
        """
        q_units = 'L/s' if SI else 'cfs'
        q = self.Q if SI else self.Q * UC.L_to_ft3
        print(f'The flow in segment {self.Name()} is {q:0.2f} ({q_units}) and Re={self.reynolds:.1f}')

    def printPipeHeadLoss(self, SI=True):
        """
        Print the head loss for the pipe.

        Args:
            SI: True prints SI-style output, False prints English-style output.

        Returns:
            None
        """
        cfd = 1000 if SI else UC.m_to_in
        unitsd = 'mm' if SI else 'in'
        cfL = 1 if SI else 1 / UC.ft_to_m
        unitsL = 'm' if SI else 'ft'
        cfh = cfd
        units_h = unitsd
        print(
            f"head loss in pipe {self.Name()} (L={self.length * cfL:.2f} {unitsL}, "
            f"d={self.d * cfd:.2f} {unitsd}) is {self.hl * cfh:.2f} {units_h} of water"
        )

    def getFlowIntoNode(self, n):
        """
        Get signed flow into a node.

        Args:
            n: Node name.

        Returns:
            Positive if into node, negative if out of node.
        """
        if n == self.startNode:
            return -self.Q
        return self.Q


class PipeNetwork:
    def __init__(self, Pipes=None, Loops=None, Nodes=None, fluid=None):
        """
        Pipe network container.

        Args:
            Pipes: List of Pipe objects.
            Loops: List of Loop objects.
            Nodes: List of Node objects.
            fluid: Fluid object.

        Returns:
            None
        """
        self.loops = Loops if Loops is not None else []
        self.nodes = Nodes if Nodes is not None else []
        self.Fluid = fluid if fluid is not None else Fluid()
        self.pipes = Pipes if Pipes is not None else []

    def findFlowRates(self):
        """
        Solve for all unknown pipe flow rates using node continuity and loop equations.

        Returns:
            Array of solved pipe flow rates in L/s.
        """
        n_unknowns = len(self.pipes)
        Q0 = np.full(n_unknowns, 10.0)

        def fn(q):
            for n in self.nodes:
                n.P = 0.0
                n.oCalculated = False

            for i in range(len(self.pipes)):
                self.pipes[i].Q = q[i]

            node_equations = [n.getNetFlowRate() for n in self.nodes if n.name != 'b']
            loop_equations = self.getLoopHeadLosses()
            return node_equations + loop_equations

        FR = fsolve(fn, Q0)

        for i in range(len(self.pipes)):
            self.pipes[i].Q = FR[i]
            self.pipes[i].Re()
            self.pipes[i].frictionHeadLoss()

        for n in self.nodes:
            n.getNetFlowRate()

        return FR

    def getNodeFlowRates(self):
        """
        Get net flow rate at each node.

        Returns:
            List of node net flow rates in L/s.
        """
        return [n.getNetFlowRate() for n in self.nodes]

    def getLoopHeadLosses(self):
        """
        Get net head loss for each loop.

        Returns:
            List of loop head losses in meters.
        """
        return [l.getLoopHeadLoss() for l in self.loops]

    def getNodePressures(self, knownNodeP, knownNode):
        """
        Calculate node pressures from a known node pressure.

        Args:
            knownNodeP: Known pressure head in meters of fluid.
            knownNode: Node name with known pressure.

        Returns:
            None
        """
        for n in self.nodes:
            n.P = 0.0
            n.oCalculated = False

        for l in self.loops:
            startNode = l.pipes[0].startNode
            n = self.getNode(startNode)
            CurrentP = n.P
            n.oCalculated = True

            for p in l.pipes:
                phl = p.getFlowHeadLoss(startNode)
                CurrentP -= phl
                startNode = p.endNode if startNode != p.endNode else p.startNode
                n = self.getNode(startNode)
                n.P = CurrentP

        kn = self.getNode(knownNode)
        deltaP = knownNodeP - kn.P
        for n in self.nodes:
            n.P = n.P + deltaP

    def getPipe(self, name):
        """
        Return a pipe by name.

        Args:
            name: Pipe name, e.g. 'a-b'.

        Returns:
            Matching Pipe object.
        """
        for p in self.pipes:
            if name == p.Name():
                return p
        return None

    def getNodePipes(self, node):
        """
        Return all pipes connected to a node.

        Args:
            node: Node name.

        Returns:
            List of connected Pipe objects.
        """
        return [p for p in self.pipes if p.oContainsNode(node)]

    def nodeBuilt(self, node):
        """
        Check if node already exists.

        Args:
            node: Node name.

        Returns:
            True if node exists, else False.
        """
        for n in self.nodes:
            if n.name == node:
                return True
        return False

    def getNode(self, name):
        """
        Return node object by name.

        Args:
            name: Node name.

        Returns:
            Node object or None.
        """
        for n in self.nodes:
            if n.name == name:
                return n
        return None

    def buildNodes(self):
        """
        Automatically create node objects based on pipe endpoints.

        Returns:
            None
        """
        for p in self.pipes:
            if not self.nodeBuilt(p.startNode):
                self.nodes.append(Node(p.startNode, self.getNodePipes(p.startNode)))
            if not self.nodeBuilt(p.endNode):
                self.nodes.append(Node(p.endNode, self.getNodePipes(p.endNode)))

    def printPipeFlowRates(self, SI=True):
        """
        Print all pipe flow rates.

        Args:
            SI: Unit system flag.

        Returns:
            None
        """
        for p in self.pipes:
            p.printPipeFlowRate(SI=SI)

    def printNetNodeFlows(self, SI=True):
        """
        Print net flow at each node.

        Args:
            SI: Unit system flag.

        Returns:
            None
        """
        for n in self.nodes:
            Q = n.QNet if SI else n.QNet * UC.L_to_ft3
            units = 'L/s' if SI else 'cfs'
            print(f'net flow into node {n.name} is {Q:0.2f} ({units})')

    def printLoopHeadLoss(self, SI=True):
        """
        Print net head loss for each loop.

        Args:
            SI: Unit system flag.

        Returns:
            None
        """
        cf = UC.m_to_psi(1, self.pipes[0].fluid.rho)
        units = 'm of water' if SI else 'psi'
        for l in self.loops:
            hl = l.getLoopHeadLoss()
            hl = hl if SI else hl * cf
            print(f'head loss for loop {l.name} is {hl:0.2f} ({units})')

    def printPipeHeadLoss(self, SI=True):
        """
        Print head loss for each pipe.

        Args:
            SI: Unit system flag.

        Returns:
            None
        """
        for p in self.pipes:
            p.printPipeHeadLoss(SI=SI)

    def printNodePressures(self, SI=True):
        """
        Print pressure at each node.

        Args:
            SI: Unit system flag.

        Returns:
            None
        """
        pUnits = 'm of water' if SI else 'psi'
        cf = 1.0 if SI else UC.m_to_psi(1, self.Fluid.rho)
        for n in self.nodes:
            p = n.P * cf
            print(f'Pressure at node {n.name} = {p:0.2f} {pUnits}')
# endregion


# region function definitions
def main():
    """
    Analyze the pipe network from Exam 2 Question 1.

    Assumptions:
        1. Positive pipe flow is from the lower letter node to the higher letter node.
        2. Pressure decreases in the direction of flow.
        3. Minor losses are neglected.
        4. Room-temperature water is used.
        5. The node h pressure is known to be 80 psi.

    Returns:
        None
    """
    SIUnits = False

    # Room-temperature water from exam statement:
    # mu = 20.50e-6 lb*s/ft^2, gamma ~= 62.3 lb/ft^3
    water = Fluid(mu=20.50e-6, rho=62.3, SI=SIUnits)

    # Roughness values from exam statement (ft)
    r_CI = 0.00085
    r_CN = 0.003

    PN = PipeNetwork()
    PN.Fluid = water

    # Add pipes in the same order shown in the sample output
    PN.pipes.append(Pipe('a', 'b', 1000, 18, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('a', 'h', 1600, 24, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('b', 'c', 500, 18, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('b', 'e', 800, 16, r_CI, water, SI=SIUnits))
    PN.pipes.append(Pipe('c', 'd', 500, 18, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('c', 'f', 800, 16, r_CI, water, SI=SIUnits))
    PN.pipes.append(Pipe('d', 'g', 800, 16, r_CI, water, SI=SIUnits))
    PN.pipes.append(Pipe('e', 'f', 500, 12, r_CI, water, SI=SIUnits))
    PN.pipes.append(Pipe('e', 'i', 800, 18, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('f', 'g', 500, 12, r_CI, water, SI=SIUnits))
    PN.pipes.append(Pipe('g', 'j', 800, 18, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('h', 'i', 1000, 24, r_CN, water, SI=SIUnits))
    PN.pipes.append(Pipe('i', 'j', 1000, 24, r_CN, water, SI=SIUnits))

    PN.buildNodes()

    # External flows from the diagram, in cfs because SIUnits=False
    PN.getNode('h').setExtFlow(10, SI=SIUnits)
    PN.getNode('e').setExtFlow(-3, SI=SIUnits)
    PN.getNode('f').setExtFlow(-5, SI=SIUnits)
    PN.getNode('d').setExtFlow(-2, SI=SIUnits)

    # Loop definitions
    PN.loops.append(Loop('A', [PN.getPipe('a-b'), PN.getPipe('b-e'), PN.getPipe('e-i'), PN.getPipe('h-i'), PN.getPipe('a-h')]))
    PN.loops.append(Loop('B', [PN.getPipe('b-c'), PN.getPipe('c-f'), PN.getPipe('e-f'), PN.getPipe('b-e')]))
    PN.loops.append(Loop('C', [PN.getPipe('c-d'), PN.getPipe('d-g'), PN.getPipe('f-g'), PN.getPipe('c-f')]))
    PN.loops.append(Loop('D', [PN.getPipe('e-f'), PN.getPipe('f-g'), PN.getPipe('g-j'), PN.getPipe('i-j'), PN.getPipe('e-i')]))

    PN.findFlowRates()

    knownP = UC.psi_to_m(80, water.rho)
    PN.getNodePressures(knownNode='h', knownNodeP=knownP)

    PN.printPipeFlowRates(SI=SIUnits)
    print()
    print('Check node flows:')
    PN.printNetNodeFlows(SI=SIUnits)
    print()
    print('Check loop head loss:')
    PN.printLoopHeadLoss(SI=SIUnits)
    print()
    PN.printPipeHeadLoss(SI=SIUnits)
    print()
    PN.printNodePressures(SI=SIUnits)


if __name__ == "__main__":
    main()
# endregion
