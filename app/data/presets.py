"""Read-only catalog presets for materials and sections.

Presets are static engineering data (concrete grades per NSR-10/ACI, steel
grades, common AISC metric sections) shared across all projects. Elements can
reference a preset as ``preset:<key>`` without creating a project row; projects
can also copy a preset into their own catalog and customize it.
"""

MATERIAL_PRESETS: list[dict] = [
    {
        'key': 'concrete-21',
        'name': "Concrete f'c=21 MPa",
        'category': 'concrete',
        'properties': {'fc_mpa': 21, 'elastic_modulus_mpa': 21500, 'density_kg_m3': 2400, 'poisson': 0.2},
    },
    {
        'key': 'concrete-28',
        'name': "Concrete f'c=28 MPa",
        'category': 'concrete',
        'properties': {'fc_mpa': 28, 'elastic_modulus_mpa': 24870, 'density_kg_m3': 2400, 'poisson': 0.2},
    },
    {
        'key': 'concrete-35',
        'name': "Concrete f'c=35 MPa",
        'category': 'concrete',
        'properties': {'fc_mpa': 35, 'elastic_modulus_mpa': 27800, 'density_kg_m3': 2400, 'poisson': 0.2},
    },
    {
        'key': 'concrete-42',
        'name': "Concrete f'c=42 MPa",
        'category': 'concrete',
        'properties': {'fc_mpa': 42, 'elastic_modulus_mpa': 30460, 'density_kg_m3': 2400, 'poisson': 0.2},
    },
    {
        'key': 'steel-a36',
        'name': 'Steel A-36',
        'category': 'steel',
        'properties': {'fy_mpa': 250, 'fu_mpa': 400, 'elastic_modulus_mpa': 200000, 'density_kg_m3': 7850, 'poisson': 0.3},
    },
    {
        'key': 'steel-a50',
        'name': 'Steel A-50',
        'category': 'steel',
        'properties': {'fy_mpa': 350, 'fu_mpa': 490, 'elastic_modulus_mpa': 200000, 'density_kg_m3': 7850, 'poisson': 0.3},
    },
    {
        'key': 'rebar-60',
        'name': 'Rebar Grade 60 (fy=420 MPa)',
        'category': 'steel',
        'properties': {'fy_mpa': 420, 'fu_mpa': 620, 'elastic_modulus_mpa': 200000, 'density_kg_m3': 7850, 'poisson': 0.3},
    },
    {
        'key': 'masonry',
        'name': 'Structural masonry',
        'category': 'masonry',
        'properties': {'fm_mpa': 8, 'elastic_modulus_mpa': 6000, 'density_kg_m3': 1800, 'poisson': 0.15},
    },
    {
        'key': 'timber',
        'name': 'Structural timber',
        'category': 'timber',
        'properties': {'fm_mpa': 18, 'elastic_modulus_mpa': 9000, 'density_kg_m3': 600, 'poisson': 0.3},
    },
]

SECTION_PRESETS: list[dict] = [
    {
        'key': 'rect-20x30',
        'name': 'Rectangular 0.20×0.30 m',
        'category': 'section',
        'shape': 'rectangular',
        'dimensions': {'b': 0.2, 'h': 0.3},
    },
    {
        'key': 'rect-25x40',
        'name': 'Rectangular 0.25×0.40 m',
        'category': 'section',
        'shape': 'rectangular',
        'dimensions': {'b': 0.25, 'h': 0.4},
    },
    {
        'key': 'rect-30x30',
        'name': 'Rectangular 0.30×0.30 m',
        'category': 'section',
        'shape': 'rectangular',
        'dimensions': {'b': 0.3, 'h': 0.3},
    },
    {
        'key': 'rect-30x50',
        'name': 'Rectangular 0.30×0.50 m',
        'category': 'section',
        'shape': 'rectangular',
        'dimensions': {'b': 0.3, 'h': 0.5},
    },
    {
        'key': 'rect-40x40',
        'name': 'Rectangular 0.40×0.40 m',
        'category': 'section',
        'shape': 'rectangular',
        'dimensions': {'b': 0.4, 'h': 0.4},
    },
    {
        'key': 'circle-30',
        'name': 'Circular Ø0.30 m',
        'category': 'section',
        'shape': 'circular',
        'dimensions': {'diameter': 0.3},
    },
    {
        'key': 'circle-40',
        'name': 'Circular Ø0.40 m',
        'category': 'section',
        'shape': 'circular',
        'dimensions': {'diameter': 0.4},
    },
    {
        'key': 'w200x22-5',
        'name': 'W200×22.5',
        'category': 'section',
        'shape': 'i_shape',
        'dimensions': {'d': 0.206, 'bf': 0.102, 'tf': 0.008, 'tw': 0.0062},
        'properties': {'area_m2': 0.00286, 'ix_m4': 2.0e-5, 'iy_m4': 1.42e-6},
    },
    {
        'key': 'w250x32-7',
        'name': 'W250×32.7',
        'category': 'section',
        'shape': 'i_shape',
        'dimensions': {'d': 0.258, 'bf': 0.146, 'tf': 0.0091, 'tw': 0.0061},
        'properties': {'area_m2': 0.00419, 'ix_m4': 4.91e-5, 'iy_m4': 4.73e-6},
    },
    {
        'key': 'w310x38-7',
        'name': 'W310×38.7',
        'category': 'section',
        'shape': 'i_shape',
        'dimensions': {'d': 0.31, 'bf': 0.165, 'tf': 0.0097, 'tw': 0.0058},
        'properties': {'area_m2': 0.00494, 'ix_m4': 8.51e-5, 'iy_m4': 7.23e-6},
    },
    {
        'key': 'w360x51',
        'name': 'W360×51',
        'category': 'section',
        'shape': 'i_shape',
        'dimensions': {'d': 0.355, 'bf': 0.171, 'tf': 0.0116, 'tw': 0.0072},
        'properties': {'area_m2': 0.00645, 'ix_m4': 1.42e-4, 'iy_m4': 9.68e-6},
    },
    {
        'key': 'w410x46-1',
        'name': 'W410×46.1',
        'category': 'section',
        'shape': 'i_shape',
        'dimensions': {'d': 0.403, 'bf': 0.14, 'tf': 0.0112, 'tw': 0.007},
        'properties': {'area_m2': 0.00586, 'ix_m4': 1.56e-4, 'iy_m4': 5.13e-6},
    },
]
