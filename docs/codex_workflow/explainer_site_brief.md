# Explainer site brief

## Style reference

Tham khao tinh than cua `https://bbycroft.net/llm`: mot interactive explainer theo chuong,
co navigation ro rang, visual trung tam, va commentary giai thich tung buoc.

Khong copy design, assets, code, hay visual cu the. Chi hoc cac nguyen tac:

- giai thich theo chuong,
- visual dong bo voi noi dung,
- nguoi doc co the tua qua tung buoc,
- cung mot doi tuong duoc highlight qua nhieu layer giai thich,
- math chi hien khi can, khong day vao mat nguoi moi doc.

## Site khong phai training app

Site chi doc data trong:

```text
site/public/artifacts/
```

Khong import Torch. Khong goi API. Khong train tren Render.

## Trang/chuong de xay

1. Overview: Active learning la gi?
2. Dataset: Pool, labeled set, test set, label budget.
3. Model: Deep Ensembles gom nhieu neural nets doc lap.
4. Uncertainty: Epistemic vs Aleatoric.
5. Acquisition: Random, GreedyVariance, KMeansVariance.
6. Loop: Xem iteration slider va cac diem duoc chon.
7. Results: RMSE theo so label.
8. Why diversity matters: Greedy tap trung, KMeans phu rong hon.
9. Notes: Vi sao chon Deep Ensembles thay vi MC Dropout.

## Visual components can co

- PCA scatter plot.
- Labeled/pool/selected point highlighting.
- Iteration slider.
- Strategy comparison toggle.
- RMSE line chart.
- Uncertainty decomposition chart.
- Ensemble disagreement mini-view.
- KMeans candidate and cluster center view.

## UX nguyen tac

- First screen phai cho thay active learning dang lam gi.
- Moi chuong co mot visual chinh.
- Text ngan, co muc dich, khong thanh paper.
- Math notes dat o expandable panels hoac trang rieng.
- Site phai doc duoc artifacts da build san.

