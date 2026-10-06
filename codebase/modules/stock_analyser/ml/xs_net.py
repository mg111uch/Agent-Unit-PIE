"""Shallow cross-sectional net, IC-loss.  Drop-in `scorer` for research.horizon_ic.horizon_scan.

Scope / expectations (be realistic):
  * Capacity is deliberately tiny (<=2 hidden layers, dropout, weight decay, seed ensemble, early stop):
    published large-sample work finds neural nets peak at ~3 shallow layers and that their edge over linear
    models comes from NONLINEAR INTERACTIONS among many predictors on decades x thousands of stocks.
    With ~5 years x 200 names an MLP will only help if the new feature blocks (flows/events) contain
    interactions; on OHLCV alone expect it to tie ridge.  Use it as an ensemble member AFTER new features exist.
  * Loss = -mean over dates of corr(pred, rank-gauss target): optimises what you are judged on (rank IC),
    is invariant to the date-level market component, and ignores target scale/outliers.
  * No sequence model: a 20-day window of the same 23 features adds parameters, not information.
"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn


def _corr_loss(pred, y):
    p = pred - pred.mean()
    t = y - y.mean()
    return -(p * t).sum() / (p.norm() * t.norm() + 1e-8)


def mlp_scorer(hidden=(32, 16), dropout=0.3, wd=1e-3, lr=2e-3, epochs=15, patience=3,
               n_seeds=3, dates_per_batch=16, val_frac=0.15, purge=20):
    torch.set_num_threads(1)

    def f(X_tr, y_tr, grp_tr, X_te):
        X_tr, X_te = np.nan_to_num(X_tr).astype(np.float32), np.nan_to_num(X_te).astype(np.float32)
        y_tr = np.nan_to_num(y_tr).astype(np.float32)
        ud = np.unique(grp_tr)
        cut = int(len(ud) * (1 - val_frac))
        fit_d, val_d = ud[: max(cut - purge, 1)], ud[cut:]
        idx = {d: np.where(grp_tr == d)[0] for d in ud}
        mk = lambda ds: [(torch.from_numpy(X_tr[idx[d]]), torch.from_numpy(y_tr[idx[d]])) for d in ds if len(idx[d]) > 20]
        fit_b, val_b = mk(fit_d), mk(val_d)
        Xte = torch.from_numpy(X_te)
        preds = []
        for seed in range(n_seeds):
            torch.manual_seed(seed)
            layers, d_in = [], X_tr.shape[1]
            for hdim in hidden:
                layers += [nn.Linear(d_in, hdim), nn.GELU(), nn.Dropout(dropout)]
                d_in = hdim
            net = nn.Sequential(*layers, nn.Linear(d_in, 1))
            opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=wd)
            best, best_state, bad = 1e9, None, 0
            rng = np.random.default_rng(seed)
            for _ in range(epochs):
                net.train()
                order = rng.permutation(len(fit_b))
                for k in range(0, len(order), dates_per_batch):
                    opt.zero_grad()
                    loss = sum(_corr_loss(net(fit_b[i][0]).squeeze(-1), fit_b[i][1]) for i in order[k : k + dates_per_batch]) / len(order[k : k + dates_per_batch])
                    loss.backward()
                    opt.step()
                net.eval()
                with torch.no_grad():
                    v = float(np.mean([_corr_loss(net(x).squeeze(-1), y).item() for x, y in val_b])) if val_b else 0.0
                if v < best - 1e-4:
                    best, bad = v, 0
                    best_state = {k_: t.clone() for k_, t in net.state_dict().items()}
                else:
                    bad += 1
                    if bad >= patience:
                        break
            if best_state:
                net.load_state_dict(best_state)
            net.eval()
            with torch.no_grad():
                preds.append(net(Xte).squeeze(-1).numpy())
        P = np.stack(preds)
        P = (P - P.mean(1, keepdims=True)) / (P.std(1, keepdims=True) + 1e-8)
        return P.mean(0)

    return f
