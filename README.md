# IFC Model Analysis and Generation

Python scripts that use IfcOpenShell to analyse an existing IFC model and build a new IFC4 model from scratch. Made for the openBIM data structures exercise in my MSc Digital Civil Engineering Science (TU Wien).

## What it does

**Part 1: Analysis of the source model**
- Counts all walls and the internal walls
- Calculates the total wall footprint area from existing quantities
- Renames all walls (Wall-1, Wall-2, ...)

**Part 2: New IFC4 model**
- Sets up units and a representation context
- Rebuilds the spatial structure: project, site, building and storeys
- Adds a new storey (Floor -1, 3 m high) below the ground floor
- Recreates the internal walls of floor 0 on floor -1 by extracting their geometry and creating the IFC entities manually
- Adds properties (Status = Existing, Compartmentation = False) and a gross footprint area quantity to the new walls
- Adds a circular steel column on floor -1
- Checked with the buildingSMART Validation Service

## Tools

Python, IfcOpenShell, IFC4

## How to run

    pip install ifcopenshell
    python analysis.py
    python create_model.py


