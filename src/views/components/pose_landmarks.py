"""
Synthetic MediaPipe Pose skeletons for the authentication artwork.

Pure geometry (no Qt): it produces the 33 BlazePose landmarks, in the same index
order MediaPipe uses, for a short fall sequence. Poses come from forward kinematics
over joint angles (torso, head, arms, legs, feet) rather than from rotating one rigid
body, so limbs bend the way a real person's do.

Coordinates are normalised to the person's standing height: x grows to the right,
y grows upwards, y = 0 is the ground.
"""

import math

LANDMARK_COUNT = 33

# MediaPipe Pose landmark indices (BlazePose topology).
NOSE = 0
LEFT_EYE_INNER, LEFT_EYE, LEFT_EYE_OUTER = 1, 2, 3
RIGHT_EYE_INNER, RIGHT_EYE, RIGHT_EYE_OUTER = 4, 5, 6
LEFT_EAR, RIGHT_EAR = 7, 8
MOUTH_LEFT, MOUTH_RIGHT = 9, 10
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_PINKY, RIGHT_PINKY = 17, 18
LEFT_INDEX, RIGHT_INDEX = 19, 20
LEFT_THUMB, RIGHT_THUMB = 21, 22
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28
LEFT_HEEL, RIGHT_HEEL = 29, 30
LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX = 31, 32

# mediapipe.solutions.pose.POSE_CONNECTIONS
POSE_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32),
    (27, 31), (28, 32),
)

# Landmarks of the head, hands and feet are drawn smaller than the body joints.
MINOR_LANDMARKS = frozenset(
    list(range(11)) + [17, 18, 19, 20, 21, 22] + [29, 30, 31, 32]
)

# Segment lengths, as fractions of standing height.
_TORSO = 0.288        # mid-hip -> mid-shoulder
_HEAD = 0.115         # mid-shoulder -> head centre
_UPPER_ARM = 0.186
_FOREARM = 0.146
_THIGH = 0.245
_SHIN = 0.246


def _down(angle: float):
    """Unit vector pointing 'down' rotated by `angle` degrees towards +x."""
    a = math.radians(angle)
    return (math.sin(a), -math.cos(a))


def _up(angle: float):
    a = math.radians(angle)
    return (math.sin(a), math.cos(a))


def _forward(angle: float):
    """Unit vector perpendicular to `_up(angle)`, pointing the way the person faces (+x)."""
    a = math.radians(angle)
    return (math.cos(a), -math.sin(a))


def _add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def _rotate(v, degrees: float):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def build_pose(kf: dict):
    """
    Forward kinematics for one keyframe. Angles are in degrees; limbs are measured from
    'straight down' (positive towards the direction the person faces), the torso and head
    from 'straight up'. Returns 33 (x, y) tuples, standing on y = 0.
    """
    hip_c = (0.0, 0.0)
    torso = kf["torso"]
    up, fwd = _up(torso), _forward(torso)
    sh_c = _add(hip_c, up, _TORSO)

    head_angle = torso + kf["head"]
    head_up, head_fwd = _up(head_angle), _forward(head_angle)
    head_c = _add(sh_c, head_up, _HEAD)

    pts = [(0.0, 0.0)] * LANDMARK_COUNT

    # Face offsets (up, forward) around the head centre, in body heights. Scaled so the
    # eyes, ears and mouth stay legible at the size the artwork is drawn.
    k = 1.35

    def face(u, f):
        return _add(_add(head_c, head_up, u * k), head_fwd, f * k)

    pts[NOSE] = face(-0.004, 0.052)
    pts[LEFT_EYE_INNER] = face(0.024, 0.040)
    pts[LEFT_EYE] = face(0.026, 0.048)
    pts[LEFT_EYE_OUTER] = face(0.024, 0.056)
    pts[RIGHT_EYE_INNER] = face(0.025, 0.030)
    pts[RIGHT_EYE] = face(0.027, 0.036)
    pts[RIGHT_EYE_OUTER] = face(0.025, 0.042)
    pts[LEFT_EAR] = face(0.002, -0.016)
    pts[RIGHT_EAR] = face(0.004, 0.004)
    pts[MOUTH_LEFT] = face(-0.030, 0.042)
    pts[MOUTH_RIGHT] = face(-0.030, 0.050)

    sides = (
        (+1, "arm_l", "leg_l", {"sh": 11, "el": 13, "wr": 15, "pi": 17, "ix": 19, "tb": 21, "hip": 23, "kn": 25, "an": 27, "he": 29, "ft": 31}),
        (-1, "arm_r", "leg_r", {"sh": 12, "el": 14, "wr": 16, "pi": 18, "ix": 20, "tb": 22, "hip": 24, "kn": 26, "an": 28, "he": 30, "ft": 32}),
    )
    for side, arm_key, leg_key, ix in sides:
        upper, fore = kf[arm_key]
        shoulder = _add(sh_c, fwd, 0.042 * side)
        elbow = _add(shoulder, _down(upper), _UPPER_ARM)
        wrist = _add(elbow, _down(fore), _FOREARM)
        pts[ix["sh"]], pts[ix["el"]], pts[ix["wr"]] = shoulder, elbow, wrist
        pts[ix["pi"]] = _add(wrist, _down(fore + 10), 0.052)
        pts[ix["ix"]] = _add(wrist, _down(fore - 8), 0.070)
        pts[ix["tb"]] = _add(wrist, _down(fore - 28), 0.045)

        thigh, shin, foot = kf[leg_key]
        hip = _add(hip_c, fwd, 0.024 * side)
        knee = _add(hip, _down(thigh), _THIGH)
        ankle = _add(knee, _down(shin), _SHIN)
        pts[ix["hip"]], pts[ix["kn"]], pts[ix["an"]] = hip, knee, ankle
        pts[ix["ft"]] = _add(ankle, _rotate((0.095, -0.032), foot))
        pts[ix["he"]] = _add(ankle, _rotate((-0.042, -0.034), foot))

    # Stand the figure on the ground: lowest landmark at y = 0, pelvis at x = 0.
    lowest = min(p[1] for p in pts)
    return [(p[0], p[1] - lowest) for p in pts]


# One keyframe per instant of the fall. Facing right; the person pitches forward.
#   arm_* = (upper arm, forearm), leg_* = (thigh, shin, foot)
FALL_KEYFRAMES = (
    {   # t-3: upright, relaxed
        "torso": 2, "head": 0,
        "arm_l": (6, 14), "arm_r": (-5, 8),
        "leg_l": (2, 1, 0), "leg_r": (-2, -1, 0),
    },
    {   # t-2: balance lost, knees give, arms swing forward
        "torso": 18, "head": -4,
        "arm_l": (38, 62), "arm_r": (22, 44),
        "leg_l": (20, -6, 0), "leg_r": (14, -12, 0),
    },
    {   # t-1: pitching forward, legs buckling, arms reach to break the fall
        "torso": 58, "head": -24,
        "arm_l": (84, 72), "arm_r": (98, 84),
        "leg_l": (36, -16, -8), "leg_r": (26, -26, -14),
    },
    {   # t: face down on the ground, arms forward, soles up
        "torso": 86, "head": -34,
        "arm_l": (104, 98), "arm_r": (86, 94),
        "leg_l": (-84, -98, 170), "leg_r": (-80, -102, 172),
    },
)

# Pelvis x position of each frame, in body heights (increases to the right).
FRAME_X = (0.0, 0.36, 0.84, 1.52)

FRAME_LABELS = ("t-3", "t-2", "t-1", "t")


def fall_sequence():
    """Landmarks of every frame, already offset along x. List of 4 lists of 33 (x, y)."""
    frames = []
    for keyframe, x0 in zip(FALL_KEYFRAMES, FRAME_X):
        frames.append([(x + x0, y) for x, y in build_pose(keyframe)])
    return frames


def mid_hip(landmarks):
    """Centre of the hips: the 'centroid' the detector tracks."""
    a, b = landmarks[LEFT_HIP], landmarks[RIGHT_HIP]
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
