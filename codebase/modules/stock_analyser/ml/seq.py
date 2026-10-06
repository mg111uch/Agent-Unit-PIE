"""Sequence experiment (Phase 5): tiny GRU ranker over trailing feature windows.

Expectation (set explicitly): indistinguishable from ridge. Daily-return
predictability is tiny (R² ~0.1-0.5%) against ~10³-10⁴ effective independent
periods; a GRU will mostly memorise regime noise. This module exists to test
that claim, not to ship a model. History caveat: current constituents only —
delisted names are missing (survivorship bias favors the past).

Kept OUT of the genome mutation pool (ML_MODELS): per-candidate torch fits
are too expensive for sweeps. Manual probes only, via ranker model="gru".
"""
from __future__ import annotations
from typing import List

SEQ_LEN = 20
HIDDEN = 16
EPOCHS = 3
LR = 1e-3


def _frame(df, feats: List[str]):
    """Per-symbol (SEQ_LEN, F) windows + fwd_ret labels. Time-ordered."""
    import numpy as np
    X, y = [], []
    for _s, g in df.sort_values("ts").groupby("symbol", sort=False):
        arr = g[list(feats)].to_numpy(dtype=np.float32)
        lab = g["fwd_ret"].to_numpy(dtype=np.float32)
        for i in range(SEQ_LEN, len(g)):
            if np.isfinite(arr[i - SEQ_LEN:i]).all() and np.isfinite(lab[i]):
                X.append(arr[i - SEQ_LEN:i])
                y.append(lab[i])
    import numpy as _np
    return _np.array(X), _np.array(y)


def train(df, feats: List[str], top_n: int = 5, seed: int = 7, epochs: int = EPOCHS):
    import torch
    import torch.nn as nn
    torch.manual_seed(seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass
    X, y = _frame(df, feats)
    if len(X) < 200:
        raise ValueError(f"thin sequence panel ({len(X)} windows)")

    class GRU(nn.Module):
        def __init__(self, f: int):
            super().__init__()
            self.gru = nn.GRU(f, HIDDEN, batch_first=True)
            self.head = nn.Linear(HIDDEN, 1)

        def forward(self, x):
            _, h = self.gru(x)
            return self.head(h[-1]).squeeze(-1)

    net = GRU(X.shape[2])
    opt = torch.optim.Adam(net.parameters(), lr=LR)
    loss = nn.MSELoss()
    Xt, yt = torch.from_numpy(X), torch.from_numpy(y)
    net.train()
    for _ in range(max(1, epochs)):
        opt.zero_grad()
        l = loss(net(Xt), yt)
        l.backward()
        opt.step()

    class GRUModel:
        model_name_ = "gru"

        def __init__(self, net, feats, top_n):
            self._net = net
            self.feats_ = list(feats)
            self.top_n_ = top_n

        def score_frame(self, df):
            """Row-aligned scores: each row scored from its own symbol's
            trailing SEQ_LEN window (edge-padded at history start)."""
            import numpy as _np
            # positional index: callers often pass slices with parent labels
            df = df.reset_index(drop=True)
            self._net.eval()
            out = _np.zeros(len(df), dtype=_np.float32)
            with torch.no_grad():
                for _s, g in df.groupby("symbol", sort=False):
                    idx = g.index.to_numpy()
                    arr = g[self.feats_].to_numpy(dtype=_np.float32)
                    pad = _np.repeat(arr[:1], SEQ_LEN - 1, axis=0)
                    full = _np.concatenate([pad, arr], axis=0)
                    # sliding window lands last ((N,F) -> (N,F,L)); move to (N,L,F)
                    w = _np.lib.stride_tricks.sliding_window_view(
                        full, SEQ_LEN, axis=0).transpose(0, 2, 1)
                    t = torch.from_numpy(_np.ascontiguousarray(w))
                    for j in range(0, len(t), 2048):
                        chunk = t[j:j + 2048]
                        _, h = self._net.gru(chunk)
                        out[idx[j:j + 2048]] = self._net.head(
                            h[-1]).squeeze(-1).numpy()
            return out

        def predict(self, Xa):
            raise NotImplementedError("GRU scores per-symbol windows; use score_frame")

    return GRUModel(net, feats, top_n)
