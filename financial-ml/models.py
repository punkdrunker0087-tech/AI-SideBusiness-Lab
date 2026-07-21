"""4. モデル比較 ―― 線形・決定木系・ニューラルネットワークを同一条件で比較する。"""
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor

FEATURE_COLS = ["momentum_120", "volatility_20", "reversal_5", "rsi_14", "liquidity_log"]
LABEL_COL = "label"


def build_models(seed: int = 0) -> dict:
    """3系統のモデルを同一のハイパーパラメータ規模感で用意する。"""
    return {
        "線形(Ridge)": Ridge(alpha=1.0),
        "決定木系(RandomForest)": RandomForestRegressor(
            n_estimators=200, max_depth=4, min_samples_leaf=50, random_state=seed
        ),
        "ニューラルネット(MLP)": MLPRegressor(
            hidden_layer_sizes=(16, 8), alpha=0.01, max_iter=500,
            early_stopping=True, random_state=seed,
        ),
    }


def prepare_xy(df, feature_cols=None, label_col=LABEL_COL):
    feature_cols = feature_cols or FEATURE_COLS
    d = df.dropna(subset=feature_cols + [label_col])
    return d[feature_cols], d[label_col], d
