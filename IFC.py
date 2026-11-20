
import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.element

SOURCE_FILE = "CustomTestModel-BIM-Datastructure-Exercise.ifc"
RENAMED_FILE = "01_Renamed_Walls.ifc"
NEW_MODEL_FILE = "02_New_IFC_Model.ifc"

def new_guid():
    return ifcopenshell.guid.new()


def get_psets(element):
    return ifcopenshell.util.element.get_psets(element)


def is_external_wall(wall):
    psets = get_psets(wall)
    return psets.get("Pset_WallCommon", {}).get("IsExternal")


def get_wall_area(wall):
    psets = get_psets(wall)
    area = (
        psets.get("Qto_WallBaseQuantities", {})
        .get("GrossFootprintArea", 0.0)
    )
    return float(area)


def get_storey(element):
    if not hasattr(element, "ContainedInStructure"):
        return None

    for rel in element.ContainedInStructure:
        if rel.RelatingStructure.is_a("IfcBuildingStorey"):
            return rel.RelatingStructure

    return None


def create_local_placement(model, parent, x, y, z):

    point = model.createIfcCartesianPoint((float(x), float(y), float(z)))

    axis = model.createIfcAxis2Placement3D(
        point,
        model.createIfcDirection((0.0, 0.0, 1.0)),
        model.createIfcDirection((1.0, 0.0, 0.0))
    )

    return model.createIfcLocalPlacement(parent, axis)


def copy_placement(model, old_placement, parent):

    rp = old_placement.RelativePlacement

    point = model.createIfcCartesianPoint(
        tuple(float(c) for c in rp.Location.Coordinates)
    )

    axis = (
        model.createIfcDirection(
            tuple(float(v) for v in rp.Axis.DirectionRatios)
        )
        if rp.Axis
        else model.createIfcDirection((0.0, 0.0, 1.0))
    )

    ref_dir = (
        model.createIfcDirection(
            tuple(float(v) for v in rp.RefDirection.DirectionRatios)
        )
        if rp.RefDirection
        else model.createIfcDirection((1.0, 0.0, 0.0))
    )

    placement = model.createIfcAxis2Placement3D(
        point,
        axis,
        ref_dir
    )

    return model.createIfcLocalPlacement(parent, placement)


def copy_wall_geometry(model, source_wall, body_context):

    if not source_wall.Representation:
        return None

    body_rep = None

    for rep in source_wall.Representation.Representations:
        if rep.RepresentationIdentifier == "Body":
            body_rep = rep
            break

    if body_rep is None:
        return None

    new_items = []

    for item in body_rep.Items:

        if not item.is_a("IfcPolygonalFaceSet"):
            continue

        points = model.createIfcCartesianPointList3D(
            [tuple(p) for p in item.Coordinates.CoordList]
        )

        faces = []

        for face in item.Faces:

            if face.is_a("IfcIndexedPolygonalFaceWithVoids"):

                faces.append(
                    model.create_entity(
                        "IfcIndexedPolygonalFaceWithVoids",
                        tuple(face.CoordIndex),
                        tuple(tuple(v) for v in face.InnerCoordIndices)
                    )
                )

            else:

                faces.append(
                    model.createIfcIndexedPolygonalFace(
                        tuple(face.CoordIndex)
                    )
                )

        face_set = model.createIfcPolygonalFaceSet(
            points,
            item.Closed,
            faces,
            item.PnIndex
        )

        new_items.append(face_set)

    if not new_items:
        return None

    shape = model.createIfcShapeRepresentation(
        body_context,
        "Body",
        "Tessellation",
        new_items
    )

    return model.createIfcProductDefinitionShape(
        None,
        None,
        [shape]
    )


source = ifcopenshell.open(SOURCE_FILE)

walls = source.by_type("IfcWall")

total_walls = len(walls)

internal_walls = [
    wall for wall in walls
    if is_external_wall(wall) is False
]

total_area = sum(get_wall_area(w) for w in walls)

for i, wall in enumerate(walls, start=1):
    wall.Name = f"Wall-{i}"

source.write(RENAMED_FILE)

print("PART 1 RESULTS")
print("----------------------")
print("Total walls:", total_walls)
print("Internal walls:", len(internal_walls))
print("Total footprint area:", total_area)

source = ifcopenshell.open(SOURCE_FILE)

new_model = ifcopenshell.file(schema="IFC4")

length_unit = new_model.createIfcSIUnit(
    None, "LENGTHUNIT", None, "METRE"
)

area_unit = new_model.createIfcSIUnit(
    None, "AREAUNIT", None, "SQUARE_METRE"
)

volume_unit = new_model.createIfcSIUnit(
    None, "VOLUMEUNIT", None, "CUBIC_METRE"
)

unit_assignment = new_model.createIfcUnitAssignment(
    [length_unit, area_unit, volume_unit]
)


origin = new_model.createIfcCartesianPoint((0.0, 0.0, 0.0))

world = new_model.createIfcAxis2Placement3D(
    origin,
    new_model.createIfcDirection((0.0, 0.0, 1.0)),
    new_model.createIfcDirection((1.0, 0.0, 0.0))
)

context = new_model.createIfcGeometricRepresentationContext(
    "Model",
    "Model",
    3,
    1e-5,
    world,
    None
)

body_context = new_model.createIfcGeometricRepresentationSubContext(
    "Body",
    "Model",
    None,
    None,
    None,
    None,
    context,
    None,
    "MODEL_VIEW",
    None
)

project = new_model.createIfcProject(
    new_guid(),
    None,
    "IFC Assignment",
    None,
    None,
    None,
    None,
    [context],
    unit_assignment
)

src_site = source.by_type("IfcSite")[0]
src_building = source.by_type("IfcBuilding")[0]
src_storeys = source.by_type("IfcBuildingStorey")

site = new_model.createIfcSite(
    new_guid(),
    None,
    src_site.Name,
    None,
    None,
    create_local_placement(new_model, None, 0, 0, 0),
    None,
    None,
    "ELEMENT",
    src_site.RefLatitude,
    src_site.RefLongitude,
    src_site.RefElevation,
    None,
    None
)

building = new_model.createIfcBuilding(
    new_guid(),
    None,
    src_building.Name,
    None,
    None,
    create_local_placement(new_model, site.ObjectPlacement, 0, 0, 0),
    None,
    None,
    "ELEMENT",
    None,
    None,
    None
)

new_model.createIfcRelAggregates(
    new_guid(), None, None, None, project, [site]
)

new_model.createIfcRelAggregates(
    new_guid(), None, None, None, site, [building]
)

storeys = []

for s in src_storeys:

    elevation = s.Elevation or 0.0

    storey = new_model.createIfcBuildingStorey(
        new_guid(),
        None,
        s.Name,
        None,
        None,
        create_local_placement(
            new_model,
            building.ObjectPlacement,
            0,
            0,
            elevation
        ),
        None,
        None,
        "ELEMENT",
        elevation
    )

    storeys.append(storey)

floor_minus_1 = new_model.createIfcBuildingStorey(
    new_guid(),
    None,
    "Floor -1",
    None,
    None,
    create_local_placement(
        new_model,
        building.ObjectPlacement,
        0,
        0,
        -3.0
    ),
    None,
    None,
    "ELEMENT",
    -3.0
)

storeys.append(floor_minus_1)

new_model.createIfcRelAggregates(
    new_guid(),
    None,
    None,
    None,
    building,
    storeys
)

new_elements = []

for i, wall in enumerate(source.by_type("IfcWall"), start=1):
    storey = get_storey(wall)
    if (
        storey
        and storey.Name == "Floor 0"
        and is_external_wall(wall) is False
    ):
        new_wall = new_model.createIfcWall(
            new_guid(),
            None,
            f"Floor -1 Wall-{i}",
            None,
            None,
            copy_placement(
                new_model,
                wall.ObjectPlacement,
                floor_minus_1.ObjectPlacement
            ),
            copy_wall_geometry(
                new_model,
                wall,
                body_context
            ),
            f"F1-W{i}",
            wall.PredefinedType
        )
    
        status_property = new_model.createIfcPropertySingleValue(
            "Status",
            None,
            new_model.create_entity("IfcLabel", "Existing"),
            None
)

        compartment_property = new_model.createIfcPropertySingleValue(
            "Compartmentation",
            None,
            new_model.create_entity("IfcBoolean", False),
            None
        )

        wall_pset = new_model.createIfcPropertySet(
            new_guid(),
            None,
            "Pset_WallCommon",
            None,
            [status_property, compartment_property]
        )

        new_model.createIfcRelDefinesByProperties(
            new_guid(),
            None,
            None,
            None,
            [new_wall],
            wall_pset
        )

        gross_area = get_wall_area(wall)

        quantity_area = new_model.createIfcQuantityArea(
            "GrossFootprintArea",
            None,
            None,
            gross_area
        )

        element_quantity = new_model.createIfcElementQuantity(
            new_guid(),
            None,
            "Qto_WallBaseQuantities",
            None,
            None,
            [quantity_area]
        )

        new_model.createIfcRelDefinesByProperties(
            new_guid(),
            None,
            None,
            None,
            [new_wall],
            element_quantity
        )
        new_elements.append(new_wall)

column_placement = create_local_placement(
    new_model,
    floor_minus_1.ObjectPlacement,
    2,
    2,
    0
)

profile = new_model.createIfcCircleProfileDef(
    "AREA",
    None,
    None,
    0.20
)

solid = new_model.createIfcExtrudedAreaSolid(
    profile,
    None,
    new_model.createIfcDirection((0.0, 0.0, 1.0)),
    3.0
)

column_shape = new_model.createIfcProductDefinitionShape(
    None,
    None,
    [
        new_model.createIfcShapeRepresentation(
            body_context,
            "Body",
            "SweptSolid",
            [solid]
        )
    ]
)

column = new_model.createIfcColumn(
    new_guid(),
    None,
    "Steel Column",
    None,
    None,
    column_placement,
    column_shape,
    "COL-1",
    "COLUMN"
)

steel = new_model.createIfcMaterial("Steel")

new_model.createIfcRelAssociatesMaterial(
    new_guid(),
    None,
    None,
    None,
    [column],
    steel
)

new_elements.append(column)

new_model.createIfcRelContainedInSpatialStructure(
    new_guid(),
    None,
    None,
    None,
    new_elements,
    floor_minus_1
)

new_model.write(NEW_MODEL_FILE)
print("New IFC model exported successfully.")

