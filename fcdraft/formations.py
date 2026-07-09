"""Formation slot naming helpers."""

from fcdraft.config import FORMATIONS


def get_formation_slots(formation):
    raw_slots = FORMATIONS.get(formation, ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"])
    slots = []
    counts = {}
    for pos in raw_slots:
        counts[pos] = counts.get(pos, 0) + 1

    current_counts = {}
    for pos in raw_slots:
        if counts[pos] > 1:
            current_counts[pos] = current_counts.get(pos, 0) + 1
            slots.append(f"{pos} {current_counts[pos]}")
        else:
            slots.append(pos)
    return slots


def get_base_position(slot_name):
    return slot_name.split()[0].upper()


def build_slot_list(formation, bench_slots):
    """Starting-XI slot names for a formation plus numbered SUB slots."""
    return get_formation_slots(formation) + [f"SUB {x}" for x in range(1, bench_slots + 1)]
