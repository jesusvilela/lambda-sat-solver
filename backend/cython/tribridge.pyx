# distutils: language = c++

from libcpp.vector cimport vector
from libcpp.string cimport string

cdef extern from "../cpp/router.hpp" namespace "tribridge":
    cdef enum StructuralClass:
        PURE_GF2
        PARTIAL_XOR_SADDLE
        UNSTRUCTURED
        
    cdef struct RouterResult:
        StructuralClass type
        string route_name
        double expected_overhead_ms
        string flavor_group

    cdef cppclass GatedRouter:
        @staticmethod
        RouterResult evaluate(float xor_fraction)
        
        @staticmethod
        RouterResult classify(const vector[vector[int]]& clauses, int num_vars)

def route_instance_topology(clauses, int num_vars):
    """
    Given the list of clauses, computes the discrete topological flavor 
    and returns the structural class and route name.
    """
    cdef vector[vector[int]] cpp_clauses
    cdef vector[int] cpp_clause
    
    for clause in clauses:
        cpp_clause.clear()
        for lit in clause:
            cpp_clause.push_back(lit)
        cpp_clauses.push_back(cpp_clause)

    cdef RouterResult res = GatedRouter.classify(cpp_clauses, num_vars)

    
    # Convert enum to string for Python dict
    cdef str struct_class_str = ""
    if res.type == PURE_GF2:
        struct_class_str = "PURE_GF2"
    elif res.type == PARTIAL_XOR_SADDLE:
        struct_class_str = "PARTIAL_XOR_SADDLE"
    else:
        struct_class_str = "UNSTRUCTURED"
        
    return {
        "class": struct_class_str,
        "route_name": res.route_name.decode("utf-8"),
        "expected_overhead_ms": res.expected_overhead_ms,
        "flavor_group": res.flavor_group.decode("utf-8")
    }

def route_instance(float xor_fraction):
    """
    Legacy evaluator using XOR clause fraction.
    """
    cdef RouterResult res = GatedRouter.evaluate(xor_fraction)
    
    cdef str struct_class_str = ""
    if res.type == PURE_GF2:
        struct_class_str = "PURE_GF2"
    elif res.type == PARTIAL_XOR_SADDLE:
        struct_class_str = "PARTIAL_XOR_SADDLE"
    else:
        struct_class_str = "UNSTRUCTURED"
        
    return {
        "class": struct_class_str,
        "route_name": res.route_name.decode("utf-8"),
        "expected_overhead_ms": res.expected_overhead_ms,
        "flavor_group": res.flavor_group.decode("utf-8")
    }

cdef extern from "../cpp/gf2_oracle.hpp" namespace "tribridge":
    cdef struct XORConstraint:
        vector[int] variables
        int rhs

    cdef struct XORRefutation:
        bint refuted
        int num_xors
        bint decides_fully

    cdef cppclass GF2Oracle:
        @staticmethod
        XORRefutation gf2_xor_refutation(const vector[XORConstraint]& xors, int num_vars, float xor_clause_fraction)

def run_gf2_oracle(xors_list, int num_vars, float xor_fraction):
    """
    Python wrapper for GF2 Gaussian elimination.
    xors_list: list of tuples (vars_list, rhs)
    """
    cdef vector[XORConstraint] cpp_xors
    cdef XORConstraint xc
    for vars_list, rhs in xors_list:
        xc.variables = vars_list
        xc.rhs = rhs
        cpp_xors.push_back(xc)

    cdef XORRefutation res = GF2Oracle.gf2_xor_refutation(cpp_xors, num_vars, xor_fraction)
    
    return {
        "refuted": res.refuted,
        "num_xors": res.num_xors,
        "decides_fully": res.decides_fully
    }
