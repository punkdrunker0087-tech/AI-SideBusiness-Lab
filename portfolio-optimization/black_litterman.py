"""2. ブラック・リッターマン ―― 市場均衡リターンと見通しを一貫した方法で組み合わせる。

Black & Litterman (1992) の枠組み:
  1. 市場（政策ポートフォリオ）の重みから、逆最適化で「市場が織り込んでいる
     均衡期待リターン」πを逆算する
  2. 見通し(views)を P・Q・Ω（確信度）で表現する
  3. πとviewsをベイズ的に統合し、事後期待リターン・共分散を得る

⚠️ 本実装では真の時価総額データがないため、市場均衡の重みは
「政策ポートフォリオ」（研究上よく使われる代表的な資産配分）で代用する。
実務では各資産クラスの時価総額（浮動株調整後）を用いるのが正式。
"""
import numpy as np


def implied_equilibrium_returns(market_weights: np.ndarray, cov: np.ndarray,
                                delta: float = 2.5) -> np.ndarray:
    """逆最適化: π = δ・Σ・w_mkt。deltaは市場のリスク回避度（一般に2.5前後が使われる）。"""
    return delta * cov @ market_weights


def combine_views(pi: np.ndarray, cov: np.ndarray, P: np.ndarray, Q: np.ndarray,
                  omega: np.ndarray = None, tau: float = 0.05) -> tuple:
    """均衡リターンπに見通し(P,Q,Ω)を統合し、事後期待リターン・共分散を返す。

    P: 見通し行列(k×n)。各行が「どの資産の組み合わせについての見通しか」を表す
    Q: 見通しのリターン値(k,)
    omega: 見通しの不確実性（対角行列、大きいほど確信度が低い）。省略時は
           tau・P・Σ・P^T の対角成分から自動生成（標準的な簡易設定）
    tau: 事前分布（均衡リターンπ）の不確実性スケール（一般に0.01〜0.1）
    """
    if omega is None:
        omega = np.diag(np.diag(tau * P @ cov @ P.T))

    tau_cov = tau * cov
    tau_cov_inv = np.linalg.inv(tau_cov)
    omega_inv = np.linalg.inv(omega)

    posterior_cov_factor = np.linalg.inv(tau_cov_inv + P.T @ omega_inv @ P)
    posterior_mu = posterior_cov_factor @ (tau_cov_inv @ pi + P.T @ omega_inv @ Q)
    posterior_cov = cov + posterior_cov_factor

    return posterior_mu, posterior_cov


def view_confidence_to_omega(P: np.ndarray, cov: np.ndarray, confidences: np.ndarray,
                             tau: float = 0.05) -> np.ndarray:
    """確信度(0-1、高いほど自信がある)からΩを構築する簡易ヘルパー。

    確信度1に近いほどΩの対角成分を小さく（見通しをより重視）、
    確信度0に近いほど大きく（見通しをほぼ無視）する。
    """
    base_var = np.diag(tau * P @ cov @ P.T)
    scale = 1.0 / np.clip(confidences, 1e-3, 1.0)
    return np.diag(base_var * scale)
