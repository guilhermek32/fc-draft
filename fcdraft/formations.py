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


# Portuguese display labels for base positions. Display-only: slot keys stay
# in English everywhere (persisted state, position matching, URLs, CSV export).
POSITION_LABELS_PT = {
    "GK": "GOL", "CB": "ZAG", "LB": "LE", "RB": "LD",
    "LWB": "ALE", "RWB": "ALD", "CDM": "VOL", "CM": "MC",
    "CAM": "MEI", "LM": "ME", "RM": "MD", "LW": "PE", "RW": "PD",
    "ST": "ATA", "CF": "CA", "LF": "PE", "RF": "PD", "SUB": "RES",
}


def position_label_pt(base_pos):
    """Portuguese label for a base position code (falls back to the code)."""
    return POSITION_LABELS_PT.get(str(base_pos).upper(), base_pos)


def slot_label_pt(slot):
    """Portuguese label for a slot name, keeping the number ("CB 1" -> "ZAG 1")."""
    base = get_base_position(slot)
    return position_label_pt(base) + slot[len(base):]


def build_slot_list(formation, bench_slots):
    """Starting-XI slot names for a formation plus numbered SUB slots."""
    return get_formation_slots(formation) + [f"SUB {x}" for x in range(1, bench_slots + 1)]


def build_snake_sequence(ordered_names, bench_slots):
    """Snake-order pick sequence over 11 + bench rounds for an already-ordered list."""
    total_rounds = 11 + bench_slots
    draft_sequence = []
    overall_pick = 1
    for r in range(1, total_rounds + 1):
        round_order = list(ordered_names)
        if r % 2 == 0:
            round_order.reverse()
        for pick_in_round, picker in enumerate(round_order):
            draft_sequence.append({
                "round": r,
                "pick_in_round": pick_in_round + 1,
                "overall_pick": overall_pick,
                "participant": picker,
            })
            overall_pick += 1
    return draft_sequence
