from typing import Optional, Tuple

F_INT_C_DEFAULT = 0.4
F_SOL_C_DEFAULT = 0.4
F_H_C_DEFAULT = 0.4
F_C_C_DEFAULT = 0.4

def get_convective_fractions(
        f_int_c: Optional[float] = None,
        f_sol_c: Optional[float] = None,
        f_H_c: Optional[float] = None,
        f_C_c: Optional[float] = None
) -> Tuple[float, float, float, float]:

    if f_int_c is None:
        f_int_c = F_INT_C_DEFAULT

    if f_sol_c is None:
        f_sol_c = F_SOL_C_DEFAULT

    if f_H_c is None:
        f_H_c = F_H_C_DEFAULT

    if f_C_c is None:
        f_C_c = F_C_C_DEFAULT

    return f_int_c, f_sol_c, f_H_c, f_C_c