"""VWAP (Volume-Weighted Average Price) ―― 出来高分布に比例して執行する。

出来高が厚い時間帯に多く・薄い時間帯に少なく発注することで、1回あたりの
参加率を抑え市場インパクトを軽減する。ただし**将来の出来高は予測値**であり、
実際の出来高分布と乖離すれば追随が崩れる（研究上の重要な論点）。
"""
import numpy as np


def schedule_from_profile(total_qty: float, volume_profile: np.ndarray) -> np.ndarray:
    """出来高プロファイル（正規化済み・合計1）に比例したスケジュール。"""
    profile = volume_profile / volume_profile.sum()
    return total_qty * profile


def predicted_profile(true_profile: np.ndarray, noise_std: float = 0.15,
                      seed: int = 1) -> np.ndarray:
    """『予測出来高』を、真の出来高プロファイルにノイズを加えて模擬する。

    実務ではVWAP執行は将来の出来高を過去実績等から予測するしかなく、
    実際の分布とは乖離する。このノイズがその乖離を表現する。
    """
    rng = np.random.default_rng(seed)
    noisy = true_profile * (1 + rng.normal(0, noise_std, len(true_profile)))
    noisy = np.clip(noisy, 1e-6, None)
    return noisy / noisy.sum()


def tracking_error(true_profile: np.ndarray, predicted: np.ndarray) -> float:
    """予測出来高分布と実際の分布の乖離（絶対誤差の合計の半分＝分布の重なりの逆）。"""
    p = true_profile / true_profile.sum()
    q = predicted / predicted.sum()
    return float(np.abs(p - q).sum() / 2)
