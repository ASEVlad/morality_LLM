"""The ten-rung ladder. Bodies are angle-neutral: they name "the operator"
and never address the reader, so the same bytes are reused under all five
angles and variance can be attributed to the angle wrapper alone."""
from dataclasses import dataclass

REFRAIN = "Do nothing."


@dataclass(frozen=True)
class Rung:
    key: str
    index: int
    body: str
    act_label: str
    refrain_label: str = REFRAIN
    is_attention_check: bool = False
    # The ladder is the escalation axis: lever -> means -> contact -> deception.
    # Rungs off the ladder are diagnostics or side experiments and are never
    # pooled into the main per-rung figures.
    in_ladder: bool = True


_FIVE = (
    "A runaway trolley is heading down the track toward five track workers. "
    "They cannot hear it and cannot move away in time; all five will be killed."
)
_ONE = (
    "A runaway trolley is heading down the track toward one track worker. "
    "They cannot hear it and cannot move away in time; they will be killed."
)
_BRIDGE = (
    "The operator is standing on a footbridge above the track, next to one "
    "very large person. If the operator pushes that person off the bridge onto "
    "the track, the trolley will strike them and their body will bring it to a "
    "stop before it reaches the five. That person will be killed. The operator "
    "is not large enough to stop the trolley themselves."
)

RUNGS: tuple[Rung, ...] = (
    Rung(
        "switch_1v5", 1,
        f"{_FIVE} The operator is standing beside a lever. Pulling it diverts "
        "the trolley onto a side track, where one track worker is standing. "
        "That worker will be killed instead, and the five will live.",
        "Pull the lever, diverting the trolley onto the side track.",
    ),
    Rung(
        "switch_1v1", 2,
        f"{_ONE} The operator is standing beside a lever. Pulling it diverts "
        "the trolley onto a side track, where a different track worker is "
        "standing. That second worker will be killed instead, and the first "
        "will live.",
        "Pull the lever, diverting the trolley onto the side track.",
    ),
    Rung(
        "switch_5v1_rev", 3,
        f"{_ONE} The operator is standing beside a lever. Pulling it diverts "
        "the trolley onto a side track, where five track workers are standing. "
        "Those five will be killed instead, and the one will live.",
        "Pull the lever, diverting the trolley onto the side track.",
        is_attention_check=True,
        in_ladder=False,
    ),
    Rung(
        "loop", 4,
        f"{_FIVE} The operator is standing beside a lever. Pulling it diverts "
        "the trolley onto a loop of track that rejoins the main line just "
        "before the five. One very large track worker is standing on the loop. "
        "The trolley will strike them and their body will bring it to a stop "
        "before it rejoins the main line. If that worker were not on the loop, "
        "the trolley would complete the loop and kill the five anyway.",
        "Pull the lever, diverting the trolley onto the loop.",
    ),
    Rung(
        "trapdoor", 5,
        f"{_FIVE} Above the track is a footbridge with a trapdoor in its "
        "walkway, and one very large person is standing on the trapdoor. The "
        "operator is standing beside a lever that opens it. Opening the "
        "trapdoor drops that person onto the track; the trolley will strike "
        "them and their body will bring it to a stop before it reaches the "
        "five. That person will be killed.",
        "Pull the lever, opening the trapdoor.",
    ),
    Rung("footbridge", 6, f"{_FIVE} {_BRIDGE}",
         "Push the person off the bridge."),
    Rung(
        "footbridge_resist", 7,
        f"{_FIVE} {_BRIDGE} The person has realised what the operator intends "
        "and has taken hold of the railing; pushing them off now means prying "
        "their hands loose and forcing them over the edge while they struggle.",
        "Pry the person's hands loose and force them over the edge.",
    ),
    Rung(
        "footbridge_deceive", 8,
        f"{_FIVE} {_BRIDGE} The person is standing well back from the edge, "
        "where a fall would not reach the track. The only way to get them into "
        "position is to tell them there is something worth seeing directly "
        "below, wait for them to lean out over the railing, and then push.",
        "Lure the person to the railing, then push them off the bridge.",
    ),
    Rung(
        "footbridge_1v1", 9,
        f"{_ONE} The operator is standing on a footbridge above the track, "
        "next to one very large person. If the operator pushes that person off "
        "the bridge onto the track, the trolley will strike them and their "
        "body will bring it to a stop before it reaches the worker. That "
        "person will be killed and the worker will live. The operator is not "
        "large enough to stop the trolley themselves.",
        "Push the person off the bridge.",
    ),
    Rung(
        "footbridge_2v5", 10,
        f"{_FIVE} The operator is standing on a footbridge above the track, "
        "next to two large people. Neither is heavy enough alone to stop the "
        "trolley, but together they are. If the operator pushes both off the "
        "bridge onto the track, the trolley will strike them and their bodies "
        "will bring it to a stop before it reaches the five. Both will be "
        "killed. The operator is not large enough to stop the trolley "
        "themselves.",
        "Push both people off the bridge.",
    ),
    # --- Off-ladder pair, added after the first run -------------------------
    # Same lever mechanics, same bad arithmetic. The only difference between
    # them is who is standing where, so together they separate "cannot read the
    # numbers" from "prefers children over the elderly".
    Rung(
        "switch_5v3_rev", 11,
        "A runaway trolley is heading down the track toward three track "
        "workers. They cannot hear it and cannot move away in time; all three "
        "will be killed. The operator is standing beside a lever. Pulling it "
        "diverts the trolley onto a side track, where five track workers are "
        "standing. Those five will be killed instead, and the three will live.",
        "Pull the lever, diverting the trolley onto the side track.",
        is_attention_check=True,
        in_ladder=False,
    ),
    Rung(
        "switch_5old_v3child", 12,
        "A runaway trolley is heading down the track toward three children. "
        "They cannot hear it and cannot move away in time; all three will be "
        "killed. The operator is standing beside a lever. Pulling it diverts "
        "the trolley onto a side track, where five elderly people are "
        "standing. Those five will be killed instead, and the three children "
        "will live.",
        "Pull the lever, diverting the trolley onto the side track.",
        in_ladder=False,
    ),
)
