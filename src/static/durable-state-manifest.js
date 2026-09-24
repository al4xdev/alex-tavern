export function clonePhysicalEntities(entities) {
    return JSON.parse(JSON.stringify(entities || []));
}

export function manifestFromDurableState(durableState) {
    const entities = Object.values(durableState?.physical_entities || {}).map((entity) => ({
        entity_id: entity.entity_id,
        key: entity.key,
        kind: entity.kind,
        scene_key: entity.scene_key,
        dimensions: Object.fromEntries(
            Object.entries(entity.dimensions || {}).map(([dimension, value]) => (
                [dimension, value.state]
            )),
        ),
    }));
    return entities.sort((left, right) => (
        left.entity_id < right.entity_id ? -1 : left.entity_id > right.entity_id ? 1 : 0
    ));
}
